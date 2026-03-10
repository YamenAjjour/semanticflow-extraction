## Semanticflow-extraction

The project extract an educational knowledge graph from a given Coursera course by scarping materials from Coursera and then
extracting course elements and their relation from the content. Always use the coursel url as provided in the following example.
The course elements will be extracted using openai. To extract the educational knowledge graph from a given course do the following:

### Setup

1. copy ```.env-template``` to ```.env``` in the directory of the project  and add your openai_api_key token. 
2. run `pip install -r requirements` 

Notice that we use joblib to cache prompts. 

### Educational Knowledge Graph Extraction
 
```
python src/extractor.py --domain mathematics --data data/sample_courses/single_variable_calculus.json --url https://www.coursera.org/learn/single-variable-calculus
```

The extractor is based on two knowledge extraction prompts in [data/prompts.json](data/prompts.json) an `extract_elements` prompt that extracts the key concepts and `extract_relations`
prompt to detect the relations between the elements.

The output of the extractor is a json file that will be saved under the path provided with the data argument.
The json file contains the modules, lessons, and lesson items (e.g., videos or readings).
For each lesson, we extract key concepts, methods, explanations, examples, and assessments and their relationships and store them as the nodes of the graph.
The relationships between the nodes cover
- concept a is a *preqrequisite_for* concept b
- example/explanation *elaborated_by* concept ,
- method a *applies_to* concept b
- assessment a *assesses* *method or object b*
- concept a *relates to* concept b


- The json file has the following format:
  
```
{
  "course_id": "course_identifier",
  "domain_type": "mathematics|programming|humanities",
  "course_title": "...",
  "modules": [
    {
      "module_id": "m1",
      "title": "...",
      "lessons": [
        {
          "lesson_id": "l1",
          "title": "...",
          "scale": "lesson",
          "items": [ "Video a", "Video", "Transcript" ],
          "nodes": [ {"id": "n1", "text": "Concept 1", "difficulty": "medium"},
                     {"id": "n2", "text": "Concept 2", "difficulty": "medium", "rationale": "here is the rationale"}] 
         "edges": [
                    {
                      "source": "n1",
                      "target": "n2",
                      "type": "prerequisite",
                      "confidence": 0.95,
                      "rationale": "Concept 1 is nessecary to understand Concept 2"
                    }
            }
          ],
  "cross_scale_links": [
    {
      "lesson_node": "n1",
      "module_node": "mn2",
      "relationship": "part_of"
    }
  ]
}
```
### Rationale Extraction

In addition to knowledge extraction, the extractor uses the prompts `extract_element_rationales` and `extract_relations_rationales` in [data/prompts.json](data/prompts.json) for rationales extraction. 
The rationales are pedagogical reasons that indicate to why the course elements and relations are ordered in that specific way. The prompts take the graph of a specific lesson after topolgically sorting it.  
The element rationales are generated for key concepts, assessments, and methods. Also, we generate rationales for all relations in the graph. 

Example:
```
 {
  "id": "n22",
  "text": "Natural Logarithm",
  "type": "concept",
  "difficulty": "medium",
  "lesson_id": "m2-l1",
  "rationale": "Natural logarithms are introduced alongside exponential functions to explore inverse operations in calculus, providing a natural progression into solving integrals and derivatives involving exponential growth and decay."
}
```
### Token Usage 

In addition to the extracted courses, the script also tracks the costs of calling the openai api by storing the input and output token count,
the arguments of each prompt, and the costs in a csv file in `data/usage.csv`. 
To add a new model, you have to add its price per 1,000,000 token to [config.yaml](config.yaml)

### Evaluation
To evaluate the extraction method, the output of the extractor for a [sample course](data/sample_courses/single_variable_calculus_sample.json) of two lessons from two module (functions and bonus video on exponantials) is first
labeled with `gpt-4o` and then annotated by me. The ground truth can found in saved in [single_variable_calculus_elements_ground_truth.csv](data/evaluation/single_variable_calculus_elements_ground_truth.csv) 
and [single_variable_calculus_relations_ground_truth.csv](data/evaluation/single_variable_calculus_relations_ground_truth.csv).
The output of an extractor for the two lessons are evaluated against these files by calling 

**Relations**
```
python src/evaluation.py --evaluate_relations --predictions data/sample_courses/single_variable_calculus.json --ground_truth data/evaluation/single_variable_calculus_relations_ground_truth.csv 
```
This will output 

``` Relations Evaluation - Macro F1: 0.42666666666666664
  - F1 for 'assess': 0
  - F1 for 'elaborate': 0.13333333333333333
  - F1 for 'apply': 1.0
  - F1 for 'prerequisite': 0.2
  - F1 for 'relate': 0.8
```
**Elements**
```
python src/evaluation.py --evaluate_elements --predictions data/sample_courses/single_variable_calculus.json --ground_truth data/evaluation/single_variable_calculus_elements_ground_truth.csv
```

```
  - F1 for 'assessment': 0
  - F1 for 'example': 0.20000000000000004
  - F1 for 'explanation': 0
  - F1 for 'concept': 0.7307692307692308
  - F1 for 'method': 1.0

```