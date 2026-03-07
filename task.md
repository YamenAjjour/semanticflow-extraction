## Overview

This assessment evaluates a candidate's ability to:
1. **Read and synthesize research papers** on pedagogical reasoning, knowledge structure extraction, and cross-domain transfer
2. **Write functional code** for semantic flow extraction from educational content
3. **Use LLMs effectively** within strict resource constraints
4. **Analyze patterns across multiple scales** (lesson → module → curriculum)
5. **Adapt extraction strategies** to fundamentally different content structures

**Duration:** 5-7 days
**Format:** Remote work with deliverables submission

---

## Project Context

You'll be working on a proof-of-concept related to the **SemanticFlowAI** project - a 3-year research initiative developing rationale-driven content generation for education. SemanticFlow goes beyond vanilla LLMs/RAG by providing:
- Machine-actionable semantic flows with structural reasoning
- Reusable pedagogical patterns across domains
- Rationale-aware generation (every structural decision is explained)
- Adaptive content delivery based on audience profiles
- Cross-domain transfer of reasoning structures

Your task is to build a prototype that extracts semantic flows from educational materials across different domains, revealing the underlying reasoning structures.

---

## Task Components

### Part 1: Literature Review (1-2 days)

**Objective:** Survey state-of-the-art approaches for semantic structure extraction and pedagogical reasoning representation

**Required Reading:**
Read and analyze **2-3 papers** from the following suggested topics:

**Suggested Paper Categories:**

1. **Pedagogical Reasoning & Concept Structure:**
    - Knowledge graph construction for educational content (search AIED/EDM 2023-2025)
    - Learning path recommendation in MOOCs
    - Concept map extraction from educational text

2. **Cross-Domain Transfer & Ontology Alignment:**
    - Cross-domain knowledge graph embedding (search KDD/WWW/AAAI)
    - Ontology alignment for educational resources
    - Transfer learning in educational content generation

3. **LLM-based Content Structure Analysis:**
    - Large language models for curriculum planning (2024-2025)
    - Prompt engineering for educational content analysis
    - Evaluating LLMs on pedagogical reasoning tasks

**Recommended Venues:**
- AIED (International Conference on Artificial Intelligence in Education)
- EDM (Educational Data Mining)
- CHI (Learning at Scale track)
- L@S (Learning at Scale)
- WWW/KDD/AAAI (for knowledge graph/transfer learning)
- ACL/EMNLP (for NLP-based extraction)

**Alternative:** If you have strong background knowledge, you may substitute with recent papers (2023-2025) from these venues on similar topics.

**Deliverable 1: Literature Summary (2-3 pages)**

Write a concise summary covering:
- **Key techniques** for extracting semantic structure from educational content (graph-based, LLM-based, hybrid)
- **Pedagogical reasoning representation** methods (how to capture the "why" behind content structure)
- **Evaluation metrics** commonly used (precision, recall, F1, coherence metrics)
- **Challenges** specific to cross-domain extraction (different ontologies, varying structure types)
- **Applicability to SemanticFlow:** Which approaches would be most suitable and why?

**Format:** PDF or Markdown, 2-3 pages maximum

---

### Part 2: Prototype Implementation (3-4 days)

**Objective:** Build a working prototype that extracts semantic flows from educational materials across three different domains

#### 2.1 Domain Selection

Select **one course** from each of the following domain types:

1. **Mathematics** (hierarchical flow structure)
    - Example: Linear Algebra, Calculus, Statistics
    - Flow characteristic: Strong prerequisite chains, hierarchical concept dependencies

2. **Programming** (linear/scaffolded flow structure)
    - Example: Python for Data Science, Web Development, Algorithms
    - Flow characteristic: Step-by-step scaffolding, cumulative skill building

3. **Humanities/Social Sciences** (narrative flow structure)
    - Example: Philosophy, Psychology, History, Literature
    - Flow characteristic: Thematic progression, conceptual weaving, less strict prerequisites

