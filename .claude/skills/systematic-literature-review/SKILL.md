---
name: systematic-literature-review
description: >
  Use this skill for any formal, protocol-driven literature review task: writing SLR protocols
  (PROSPERO, OSF); building database search strings (Scopus, Web of Science, PubMed, IEEE Xplore,
  ACM); designing inclusion/exclusion criteria; creating PRISMA 2020 flow diagrams; building data
  extraction forms; quality appraisal (JBI, CASP, Newcastle-Ottawa); inter-rater reliability
  (kappa, Rayyan, Covidence); or synthesizing findings. Trigger on: SLR, PRISMA, Kitchenham,
  systematic review, PICO, PICOC, SPIDER, screening records, data extraction, or Rayyan/Covidence
  — even for a single step like "help me write a search string." The signal is systematic,
  reproducible methodology. Complements research-gap-analyst (exploratory) — use this skill for
  the formal review process.
---

# Systematic Literature Review (SLR) Specialist

A comprehensive skill for conducting rigorous, reproducible Systematic Literature Reviews following
PRISMA 2020 and/or Kitchenham guidelines. This skill guides the entire SLR lifecycle — from
protocol development through search strategy, screening, data extraction, quality assessment,
synthesis, and reporting.

This skill is designed to be **domain-agnostic**: it works for engineering, health sciences,
social sciences, computer science, or any field where systematic evidence synthesis is needed.

---

## How This Skill Relates to research-gap-analyst

These two skills serve different purposes and work best together:

| Aspect | research-gap-analyst | This skill (SLR) |
|--------|---------------------|-------------------|
| **Purpose** | Exploratory gap identification | Formal, reproducible evidence synthesis |
| **Methodology** | Flexible, web-search driven | Protocol-driven (PRISMA / Kitchenham) |
| **Output** | Gap report + concept map | Full SLR deliverables (protocol, PRISMA flow, data extraction, synthesis) |
| **When to use** | "What gaps exist in X?" | "I need to conduct a systematic review on X" |

You can use research-gap-analyst first to scope a topic, then switch to this skill to execute
the formal SLR.

---

## Input Types Supported

Handle any combination of:
- **Research question or topic** — start from scratch with protocol development
- **Existing protocol** — user already has a protocol; help execute remaining steps
- **Set of uploaded PDFs** — help with screening, extraction, or synthesis
- **Search results (CSV/Excel)** — help with deduplication and screening
- **Partial SLR in progress** — pick up wherever the user left off

Always ask the user where they are in the SLR process before jumping in. A user who says
"help me with my SLR" might need anything from protocol design to final reporting.

---

## Workflow Overview

The SLR follows these phases. Not every review needs every phase — adapt based on the user's
needs and where they are in the process.

### Phase 1 — Protocol Development

The protocol is the blueprint. It defines every decision before the review begins, which is
what makes an SLR reproducible rather than ad hoc.

**1.1 Define the Research Question(s)**

Help the user formulate precise, answerable research questions. Offer structured frameworks
but don't force them — some questions don't fit neatly into a framework:

- **PICO** (Population, Intervention, Comparison, Outcome) — best for clinical/quantitative studies
- **PICo** (Population, Interest, Context) — best for qualitative studies
- **SPIDER** (Sample, Phenomenon of Interest, Design, Evaluation, Research type) — mixed methods

If the user's question doesn't fit these, help them articulate it clearly without a framework.
The goal is precision, not framework compliance.

**1.2 Define Inclusion/Exclusion Criteria**

Guide the user to specify:
- **Time period** (e.g., 2015–2025)
- **Language** (e.g., English only)
- **Publication types** (journal articles, conference papers, theses, grey literature)
- **Study designs** (if relevant — RCTs, case studies, surveys, etc.)
- **Domain-specific filters** (e.g., "only studies involving commercial aviation" or "only human subjects")

Present criteria in a clear table format:

| # | Criterion | Inclusion | Exclusion |
|---|-----------|-----------|-----------|
| IC1 | Time period | 2015–2025 | Before 2015 |
| IC2 | Language | English | Non-English |
| ... | ... | ... | ... |

**1.3 Select Databases**

Recommend databases based on the user's field. Read `references/databases.md` for detailed
guidance on database-specific syntax and coverage. Common combinations:

- **Engineering/CS**: Scopus + Web of Science + IEEE Xplore + ACM Digital Library
- **Health/Medical**: PubMed + Scopus + Web of Science + Cochrane Library
- **Social Sciences**: Scopus + Web of Science + PsycINFO + ERIC
- **Multidisciplinary**: Scopus + Web of Science + domain-specific database

