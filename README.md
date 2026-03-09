## Semanticflow-extraction

The project extract an educational knowledge graph from a given Coursera course by scarping materials from Coursera and then
extracting course elements and their relation from the content. Always use the coursel url as provided in the following example.
The course elements will be extracted using openai. To extract the educational knowledge graph from a given course do the following:
1. copy ```.env-template``` to ```.env``` in the directory of the project  and add your openai_api_key token. 

2. Call 
```
python src/extractor.py --domain mathematics --data data/sample_courses/single_variable_calculus.json --url https://www.coursera.org/learn/single-variable-calculus
```

The extractor is based on two prompts in [data/prompts.json](data/prompts.json) an `extract_concepts` prompt that extracts the key concepts and `extract_preqrequisites`
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

The json file has the following format:
the `lesson_item_id` of a concept indicates the original learning item that the concept is first extracted from.  
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
          "nodes": [ {"id": "n1", "text": "Node 1", "difficulty": "medium", "lesson_item_id": "m1-l1-video-Video a-1"}] 
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
In addition to the extracted courses, the script also tracks the costs of calling the openai api by storing the input and output token count,
the arguments of each prompt, and the costs in a csv file in `data/usage.csv`. 

### Evaluation
To evaluate the extraction method, the output of the extractor for a sample of 3 lessons from two module (functions and taylor serises) is collaboratively
labeled with `gpt-4o` and saved in `data/evaluation/calculus_sample_concepts.csv` `data/evaluation/calculus_sample_prerequisite.csv` 
The output of an extractor for the 3 lessons are evaluated against these files by calling 


```
python src/evaluation.py --data data/sample_courses/calculus_sample.json 
```