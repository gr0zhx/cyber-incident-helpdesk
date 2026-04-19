# Quality Assessment Tools Reference

This reference covers the major critical appraisal tools used in SLRs. Choose the tool that
matches the study designs in your review.

---

## CASP (Critical Appraisal Skills Programme)

**Website**: casp-uk.net

CASP provides separate checklists for different study types. Each checklist has ~10-12 questions
answered as Yes / Can't Tell / No.

### CASP for Randomised Controlled Trials (RCTs)
1. Did the study address a clearly focused research question?
2. Was the assignment of participants to interventions randomised?
3. Were all participants who entered the study accounted for at its conclusion?
4. Were participants, investigators, and outcome assessors blind to the intervention?
5. Were the study groups similar at the start of the trial?
6. Apart from the intervention, were the groups treated equally?
7. How large was the treatment effect?
8. How precise was the estimate of the treatment effect?
9. Can the results be applied to the local population?
10. Were all clinically important outcomes considered?
11. Are the benefits worth the harms and costs?

### CASP for Qualitative Research
1. Was there a clear statement of the aims of the research?
2. Is a qualitative methodology appropriate?
3. Was the research design appropriate to address the aims?
4. Was the recruitment strategy appropriate?
5. Was the data collected in a way that addressed the research issue?
6. Has the relationship between researcher and participants been adequately considered?
7. Have ethical issues been taken into consideration?
8. Was the data analysis sufficiently rigorous?
9. Is there a clear statement of findings?
10. How valuable is the research?

### CASP for Cohort Studies
1. Did the study address a clearly focused issue?
2. Was the cohort recruited in an acceptable way?
3. Was the exposure accurately measured?
4. Was the outcome accurately measured?
5. Have the authors identified all important confounding factors?
6. Was the follow-up complete and long enough?
7. What are the results?
8. How precise are the results?
9. Do you believe the results?
10. Can the results be applied to the local population?
11. Do the results fit with other available evidence?
12. What are the implications for practice?

---

## JBI (Joanna Briggs Institute) Critical Appraisal Tools

**Source**: jbi.global

JBI provides checklists for 13 different study types. Each item is scored as
Yes / No / Unclear / Not Applicable.

### JBI Checklist for Analytical Cross-Sectional Studies (8 items)
1. Were the criteria for inclusion in the sample clearly defined?
2. Were the study subjects and setting described in detail?
3. Was the exposure measured in a valid and reliable way?
4. Were objective, standard criteria used for measurement of the condition?
5. Were confounding factors identified?
6. Were strategies to deal with confounding factors stated?
7. Were the outcomes measured in a valid and reliable way?
8. Was appropriate statistical analysis used?

### JBI Checklist for Case Studies (8 items)
1. Were the patient's demographic characteristics clearly described?
2. Was the patient's history clearly described and presented as a timeline?
3. Was the current clinical condition clearly described?
4. Were diagnostic tests or assessment methods and results clearly described?
5. Was the intervention or treatment procedure clearly described?
6. Was the post-intervention clinical condition clearly described?
7. Were adverse events or unanticipated events identified and described?
8. Does the case report provide takeaway lessons?

### JBI Checklist for Surveys (8+ items)
Available for prevalence studies, covering: sample frame appropriateness, sampling method,
sample size adequacy, description of subjects and setting, data analysis coverage, response
rate, and measurement reliability.

---

## Newcastle-Ottawa Scale (NOS)

**For**: Observational studies (cohort and case-control)

Scored on a star system (max 9 stars for cohort, max 9 for case-control).

### Cohort Studies — Three Domains:

**Selection (max 4 stars)**
1. Representativeness of the exposed cohort
2. Selection of the non-exposed cohort
3. Ascertainment of exposure
4. Demonstration that outcome was not present at start

**Comparability (max 2 stars)**
5. Comparability based on design or analysis (controls for most important factor = 1 star,
   controls for additional factor = 1 star)

**Outcome (max 3 stars)**
6. Assessment of outcome
7. Was follow-up long enough for outcomes to occur?
8. Adequacy of follow-up of cohorts

### Case-Control Studies — Three Domains:

**Selection (max 4 stars)**
1. Is the case definition adequate?
2. Representativeness of the cases
3. Selection of controls
4. Definition of controls

**Comparability (max 2 stars)**
5. Comparability of cases and controls

**Exposure (max 3 stars)**
6. Ascertainment of exposure
7. Same method of ascertainment for cases and controls
8. Non-response rate

### Scoring Interpretation:
- 7-9 stars: High quality (low risk of bias)
- 4-6 stars: Moderate quality
- 0-3 stars: Low quality (high risk of bias)

---

## DARE Criteria (for Assessing Existing Systematic Reviews)

Use when your SLR includes previously published systematic reviews as sources.

1. Was an adequate search conducted?
2. Were the inclusion criteria appropriate and applied?
3. Was the quality of included studies assessed?
4. Are sufficient details of individual studies presented?
5. Were the studies adequately synthesized?

Score: each criterion met = 1 point (max 5).

---

## Custom Quality Assessment

When standard tools don't fit (common in software engineering, grey literature, or
interdisciplinary reviews), create a custom checklist. A good custom checklist should:

1. Cover **reporting quality**: Is the study clearly described?
2. Cover **methodological rigor**: Is the approach sound?
3. Cover **relevance**: Does it address the review's research questions?
4. Use a consistent scoring scheme (e.g., Yes=1, Partial=0.5, No=0)
5. Be piloted on 2-3 studies before full deployment
6. Be documented in the protocol

Example custom checklist for software engineering empirical studies:
1. Are the research objectives clearly stated?
2. Is the study design described and justified?
3. Are threats to validity discussed?
4. Is the data collection process described?
5. Is the data analysis approach appropriate?
6. Are the findings clearly stated?
7. Are limitations acknowledged?
8. Is the study replicable based on the description?

---

## Choosing the Right Tool

| Study Design | Recommended Tool |
|-------------|-----------------|
| RCTs | CASP RCT, Cochrane RoB 2 |
| Cohort studies | Newcastle-Ottawa, CASP Cohort |
| Case-control studies | Newcastle-Ottawa |
| Cross-sectional | JBI Cross-Sectional |
| Qualitative | CASP Qualitative, JBI Qualitative |
| Case studies/reports | JBI Case Report |
| Surveys | JBI Prevalence |
| Mixed methods | JBI Mixed Methods, MMAT |
| Systematic reviews | DARE, AMSTAR 2 |
| SE empirical studies | Custom (Kitchenham-style) |
| Grey literature | Custom |

---

## Reporting Quality Assessment Results

In the SLR report, present quality assessment as:
1. A summary table showing each included study's scores across all criteria
2. An overall assessment of the body of evidence quality
3. Discussion of how quality influenced the synthesis (did you weight by quality? exclude low-quality studies?)
