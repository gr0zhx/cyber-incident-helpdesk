---
name: research-gap-analyst
description: >
  Use this skill whenever a user wants to conduct research, identify research gaps, analyze literature,
  or explore what is unknown or understudied in a field. Triggers include: "find research gaps",
  "conduct a literature review", "what has been studied about X", "what do we not know about X",
  "analyze research on", "review papers on", "what are the open questions in", "help me write a
  research proposal", "summarize findings in the field of", "what research is missing on", or any
  request involving uploaded PDFs, abstracts, or drafts that need academic/professional analysis.
  Also trigger when the user provides a domain name, topic, or question and wants a structured
  analysis of the state of knowledge. Always use this skill when research, literature, or gap
  analysis is involved — even if the user doesn't explicitly say "skill" or "gap analysis".
---

# Research Gap Analyst

A comprehensive skill for conducting deep research, synthesizing literature, identifying knowledge
gaps, and producing structured reports with actionable next steps — tailored for industry
professionals.

---

## Input Types Supported

Handle any combination of the following:
- **Topic or research question** typed in chat (e.g., "What are the gaps in federated learning for healthcare?")
- **Uploaded PDF papers** — read and extract key findings, methods, limitations
- **Field or domain name** — treat as a broad scoping task
- **Existing draft or abstract** — analyze for gaps relative to the current literature

If the user provides multiple input types, synthesize them all.

---

## Workflow

### Step 1 — Scope Clarification (if needed)
If the topic is ambiguous or very broad, ask ONE clarifying question to narrow scope before proceeding. For specific, well-defined topics, proceed directly.

### Step 2 — Literature Search
Use web search to gather sources. Target **20+ sources** for a comprehensive analysis. Search strategy:
- Start with broad queries, then narrow by subtopic, methodology, or time period
- Prioritize: peer-reviewed papers, preprints (arXiv, SSRN), industry whitepapers, standards bodies, and reputable technical reports
- Search multiple angles: foundational work, recent advances (last 3 years), systematic reviews, and industry applications
- Look explicitly for what is *missing*: search "challenges in X", "limitations of X", "future work X", "open problems X"

### Step 3 — Read Uploaded Materials (if any)
If the user uploaded PDFs or provided an abstract/draft:
- Extract: research questions, methodology, key findings, stated limitations, and suggested future work
- Cross-reference with web sources to assess novelty and positioning

### Step 4 — Synthesis & Gap Identification
Analyze all collected sources to identify:

**Thematic clusters** — group existing research into 3–6 major themes or subtopics

**Gap taxonomy** — classify each identified gap as one of:
- 🔬 *Empirical gap* — lacks real-world data, experiments, or validation
- 🧩 *Conceptual gap* — theoretical frameworks are underdeveloped or contested
- 🌍 *Population/context gap* — studied in limited demographics, geographies, or industries
- 🔗 *Methodological gap* — existing methods are flawed, outdated, or untested
- 🏭 *Application gap* — research exists but hasn't been translated to industry practice
- ⏳ *Temporal gap* — findings may be outdated given recent technological or market changes

### Step 5 — Produce the Full Report

Deliver the report in this structure:

---

#### 📋 Executive Summary
3–5 sentence overview of the field's state and the most critical gaps found.

#### 📚 Literature Summary
Organized by thematic cluster. For each cluster:
- What has been studied and what is known
- Key representative sources (IEEE citation style)
- Dominant methodologies and datasets used

#### 🔍 Research Gap Analysis
For each identified gap (aim for 5–10 gaps):
- **Gap title** (short, clear label)
- **Type** (from gap taxonomy above)
- **Description** — what is missing and why it matters for industry
- **Evidence** — which sources point to this gap (cite in IEEE style)
- **Impact** — consequences of leaving this gap unaddressed

#### 🗺️ Visual Concept Map
After the gap analysis, produce an SVG or HTML concept map showing:
- Central topic in the middle
- Thematic clusters radiating outward
- Identified gaps highlighted (use a distinct color, e.g. orange/red nodes)
- Connections between related themes

Use the `visualize:show_widget` tool for this. Keep it clean and readable.

#### 📝 Research Proposal Outline
A structured outline a professional could use to pitch or begin a research project:
- **Title** (suggested)
- **Problem Statement**
- **Research Questions** (3–5 specific, answerable questions)
- **Proposed Methodology** — matched to the gap type (e.g., empirical gaps → field studies; methodological gaps → benchmarking studies)
- **Expected Contributions**
- **Positioning** — how this fills the identified gap relative to existing work

#### 🚀 Actionable Next Steps
Concrete recommendations for an industry professional, including:
- Recommended methodologies or frameworks to adopt
- Potential collaboration angles (academia, consortia, standards bodies)
- Relevant funding sources or grant programs (where applicable)
- Conferences, journals, or communities to engage with
- Estimated complexity/effort level for each next step (Low / Medium / High)

---

## Citation Style

Use **IEEE** format throughout:
- In-text: [1], [2], [3] etc.
- Reference list at the end, numbered in order of appearance
- Format: `[N] A. Author, "Title," *Journal/Conf.*, vol. X, no. Y, pp. Z–Z, Year. [Online]. Available: URL`
- For web sources without full metadata, use best available fields

---

## Tone & Style

- Write for **industry professionals**: clear, precise, jargon-aware but not unnecessarily academic
- Avoid filler phrases — every sentence should carry information
- Use headers, tables, and bullet points for scanability
- Be direct about uncertainty: if a gap is speculative or based on limited evidence, say so

---

## Quality Checks Before Delivering

Before presenting the report, verify:
- [ ] At least 20 sources cited
- [ ] Gaps are specific and actionable (not vague like "more research is needed")
- [ ] Each gap has at least one citation as evidence
- [ ] Proposal outline is coherent and grounded in the gaps found
- [ ] Next steps are concrete and relevant to an industry context
- [ ] Concept map is included

---

## Edge Cases

- **Very niche topic with few sources**: Broaden search to adjacent fields; note the scarcity itself as a finding
- **Contradictory findings across sources**: Flag the contradiction explicitly as a gap (contested knowledge)
- **User provides a full draft paper**: Focus gap analysis on how the draft's contributions relate to the wider field; identify gaps the paper does *not* address
- **Rapidly evolving field**: Prioritize sources from the last 2 years; note that older gaps may already be partially addressed
