# PRISMA 2020 Reference Guide

## Overview

PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) 2020 is the updated
guideline for reporting systematic reviews. It replaced the original 2009 version and includes
significant updates to reflect advances in systematic review methodology.

PRISMA 2020 consists of a **27-item checklist** and a **flow diagram** template.

---

## The 27-Item Checklist

### Title
1. **Title**: Identify the report as a systematic review

### Abstract
2. **Abstract**: Structured summary (background, objectives, data sources, study eligibility,
   synthesis methods, results, limitations, conclusions, registration)

### Introduction
3. **Rationale**: Describe the rationale in the context of existing knowledge
4. **Objectives**: Provide an explicit statement of the question(s) using PICO or equivalent

### Methods
5. **Eligibility criteria**: Specify inclusion/exclusion criteria with rationale
6. **Information sources**: List all databases, registers, websites, organizations, reference
   lists searched, with dates
7. **Search strategy**: Present full search strategies for all databases with filters/limits
8. **Selection process**: Describe methods for screening (independent reviewers, automation tools)
9. **Data collection process**: Describe methods for extracting data (forms, piloting, independent
   extraction, consensus)
10. **Data items**: List all outcome domains and variables sought, with assumptions made
11. **Study risk of bias assessment**: Describe methods and tools used for quality assessment
12. **Effect measures**: Specify effect measures used (e.g., risk ratio, mean difference)
13. **Synthesis methods**: Describe processes for deciding which studies to group, tabulating data,
    exploring heterogeneity, sensitivity analyses
14. **Reporting bias assessment**: Describe methods for assessing risk of publication bias
15. **Certainty assessment**: Describe methods for assessing certainty (e.g., GRADE)

### Results
16. **Study selection**: Describe results of the search and selection process (with PRISMA flow
    diagram)
17. **Study characteristics**: Present characteristics of each included study
18. **Risk of bias in studies**: Present risk of bias assessments for each study
19. **Results of individual studies**: Present results for all outcomes per study
20. **Results of syntheses**: Present results of each synthesis (with forest plots if applicable)
21. **Reporting biases**: Present assessments of reporting bias (e.g., funnel plots)
22. **Certainty of evidence**: Present certainty assessments for each outcome

### Discussion
23. **Discussion**: Interpret findings in context, discuss limitations, compare with other reviews
24. **Other information**: Provide registration info, protocol availability, funding, conflicts of
    interest

### Other
25. **Registration and protocol**: Registration number and where the protocol can be accessed
26. **Support**: Sources of financial/non-financial support
27. **Competing interests**: Declaration of competing interests

---

## PRISMA 2020 Flow Diagram

The flow diagram has 4 sections flowing top to bottom:

```
IDENTIFICATION
├── Records identified from databases (n = ?)
│   ├── Database 1 (n = ?)
│   ├── Database 2 (n = ?)
│   └── Database 3 (n = ?)
├── Records identified from other sources (n = ?)
│   ├── Citation searching (n = ?)
│   ├── Grey literature (n = ?)
│   └── Other (n = ?)
└── Records removed before screening
    ├── Duplicate records (n = ?)
    ├── Records marked as ineligible by automation tools (n = ?)
    └── Records removed for other reasons (n = ?)

SCREENING
├── Records screened (n = ?)
│   └── Records excluded (n = ?)
├── Reports sought for retrieval (n = ?)
│   └── Reports not retrieved (n = ?)
└── Reports assessed for eligibility (n = ?)
    └── Reports excluded with reasons:
        ├── Reason 1 (n = ?)
        ├── Reason 2 (n = ?)
        └── Reason 3 (n = ?)

INCLUDED
├── Studies included in review (n = ?)
└── Reports of included studies (n = ?)
```

### Generating the Flow Diagram as SVG

When creating the PRISMA flow diagram, generate it as a clean SVG with:
- Rectangular boxes for each stage with counts
- Arrows showing the flow from identification to inclusion
- Side boxes for exclusions (connected with arrows from the right)
- Color coding: light blue for process stages, light red/orange for exclusions, light green for included
- Clear, readable font (sans-serif, 12-14px)
- Overall dimensions around 800x1000px

Use this HTML/SVG template approach:
1. Create an HTML file containing an embedded SVG
2. Populate the numbers from the screening data
3. Save as .html for interactive viewing

---

## Key Differences from PRISMA 2009

- New items on automation tools, protocol deviations, certainty assessment
- Flow diagram updated to distinguish database vs. other source records
- Abstract checklist expanded
- Emphasis on reporting the full search strategy
- New guidance on reporting equity-relevant data

---

## When to Recommend PRISMA

PRISMA is appropriate when:
- The review follows a systematic search and selection process
- The goal is evidence synthesis (not just mapping the literature)
- The target audience expects PRISMA compliance (most health sciences journals require it)
- The user plans to register the protocol (PROSPERO requires PRISMA-aligned reviews)

PRISMA is less necessary for:
- Scoping reviews (use PRISMA-ScR instead)
- Rapid reviews (lighter reporting is acceptable)
- Narrative reviews (no formal reporting guideline required)