Always include at least 2 databases. Explain to the user why each was chosen.

**1.4 Develop Search Strings**

This is where many SLRs succeed or fail. Build search strings systematically:

1. Break the research question into **key concepts** (usually 2–4)
2. For each concept, identify **synonyms, related terms, and variants** (including acronyms, British/American spelling differences, plural forms)
3. Combine synonyms within each concept using **OR**
4. Combine concepts using **AND**
5. Adapt syntax for each database (field codes, wildcards, proximity operators differ)

Example structure:
```
("concept 1 term A" OR "concept 1 term B" OR "concept 1 term C")
AND
("concept 2 term A" OR "concept 2 term B")
AND
("concept 3 term A" OR "concept 3 term B" OR "concept 3 term C")
```

Provide database-specific versions. See `references/databases.md` for syntax differences.

**1.5 Choose the Methodology Framework**

Ask the user which framework to follow, and read the corresponding reference file for detailed
guidance:
- **PRISMA 2020** — read `references/prisma2020.md`
- **Kitchenham** — read `references/kitchenham.md`

If the user isn't sure, recommend:
- PRISMA 2020 for health sciences, psychology, and general reviews
- Kitchenham for software engineering and computer science
- Either works for other fields; PRISMA is more widely recognized

**1.6 Write the Protocol Document**

Produce a formal protocol document (Word .docx) containing:
1. Title and review team
2. Background and rationale
3. Research questions
4. Inclusion/exclusion criteria
5. Search strategy (databases + search strings)
6. Study selection process (screening stages)
7. Data extraction plan
8. Quality assessment approach
9. Data synthesis method
10. Timeline (if requested)

Use the docx skill for formatting. The protocol should be ready for registration on
PROSPERO or OSF if the user desires.

---

### Phase 2 — Search Execution & Screening

**2.1 Execute Searches**

Help the user run searches by providing ready-to-paste search strings for each database.
If the user provides search results (CSV/Excel), help with:
- **Deduplication**: Identify and remove duplicate records across databases
- **Record counting**: Report totals per database and after deduplication

**2.2 Title/Abstract Screening**

If the user provides titles and abstracts (e.g., exported from a reference manager):
- Apply inclusion/exclusion criteria systematically
- For each study, provide a clear **Include / Exclude / Uncertain** recommendation with rationale
- Flag uncertain cases for the user to decide
- Track screening decisions in a structured format

**2.3 Full-Text Screening**

For uploaded full-text PDFs:
- Read each paper and assess against inclusion/exclusion criteria
- Document reasons for exclusion (these go into the PRISMA flow diagram)
- Produce a screening log

**2.4 Generate PRISMA Flow Diagram**

After screening, create the PRISMA 2020 flow diagram showing:
- Records identified per database
- Duplicates removed
- Records screened (title/abstract)
- Records excluded with reasons
- Full-text articles assessed
- Full-text articles excluded with reasons
- Studies included in the final review

Generate this as an SVG or HTML visualization. See `references/prisma2020.md` for the
standard diagram structure.

---

### Phase 3 — Data Extraction & Quality Assessment

**3.1 Design the Data Extraction Form**

Create a structured data extraction spreadsheet (Excel .xlsx) with columns tailored to the
research questions. Standard columns include:

- Study ID, Author(s), Year, Title, Journal/Conference
- Study design, Sample size, Country/Context
- Key findings relevant to each research question
- Limitations noted by authors
- Quality assessment score

Add domain-specific columns based on the research questions. Use the xlsx skill for formatting.

**3.2 Extract Data from Included Studies**

If the user provides the included papers (as PDFs), systematically extract data into the
extraction form. Be thorough and faithful to what each paper reports — never fabricate or
infer data that isn't stated.

**3.3 Quality Assessment**

Apply appropriate critical appraisal tools based on study designs. Read
`references/quality-assessment.md` for detailed checklists:

- **CASP** (Critical Appraisal Skills Programme) — for qualitative studies, RCTs, cohort studies
- **JBI** (Joanna Briggs Institute) — comprehensive suite covering many study types
- **Newcastle-Ottawa Scale** — for observational studies (cohort, case-control)
- **DARE criteria** — for assessing existing systematic reviews
- **Custom checklists** — when standard tools don't fit (e.g., for grey literature or technical reports)