**Source Materials:**
- Coursera (https://www.coursera.org/)
- edX (https://www.edx.org/school/edx)

Select 3-5 modules from each course to extract flows from.

#### 2.2 Semantic Flow Components to Extract

Your system should identify the following components:

**Nodes (Content Elements):**
1. **Concepts** - Core ideas, theories, principles (e.g., "vector space", "gradient descent", "recursion")
2. **Methods** - Techniques, algorithms, approaches (e.g., "Gaussian elimination", "divide-and-conquer")
3. **Examples** - Illustrative instances, case studies
4. **Explanations** - Descriptions, definitions, elaborations
5. **Assessments** - Quizzes, exercises, projects

**Edges (Structural Relationships):**
1. **PREREQUISITE_FOR** - Concept A must be understood before Concept B
2. **ELABORATED_BY** - Concept A is explained in detail by Example/Explanation B
3. **APPLIES_TO** - Method A applies to Concept B
4. **ASSESSES** - Assessment evaluates understanding of Concept/Method
5. **RELATES_TO** - Conceptual connection between topics (thematic, historical, etc.)

**Rationale Annotations:**
- **Structure_rationale** - Why is content ordered this way?
- **Complexity_rationale** - Why is this level of detail appropriate here?
- **Assessment_rationale** - Why assess at this point?
- **Constraint_rationale** - What limitations or assumptions affect this flow?

#### 2.3 Implementation Requirements

**Tech Stack:**
- **Language:** Python 3.9+
- **LLM API:** OpenAI (GPT-4/GPT-4o) or Anthropic (Claude 3.5 Sonnet)
- **Output Format:** JSON (graph structure)
- **Budget Constraint:** 100,000 tokens maximum across entire task (development + extraction + evaluation)

**Required Features:**

1. **Multi-Scale Extraction Module**
    - Extract flows at **three scales**:
        - **Lesson-level:** Concept dependencies within a single lecture/module
        - **Module-level:** How lessons/modules connect to form a larger topic
        - **Curriculum-level:** How modules/topics connect to form the course structure
    - Maintain consistency across scales (concepts at one level should appear at higher levels)

2. **Domain-Adaptive Extraction**
    - Recognize and handle different flow structures:
        - Mathematics: Hierarchical dependencies, strict prerequisites
        - Programming: Linear scaffolding, cumulative skills
        - Humanities: Thematic progression, narrative flow
    - Adapt extraction strategies to domain characteristics

3. **Rationale Extraction**
    - Extract or generate rationale annotations for key structural decisions
    - Rationales should be specific and traceable (not generic)

4. **JSON Graph Output**
   Structure your output as:
   ```json
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
             "nodes": [
               {
                 "id": "n1",
                 "text": "vector space",
                 "type": "Concept",
                 "difficulty": "medium",
                 "rationale": "Core concept needed for linear transformations"
               }
             ],
             "edges": [
               {
                 "source": "n1",
                 "target": "n2",
                 "type": "PREREQUISITE_FOR",
                 "rationale": "Understanding vector spaces is required before studying linear transformations",
                 "confidence": 0.92
               }
             ]
           }
         ]
       }
     ],
     "cross_scale_links": [
       {
         "lesson_node": "n1",
         "module_node": "mn2",
         "relationship": "part_of"
       }
     ],
     "extraction_metadata": {
       "model_used": "gpt-4",
       "timestamp": "2026-03-02T10:30:00Z",
       "tokens_used": 12456,
       "estimated_cost": 0.37
     }
   }
   ```

5. **Token Budget Tracking**
    - Track token usage for every LLM call
    - Implement optimization strategies to stay within 100,000 token limit:
        - Caching repeated extractions
        - Batch processing where possible
        - Incremental extraction (build up from lesson to curriculum level)
    - Include cost breakdown in metadata

**Code Organization:**
```
semanticflow-extraction/
├── README.md              # Setup instructions, usage examples, budget breakdown
├── requirements.txt       # Python dependencies
├── src/
│   ├── extractor.py      # Main extraction logic
│   ├── domain_adapter.py # Domain-specific extraction strategies
│   ├── multi_scale.py    # Multi-scale flow construction
│   ├── rationale.py      # Rationale extraction/generation
│   ├── llm_client.py     # LLM API wrapper with token tracking
│   └── utils.py          # Helper functions
├── data/
│   └── sample_courses/   # Course materials (transcripts, outlines)
├── output/               # Generated JSON flows
└── tests/                # Unit tests (optional)
```

**Deliverable 2: GitHub Repository**
- Well-documented code with clear README
- Working prototype that can be run with: `python src/extractor.py --domain mathematics --data data/sample_courses/linear_algebra/`
- Requirements file for easy setup
- Sample outputs in `output/` directory for all three domains
- **Budget tracking:** Include `BUDGET.md` with token usage breakdown, optimization strategies used

---

### Part 3: Evaluation & Report (1 day)

**Objective:** Assess your prototype's performance and analyze cross-domain patterns

#### 3.1 Evaluation Methodology

**Hybrid Annotation:**
1. **LLM Suggestion:** Run your prototype on course materials to extract flows
2. **Human Review:** Review and correct LLM-suggested entities and relationships
3. **Calculate Metrics:** Compare corrected vs. original extractions

**Metrics Calculation:**
For each domain and scale level:
- **Precision** = Correct Entities/Relationships / All Extracted
- **Recall** = Correct Entities/Relationships / All in Ground Truth (reviewed)
- **F1 Score** = 2 × (Precision × Recall) / (Precision + Recall)

Calculate separately for:
- Entity extraction (per entity type)
- Relationship extraction (per relationship type)
- Rationale extraction (quality scoring)

**Multi-Scale Consistency Analysis:**
- Check if concepts appearing at lesson level are properly represented at module/curriculum levels
- Identify inconsistencies across scales
- Analyze how well the extraction maintains coherence from micro to macro levels

**Cross-Domain Flow Structure Analysis:**
- Compare flow structures across domains:
    - Mathematics: Hierarchical vs. Programming: Linear vs. Humanities: Narrative
    - Relationship type distributions
    - Average out-degree/in-degree of nodes
    - Flow "height" (max path length) vs. "width" (parallel tracks)
- Analyze how domain characteristics affect extraction challenges

**Error Analysis:**
- Identify common error patterns (missed relationships, wrong edge types)
- Document domain-specific failures
- Analyze where token budget constraints may have affected quality

#### 3.2 Report Structure

**Deliverable 3: Technical Report (2-4 pages PDF/Markdown)**

Include the following sections:

1. **Introduction** (0.5 pages)
    - Problem statement
    - Approach overview

2. **Methodology** (1 page)
    - Multi-scale extraction strategy
    - Domain adaptation approach
    - Rationale extraction method
    - **Token budget optimization:** How you stayed within 100K tokens
    - Design decisions and trade-offs

3. **Results** (1 page)
    - Evaluation metrics (precision, recall, F1) per domain and scale
    - Performance breakdown by entity/relationship type
    - Cross-domain flow structure comparison (with visualizations if possible)
    - Multi-scale consistency analysis
    - Token usage breakdown and cost analysis

4. **Error Analysis** (0.5 pages)
    - Common failure modes
    - Domain-specific challenges
    - Token budget impact on quality (if any)
    - Multi-scale consistency issues

5. **Discussion & Future Work** (0.5-1 page)
    - What worked well vs. what didn't
    - Limitations of current approach
    - Suggestions for improving extraction quality
    - How would you scale this to full SemanticFlow system?
    - Ideas for cross-domain flow transfer
    - **Token-quality trade-offs:** Discuss how budget constraints influenced design choices
    - Which domain structures were most challenging and why?

**Format:** PDF or Markdown, 2-4 pages maximum

---

## Evaluation Criteria

Your submission will be assessed on:

### 1. Literature Review (20%)
- [ ] Demonstrates understanding of state-of-the-art approaches
- [ ] Synthesizes techniques from multiple papers
- [ ] Critically evaluates applicability to SemanticFlow
- [ ] Clear and concise writing
- [ ] Proper citations and references

### 2. Code Quality (30%)
- [ ] **Functionality:** Code runs without errors and produces correct output
- [ ] **LLM Integration:** Effective use of LLM APIs with good prompt engineering
- [ ] **Multi-Scale Logic:** Proper handling of lesson/module/curriculum levels with consistency
- [ ] **Domain Adaptation:** Different strategies for different flow structures
- [ ] **Code Structure:** Clean, modular, well-organized code
- [ ] **Documentation:** Clear README, docstrings, comments where needed
- [ ] **Reproducibility:** Easy to set up and run (requirements.txt, clear instructions)
- [ ] **Best Practices:** Error handling, type hints (optional), reasonable efficiency
- [ ] **Resource Efficiency:** Stays within 100K token budget constraint with clear tracking

### 3. Technical Report (20%)
- [ ] Clear methodology description
- [ ] Rigorous evaluation with appropriate metrics
- [ ] Cross-domain flow structure analysis
- [ ] Multi-scale consistency assessment
- [ ] Insightful error analysis
- [ ] Honest discussion of limitations
- [ ] Thoughtful suggestions for future work
- [ ] Well-structured and readable
- [ ] Addresses token-quality trade-offs

### 4. Research Maturity (20%)
- [ ] Shows independence and problem-solving ability
- [ ] Demonstrates understanding of research process
- [ ] Makes reasonable design choices with justification
- [ ] Identifies important challenges and trade-offs
- [ ] Shows creativity in approach or analysis
- [ ] **Multi-Scale Thinking:** Maintains coherence across abstraction levels
- [ ] **Constraint Awareness:** Adapts to 100K token limit effectively
- [ ] **Structural Awareness:** Recognizes different domain flow structures

### 5. Creative Problem-Solving (10%)
- [ ] Notices extra challenges (different flow structures across domains)
- [ ] Proposes innovative solutions to constraints
- [ ] Demonstrates resourcefulness under token budget limitations
- [ ] Shows awareness of research context and implications
- [ ] Makes connections beyond explicit requirements
- [ ] Effective multi-scale reasoning

### Bonus Points:
- [ ] Implements advanced multi-scale consistency checking
- [ ] Visualizes flow structures across domains
- [ ] Automated rationale quality assessment
- [ ] Creative token optimization strategies (e.g., hierarchical extraction, caching, incremental building)
- [ ] Analyzes flow structure metrics (path lengths, branching factors, centrality)
- [ ] Proposes cross-domain flow mapping techniques
- [ ] Identifies pedagogical patterns specific to each domain type

---

## Submission Instructions

**Deadline:** 7 days from task assignment

**What to Submit:**

1. **GitHub Repository Link** (or ZIP file)
    - Contains all code, data, and outputs
    - Must include README with setup/usage instructions
    - Include `BUDGET.md` with token usage breakdown and optimization strategies

2. **Literature Summary PDF/Markdown** (2-3 pages)

3. **Technical Report PDF/Markdown** (2-4 pages)

**Submission Format:**
- Email to: andrey.ustyuzhanin@constructor.org
- Subject: “Postdoc Assessment - [Your Name] - Semantic Flow Extraction"
- Include:
    - GitHub repo link (preferred) or ZIP attachment
    - Attached PDFs for literature summary and report

---

## Resources & Support

### Sample Data Sources
- **Coursera:** https://www.coursera.org/ (free courses available for audit)
- **edX:** https://www.edx.org/school/edx (free courses available for audit)
- **Tips:** Focus on courses with transcripts, syllabi, and clear module structures

### Recommended Libraries
- `openai` or `anthropic` - LLM API clients
- `requests` - HTTP requests
- `json` - JSON handling
- `networkx` - Graph manipulation (for multi-scale operations)
- Optional: `spacy`, `nltk` (for NLP preprocessing)

### Questions?
If you have clarifying questions about the task, please email within the first 24 hours.

---

## What We're Looking For

This task tests critical skills for the SemanticFlow project:

1. **Reading Papers:** Can you quickly digest research literature and extract key ideas?
2. **Writing Code:** Can you build a working prototype with clean, documented code?
3. **Using LLMs:** Can you effectively leverage LLMs through prompt engineering while respecting constraints?
4. **Multi-Scale Thinking:** Can you maintain coherence across different abstraction levels?
5. **Structural Awareness:** Can you recognize and adapt to fundamentally different content structures?
6. **Creative Problem-Solving:** Can you notice extra challenges and adapt your approach accordingly?

We're looking for candidates who:
- Take initiative and solve problems independently
- Write clean, understandable code with good documentation
- Think critically about research problems and evaluation
- Communicate technical ideas clearly in writing
- Are honest about limitations and thoughtful about improvements
- **Notice structural differences across domains**
- **Demonstrate resourcefulness when working under token constraints**
- **Think across multiple scales simultaneously**

**We value quality over quantity.** A well-documented, working prototype with thoughtful multi-scale analysis is better than an overengineered system that doesn't work reliably.