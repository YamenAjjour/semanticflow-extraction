## Technical Report

### Introduction
**Problem statement**

MOOCs provide an invaluable resource for intelligent tutoring systems since they are fully digital and easy to access. 
Educational knowledge graphs provide a semantic layer that guide the learning process of students.
An educational knowledge graph should organize the main content elements of a course as concepts, methods, examples,
and explanations, and quizzes. The relationships between the nodes should encode semantic relations such as a concept 
*is a prerequisite of* another concept or a specific explanation *explains*. These semantic nodes and structure should be 
supported by natural language explanation that justify a certain order of nodes or even the existence of a specific node. 

Extracting knowledge graphs from MOOCs (Massive Open Online Course), is challenging since they are characterized by a various learning methods, 
different pedagogical philosophies, and diverse jargons and styles. Large Language Models excel at language understanding tasks. However,
the stochastic nature of LLMs poses the challenges of to extracting semantic flows in a consistent and coherent so that they make up a knowledge graph.
Consistency here means that the same set of concepts should be extracted regardless of the lesson or the level of details. For example, 
ideally the rationale used to explain a specific relation should use the concept temrs in the knowledge graph. Consistency should be also satisfied 
on relations, i.e., similar relations should be extracted regardless of the course or domain.   

Since different disciplines have different teaching philosophies, another challenge for using LLMs is to optimize the prompt to the target domain of each course.
To adapt 
- Approach overview

### Methodology
- Multi-scale extraction strategy
- Domain adaptation approach
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
