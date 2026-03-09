## Technical Report

### Introduction
**Problem statement**

MOOCs provide an invaluable resource for intelligent tutoring systems since they are fully digital and easy to access. 
Educational knowledge graphs provide a semantic layer that guide the learning process of students.
An educational knowledge graph should organize the main content elements of a course as concepts, methods, examples,
and explanations, and quizzes. The relationships between the nodes should encode semantic relations such as a concept 
*is a prerequisite of* another concept or a specific explanation *explains*. These semantic nodes and structure should be 
supported by natural language explanation that justify a certain order of nodes or even the existence of a specific node. 

Extracting knowledge graphs from MOOCs (Massive Open Online Course) is challenging since they are characterized by various learning methods, 
different pedagogical philosophies, and diverse jargons and styles. Large Language Models excel at language understanding tasks. However,
the stochastic nature of LLMs poses the challenges of how to extract semantic flows in a consistent and coherent so that they make up a knowledge graph.
Consistency here means that the same set of concepts should be extracted regardless of the lesson or the scale. For example, 
ideally the rationale used to explain a specific relation should use the concept terms in the knowledge graph. Consistency should be also satisfied 
on relations, i.e., similar relations should be extracted regardless of the course or domain.   

Since different disciplines have different teaching philosophies, another challenge for using LLMs is to optimize the prompt to the target domain of each course.

### Approach overview

Given a coursera course, we first scrape its content while keeping the following structure `module` -> `lesson`. For each lesson,
we also extract the script of each video or the content of each reading and call them *lesson item*. 
We utilize persona prompting and a two-step approach to extract the educational knowledge graph. 
The two-step prompting approach first extract the concepts, methods, and explanations/examples form each lesson item. 
As input to the prompt, the lesson item is fed to the model and the output is requested to be a list of elements.
The second prompt takes as input the output concepts, methods, and explanations/examples and produce a list of relations between them (e.g., prerequisite relations).
For both prompts, we utilize constrained decoding where predefine the output format as a json schmea. 

### Methodology
- Multi-scale extraction strategy
  In contrast to element extraction, we extract relations between elements on the lesson level by taking as input all the lesson items and the extracted elements.
  The output of the relation extraction can span multiple lesson items. 
  This is simply not True ! no we extract relations on the lesson item level so far! 
- Domain adaptation approach 
 To adapt the LLM to a given prompt, we utilize persona prompting where  prime the large languag model to impersonate a teacher in the domain of the course. This prepares the model to process the input lesson items in the best way.

- Rationale extraction method
- Token budget optimization: How you stayed within 100K tokens
- Design decisions and trade-offs

### Results
- Evaluation metrics (precision, recall, F1) per domain and scale
- Performance breakdown by entity/relationship type
- Cross-domain flow structure comparison (with visualizations if possible)
- Multi-scale consistency analysis
- Token usage breakdown and cost analysis

### Error Analysis
- Common failure modes
- Domain-specific challenges
- Token budget impact on quality (if any)
- Multi-scale consistency issues

### Discussion & Future Work
- What worked well vs. what didn't
- Limitations of current approach
- Suggestions for improving extraction quality
- How would you scale this to full SemanticFlow system?
- Ideas for cross-domain flow transfer
- Token-quality trade-offs: Discuss how budget constraints influenced design choices
- Which domain structures were most challenging and why?
