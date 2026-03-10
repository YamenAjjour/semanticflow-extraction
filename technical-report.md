## Technical Report

### Introduction
**Problem statement**

MOOCs provide an invaluable resource for intelligent tutoring systems since they are fully digital and easy to access.
Educational knowledge graphs provide a semantic layer that guides the learning process of students.
An educational knowledge graph should organize the main content elements of a course as concepts, methods, examples,
explanations, and quizzes. The relationships between the nodes should encode semantic relations such as a concept
*is a prerequisite of* another concept or a specific explanation *explains*. These semantic nodes and structure should be
supported by a natural language explanation that justifies a certain order of nodes or even the existence of a specific node.

Extracting knowledge graphs from MOOCs (Massive Open Online Course) is challenging since they are characterized by various learning methods,
different pedagogical philosophies, and diverse jargons and styles. Large Language Models excel at language understanding tasks. However,
the stochastic nature of LLMs poses the challenge of how to extract semantic flows in a consistent and coherent manner so that they make up a knowledge graph.
Consistency here means that the same set of concepts should be extracted regardless of the lesson or the scale. For example,
ideally, the rationale used to explain a specific relation should use the concept terms in the knowledge graph. Consistency should also be satisfied
on relations, i.e., similar relations should be extracted regardless of the course or domain.

Since different disciplines have different teaching philosophies, another challenge for using LLMs is to optimize the prompt to the target domain of each course.
To test the implementation, I extracted knowledge graphs from the following three free courses that cover three domains: mathematics, programming, and history.
The extracted knowledge graphs can be found in the [data/sample_courses](data/sample_courses)