For each included study, produce a quality score and a brief justification. Summarize quality
across all studies in a table.

---

### Phase 4 — Synthesis & Reporting

**4.1 Data Synthesis**

Choose the appropriate synthesis approach based on the data:

- **Narrative synthesis** — when studies are too heterogeneous for statistical pooling. Organize
  by themes, chronology, or methodology. Identify patterns, contradictions, and trends.
- **Thematic synthesis** — group findings into themes that emerge across studies
- **Meta-analysis guidance** — if the user has quantitative data suitable for meta-analysis,
  guide them on effect size calculation, heterogeneity assessment (I^2), and forest plot
  interpretation. Note: Claude cannot run statistical meta-analysis software, but can help
  structure the data and interpret results.

**4.2 Write the SLR Report**

Produce the final report as a Word document (.docx) following the chosen framework's structure.
Use the docx skill for professional formatting.

**PRISMA 2020 structure:**
1. Title
2. Abstract (structured: Background, Objectives, Methods, Results, Conclusions)
3. Introduction (Rationale, Objectives)
4. Methods (Protocol registration, Eligibility criteria, Information sources, Search strategy,
   Selection process, Data extraction, Quality assessment, Synthesis methods)
5. Results (Study selection — with PRISMA flow, Study characteristics, Quality assessment results,
   Synthesis results)
6. Discussion (Summary of evidence, Limitations, Implications)
7. References

**Kitchenham structure:**
1. Title
2. Abstract
3. Introduction
4. Background
5. Review Method (Research questions, Search strategy, Study selection, Data extraction,
   Quality assessment, Data synthesis)
6. Results (Search results, Included studies, Quality assessment, Data synthesis by RQ)
7. Discussion
8. Threats to Validity
9. Conclusions
10. References

**4.3 Identify Gaps and Future Directions**

After synthesis, identify and report:
- What questions remain unanswered
- Where evidence is weak or conflicting
- What methodological improvements future studies should adopt
- What populations, contexts, or variables are understudied

This is where the SLR connects back to the research-gap-analyst skill — the gaps identified
here are grounded in the systematic evidence base.

---

## Deliverables Summary

Depending on what the user needs, this skill can produce any combination of:

| Deliverable | Format | When |
|-------------|--------|------|
| SLR Protocol | .docx | Phase 1 — before the review begins |
| Search Strings | Text (in chat or .docx) | Phase 1 — ready to paste into databases |
| Screening Log | .xlsx | Phase 2 — during screening |
| PRISMA Flow Diagram | .svg or .html | Phase 2 — after screening |
| Data Extraction Form | .xlsx | Phase 3 — template or filled |
| Quality Assessment Summary | .xlsx or in report | Phase 3 — after appraisal |
| Final SLR Report | .docx | Phase 4 — the main deliverable |
| Gap Analysis | In report or separate | Phase 4 — future directions |

---

## Citation Style

Default to **APA 7th edition** for the SLR report, as it's the most widely used in systematic
reviews. Switch to IEEE, Vancouver, or another style if the user specifies a target journal
or preference.

---

## Important Principles

**Reproducibility is paramount.** Every decision should be documented clearly enough that
another researcher could repeat the review and reach similar conclusions. This means explicit
criteria, documented search strings, and transparent screening decisions.

**Never fabricate data.** When extracting data from papers, report exactly what the paper
states. If something is ambiguous, flag it for the user rather than guessing.

**Acknowledge limitations.** No SLR is perfect. Be upfront about limitations: language
restrictions, database coverage gaps, potential publication bias, and any deviations from
the protocol.

**Adapt to the user's stage.** Not every user starts from scratch. Ask where they are and
provide exactly the help they need — whether that's designing a protocol from zero or
synthesizing a stack of already-screened papers.

---

## Edge Cases

- **Very broad topic**: Help the user narrow scope before proceeding. A good SLR has a focused,
  answerable question.
- **Very few studies found**: This is itself a finding. Document the search thoroughly and
  consider broadening criteria or including grey literature.
- **User wants speed over rigor**: Suggest a Rapid Review or Scoping Review instead. These are
  legitimate review types with lighter methodology. Adjust the process accordingly.
- **Mixed-methods studies**: Use SPIDER framework for the question and JBI mixed-methods
  checklist for quality assessment.
- **User has no access to databases**: Help with Google Scholar as a fallback, but note the
  limitations (no field-specific search, inconsistent results, not recommended as sole source
  for an SLR).
