# Kitchenham Guidelines Reference

## Overview

Barbara Kitchenham's guidelines for performing systematic literature reviews in software engineering
(originally published 2004, updated 2007) are the foundational methodology for SLRs in computer
science and software engineering. While PRISMA dominates health sciences, Kitchenham is the standard
reference in SE/CS venues like IEEE TSE, ACM TOSEM, and EMSE.

---

## The Three-Phase Process

### Phase 1: Planning the Review

**1.1 Identify the Need for a Review**
- Justify why a systematic review is needed (as opposed to a traditional literature survey)
- Check if recent SLRs on the topic already exist

**1.2 Develop the Review Protocol**
The protocol must specify:

- **Research questions**: The most important part. Kitchenham recommends structuring them with PICOC:
  - **P**opulation: The group being studied (e.g., "software projects", "mobile applications")
  - **I**ntervention: The methodology/tool/technique being investigated
  - **C**omparison: What the intervention is compared against (if applicable)
  - **O**utcome: The results of interest (e.g., "defect rates", "developer productivity")
  - **C**ontext: The setting (e.g., "industry", "academic", "open source")

- **Search strategy**: 
  - Which databases to search
  - Search terms derived from research questions and PICOC
  - How to construct search strings
  - Time period to cover

- **Study selection criteria and procedures**:
  - Inclusion criteria
  - Exclusion criteria
  - Selection procedure (who screens, how disagreements are resolved)

- **Quality assessment checklists**: Criteria for evaluating study quality

- **Data extraction strategy**: What data to extract and how

- **Data synthesis strategy**: How to combine and present results

**1.3 Evaluate the Protocol**
- Have the protocol reviewed by an independent party if possible
- Conduct a pilot search to test the search strings

### Phase 2: Conducting the Review

**2.1 Identification of Research**
- Execute the search strategy across all specified databases
- Document the exact date, database, search string, and result count for each search
- Check reference lists of included studies (snowballing)
- Contact known researchers in the field if appropriate

**2.2 Selection of Primary Studies**
- Apply inclusion/exclusion criteria in stages:
  1. Title and abstract screening
  2. Full-text screening
- Use a study selection form to document decisions
- Resolve disagreements through discussion or a third reviewer

**2.3 Study Quality Assessment**
Kitchenham recommends assessing quality on multiple dimensions:
- Reporting quality (is the study clearly described?)
- Rigor (was the methodology appropriate and well-executed?)
- Credibility (are the findings trustworthy?)
- Relevance (does the study address the review's research questions?)

Use a scoring scheme (e.g., Yes=1, Partial=0.5, No=0) across specific questions.

**2.4 Data Extraction**
- Use a standardized data extraction form
- Pilot the form on 2-3 studies before full extraction
- Ideally, have two reviewers extract independently
- Record: bibliographic info, study context, methods, findings, quality scores

**2.5 Data Synthesis**
- **Quantitative synthesis**: If studies report comparable metrics, use meta-analysis or
  aggregation (e.g., vote counting, weighted averages)
- **Qualitative synthesis**: Narrative synthesis organized by research question, with
  supporting/contradicting evidence from each study

### Phase 3: Reporting the Review

**3.1 Report Structure (Kitchenham format)**
1. Title
2. Abstract
3. Introduction
4. Background (key terms, related surveys, motivation)
5. Review Method
   - Research questions
   - Search strategy (databases, search strings, dates)
   - Study selection (criteria, process, results at each stage)
   - Quality assessment (criteria, scoring)
   - Data extraction (form design, process)
   - Data synthesis (approach used)
6. Results
   - Search results and study selection (with flow chart)
   - Overview of included studies (table of study characteristics)
   - Quality assessment results
   - Findings organized by research question
7. Discussion
   - Summary of findings per RQ
   - Comparison with existing reviews/knowledge
   - Implications for practice
   - Implications for research
8. Threats to Validity
   - Internal validity (bias in study selection, data extraction)
   - External validity (generalizability)
   - Construct validity (are we measuring what we think?)
   - Conclusion validity (are conclusions supported by data?)
9. Conclusions
10. Acknowledgments
11. References
12. Appendices (search strings, list of included/excluded studies, data extraction form)

---

## Key Differences from PRISMA

| Aspect | Kitchenham | PRISMA 2020 |
|--------|-----------|-------------|
| Origin | Software engineering | Health sciences |
| Focus | Evaluation of SE technologies/methods | Clinical/health interventions |
| RQ framework | PICOC | PICO |
| Validity section | Required (4 types) | Not required (part of discussion) |
| Meta-analysis | Optional, often not applicable | Central when data allows |
| Protocol registration | Informal (in paper) | Formal (PROSPERO) |
| Quality assessment | Custom checklists encouraged | Standardized tools (RoB 2, ROBINS-I) |
| Reporting checklist | No formal checklist | 27-item checklist |

---

## When to Recommend Kitchenham

- The review is in **software engineering** or **computer science**
- The target venue is an SE/CS journal or conference
- The studies being reviewed are primarily **empirical SE studies** (experiments, case studies, surveys)
- The user is familiar with SE research conventions (e.g., "threats to validity" sections)
- The review involves evaluating tools, techniques, or processes rather than clinical interventions