1. [Crash Course on Python](https://www.coursera.org/learn/python-crash-course/)
2. [Ukraine History](https://www.coursera.org/learn/ukraine-history-culture-and-identities/)
3. [Single Variable Calculus](https://www.coursera.org/learn/single-variable-calculus)

### Approach overview

Given a Coursera course, we first scrape its content while keeping the following structure: `module` -> `lesson`. For each lesson,
we also extract the script of each video or the content of each reading and call them lesson items. We concatenate the content of all transcripts of videos and readings to form the lesson content.

We utilize a two-step approach to extract the educational knowledge graph:
In the first step, we employ a prompting approach to first extract the concepts, methods, and explanations/examples from each lesson.
As input to the prompt, the lesson item is fed to the model, and the output is requested to be a list of elements.
The second prompt-based approach takes as input the output concepts, methods, and explanations/examples and produces a list of relations between them (e.g., prerequisite relations).
For both prompts, we utilize constrained decoding where we predefine the output format as a JSON schema.


### Methodology
- **Multi-scale extraction strategy**
  We extract elements and relations between elements on the lesson level by taking as input all the lesson items (transcripts and readings) and the extracted elements.
  The output of the relation extraction can span multiple lesson items, which requires merging similar concepts and performing cross-lesson relation extraction.
- **Domain adaptation approach**
  To adapt the LLM to a given prompt, we utilize persona prompting where we prime the large language model to impersonate a teacher in the domain of the course. This prepares the model to process the input lesson items in the best way.

- **Rationale extraction method**

  We divide the rationale extraction process into two steps: element rationale extraction and relation rationale extraction.
  Element rationale extraction: which provides rationales for concepts, methods, and assessments in a lesson. These rationales elucidate the reasons for the existence of the high-level elements.
  The focus of this step is to explain why the level of abstraction or complexity is higher and why the element is positioned here.
  In contrast, relation rationale extraction focuses on the connections between all elements. The input to the prompts is the elements and the relations between the elements.
  We format the relations between elements as arrows. For example, Functions -> Inverse Function (Prequisite). To make the relations readable, we sort the relations by the topological order
  of the nodes in the graph. To sort the graph topologically, we employ the Khan algorithm, which uses BFS and a queue.

- **Token budget optimization**

  To stay within the budget, we followed two tactics. First, caching the prompts using joblib, which keeps the output of the prompts also persistent across script calls.
  Second, I worked on one *sample course* while developing the project, which consists of two lessons in one course.




### Results

We evaluate the element extraction methods by running the knowledge extraction method on a *sample course*. The sample course
contains two lessons from one module in the single variable calculus. Then, I revised the elements by dropping those that do not match the definition of the labels. Also, I added elements that were missing.
Based on this ground truth, we utilize F1, precision, and recall by considering a true positive for each element type in case
an element that is extracted by the extraction method exactly matches one of the elements in the ground truth.
false positives and false negatives are counted accordingly. A similar evaluation procedure is also employed for
relation extraction.

#### Performance breakdown by entity/relationship type

**Element Extraction Performance**

The table shows the F1-score of exact matches for each element type for a sample course that consists of two lessons.

| Method | Concept | Example | Explanation | Assessment | **Macro F1** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1.0 | 0.73 | 0.20 | 0.0 | 0.0 | **0.39** |

**Relation Extraction Performance**

The table shows the F1-score of detecting relations for each relation type for a sample course that consists of two lessons.

| Apply | Relate | Prerequisite | Elaborate | Assess | **Macro F1** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1.0 | 0.8 | 0.2 | 0.13 | 0.0 | **0.43** |


#### Rationale Generation Quality

To evaluate the quality of the generated rationales, we generate the rationale for a *sample course* and then rate them
on a Likert scale from 1 to 5 with regard to their quality, where 1 implies a low-quality rationale. We then report
the average rating for each element type and each relation type, as well as the micro average. As we notice, the quality
of the rationales for the assessment and concept nodes is lower than that of method elements. For relations, we
notice a similar problem where rationales for Assesses relations are the worst, followed by Elaborate_by relations.

**Element Rationale Quality**

The table shows the average quality rating for the three element types for a sample course that consists of two lessons. This covers 28 elements that are detected as important in each lesson graph.

| Assessment | Concept | Method | **Micro Average**           |
| :--- |:--------|:-- |:----------------------------|
| 3 | 3.13 |  4 |  **3.18**                   |

**Relation Rationale Quality**

The table shows the average quality rating for all relation types for a sample course that consists of two lessons. The relations in this amount to 22.

| Apply | Assess | Elaborate | Prerequisite | Relate | **Micro Average** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 3.5 | 3 | 3.4 | 3.67 | 4.33 | **3.53** |

#### Token usage breakdown and cost analysis

| Prompt | Input Tokens | Output Tokens | Price (USD) |
| :--- | :--- | :--- | :--- |
| Elements Extraction | 370,516 | 59,898 | 1.525 |
| Relation Extraction | 414,727 | 27,048 | 1.307 |
| Rationale Generation (Single Variable Calculus) | 52,824 | 18,305 | 0.315 |
| Rationale Generation (Crash Course Python) | 35,417 | 38,302 | 0.472 |
| Rationale Generation (Ukraine History) | 13,973 | 13,344 | 0.168 |
| **Total** | **887,457** | **156,897** | **3.787** |

### Error Analysis

Common errors in element extraction are extracting concepts at different levels of abstraction. For example, a concept such as the graph of e of x is too specific and cannot be compared by
the level of abstraction for elements such as function composition or polynomial approximation.
ppt4-o does recognize e^x as a function, but totally ignores cosine, sine, and similar concepts. Another problem that is challenging is extracting
examples and explanations whose level of detail or granularity is hard to define. Another problem that I faced is that LLMs use
labels such as Explanation: before outputting the actual output.

For relations detection, a common error is missing elaborate_by relations, despite the presence of a clear association between them.

Typical errors in rationale extraction were that rationales were not tailored to the course content or objective. Rationales
most of the time explain the reason behind a concept by indicating broad and open-ended reasons that apply to any concept, such as polynomial approximations are needed for mathematical applications. Sometimes, irrelevant learning objectives were
included that assume the students will learn for specific goals, which might not hold. An example is that exponential functions are needed
to understand compound rates.




### Discussion & Future Work

According to my annotation, LLMs performed the best at extracting examples and explanations, given their particular style.
Nevertheless, defining the exact granularity (sentence or paragraph) of the Explanation and examples is hard, which resulted in poor effectiveness as seen in the Element Extraction Performance table.
On the downside, concept extraction and rationale generation were the hardest tasks.
#### Limitations
The main limitations of the current approach lie in its inability to perform larger-scale merging of elements and relations.
Currently, we employ a bottom-up method by extracting elements and relations on the lesson level.
A clear improvement potential is implementing an ontology alignment method that merges the graphs of different lessons to form a final graph for each module, and then the whole course.
Also, cross-lesson and cross-module relation detection should be applied. Both these steps are essential to increase the consistency
of the approach. Evaluating consistency on multiple levels can be done, for example, by calculating how many elements that are recognized in one lesson (module) and
missed in another lesson (module), i.e., a cross-scale false negative count. Another analysis can also employ edit distance measures to analyze
elements that are recognized with different forms in different lessons and modules, though they have the same meaning.

To improve the extraction quality, one can use a few-shot prompting and perform prompting in a human-in-the-loop way.
Few-shot prompting should help provide the right level of granularity and abstraction that is needed for elements
such as concepts and explanations. With human-in-the-loop prompting, I assume that one should refine the output of the LLM for one lesson
and use it as established terminology while processing for subsequent lessons. This RAG-based setup should help enhance consistency by providing a reviewed element.
The low performance on Assesses relations and assessment concepts is mainly due to the lack of content extraction for the assessments in the modules, which made it hard to predict which course elements are assessed.