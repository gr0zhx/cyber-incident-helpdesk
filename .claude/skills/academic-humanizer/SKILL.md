---
name: academic-humanizer
description: >
  Use this skill whenever a researcher, student, or academic writer needs to rewrite, paraphrase,
  or improve text so it reads as authentically human-written and bypasses AI content detection
  tools (Turnitin, GPTZero, Originality.ai, etc.) used by reputable journals and institutions.
  Trigger immediately when the user says things like: "improve my paragraph", "make this sound
  more human", "rewrite this academic text", "paraphrase this for my paper", "humanize this",
  "this sounds too AI-generated", "beat AI detector", "make this less robotic", "rephrase my
  abstract/introduction/methodology/conclusion". Also trigger when the user pastes any academic
  text (sentences, paragraphs, sections) and asks for improvement, even without explicitly
  mentioning AI detection. Works across all academic domains: journal papers, theses, proposals,
  technical reports, white papers. ALWAYS use this skill for any academic writing humanization
  task — do not attempt ad-hoc rewriting without it.
---

# Academic Humanizer Skill

Transform AI-generated or AI-sounding academic text into authentic, human-quality writing that
passes AI detection tools while preserving — and often improving — scientific rigor and clarity.

---

## Core Philosophy

AI detectors (Turnitin, GPTZero, Originality.ai) flag text based on two main signals:

1. **Low perplexity** — text that is too "predictable" word-by-word
2. **Low burstiness** — uniform sentence length and rhythm throughout

Human academic writers naturally produce **high perplexity + high burstiness**: unpredictable
word choices, wildly varying sentence lengths, rhetorical rhythm, and opinionated hedging.
Your job is to engineer both.

---

## The 6-Layer Humanization Framework

Apply ALL six layers on every rewrite. Do not skip any layer even if the text seems fine.

### Layer 1 — Burstiness Injection (Sentence Length Variation)
- Deliberately alternate between very short sentences (5–10 words) and long, complex ones (30–50 words)
- Break up uniform medium-length sentences (15–20 words each) — this is the primary AI fingerprint
- Use fragments sparingly for rhetorical effect: "This matters."
- Example pattern: [long] → [short] → [long] → [medium] → [very short] → [long]

### Layer 2 — Perplexity Elevation (Unpredictable Word Choice)
- Replace high-frequency AI vocabulary with domain-specific, field-native alternatives
- Avoid these AI-typical phrases and replace them:
  - "It is worth noting that" → "Notably," / "Curiously," / "Of particular interest,"
  - "Furthermore" → "What follows from this," / "This extends to," / "Beyond this,"
  - "In conclusion" → "Taken together," / "The picture that emerges," / "Stepping back,"
  - "It is important to" → "Crucially," / "The stakes here are," / drop entirely
  - "Significantly" → "Markedly," / "In a striking departure from," / field-specific term
  - "Utilize" → "use" (always)
  - "Leverage" → "employ," "apply," "draw on"
  - "Facilitate" → "enable," "allow," "support"
  - "In order to" → "to" (always)
  - "Due to the fact that" → "because" (always)
- Introduce occasional domain jargon used in a slightly unexpected collocation

### Layer 3 — Voice & Agency Shift (Active Voice + Human Subject)
- Convert passive constructions to active where meaningful
- Reintroduce human researcher agency: "We observe..." / "Our analysis reveals..." / "The data suggest..."
- Use first-person plural ("we") for multi-author academic work; first-person singular ("I") for theses
- Reserve passive voice for genuine methodological convention (e.g., "samples were collected")

### Layer 4 — Hedging & Epistemic Stance (Human Uncertainty Markers)
- Humans hedge; AI overclaims or over-disclaims uniformly
- Inject calibrated uncertainty:
  - "appears to," "seems to," "tends to," "may reflect"
  - "arguably," "plausibly," "one might contend"
  - "to our knowledge," "as far as we can determine"
- Avoid over-hedging every sentence — cluster hedges, then make confident claims

### Layer 5 — Rhetorical Micro-Imperfections (Non-Uniform Word Choice)
- Vary how you refer to the same concept across paragraphs (synonymic rotation)
- Use occasional colloquial-adjacent phrasing even in formal text: "put differently," "in plain terms," "to be precise"
- Add a parenthetical aside, em-dash clause, or bracketed qualifier — humans do this naturally
- Introduce one slightly unusual but accurate word per paragraph (elevates perplexity sharply)

### Layer 6 — Structural Coherence & Flow (Paragraph-Level)
- Ensure each paragraph has a clear topic sentence, development, and micro-conclusion
- Add transitional logic that connects ideas causally, not just sequentially
  - Not: "Additionally, X. Furthermore, Y."
  - But: "X follows directly from this. Y, in turn, complicates the picture."
- Use cohesive devices: pronoun reference, lexical repetition, connective adverbials

---

## Output Behavior

Adapt output based on user intent, inferred from context:

| User Signal | Output Mode |
|---|---|
| "rewrite this" / pastes text only | **Direct output** — return humanized text, no commentary |
| "improve my paragraph" | **Direct output** — clean rewrite only |
| "check and rewrite" | **Brief note** on 2–3 main issues, then rewrite |
| "explain what you changed" | **Before/After comparison** with brief annotation |
| "step by step" / "analyze" | **Full analysis**: issue diagnosis → layer-by-layer notes → rewrite |

**Default when ambiguous**: Direct output (clean rewrite). Offer "Want a before/after comparison?" at the end.

---

## Quality Checklist (Internal — Apply Before Outputting)

Before returning any rewrite, verify:

- [ ] No two consecutive sentences of similar length
- [ ] Zero occurrences of: "it is worth noting," "furthermore," "in conclusion," "significantly," "utilize," "leverage," "in order to," "due to the fact that"
- [ ] At least one sentence under 10 words per paragraph
- [ ] At least one sentence over 35 words per paragraph
- [ ] Active voice is dominant (>60% of sentences)
- [ ] Hedging language present but not on every sentence
- [ ] Scientific meaning and accuracy 100% preserved
- [ ] Field-appropriate register maintained (no casual register in methodology sections)
- [ ] No fabricated citations, statistics, or claims introduced

---

## Domain-Specific Register Notes

Load the appropriate register when processing:

**Journal paper (Introduction/Literature Review)**
→ Formal, citation-heavy, hypothesis-framing. Use "the present study," "extant literature," "empirical evidence suggests"

**Journal paper (Methodology)**
→ Precision-first. Passive voice acceptable here. Use exact measurement language.

**Journal paper (Results/Discussion)**
→ Active voice, interpretive, hedged. "Our findings indicate..." "This aligns with..."

**Thesis / Proposal**
→ Can use slightly more personal voice. "This thesis argues..." "I propose..."

**Technical Report / White Paper**
→ Direct, structured, minimal hedging. Action-oriented language. Use numbered findings.

---

## Anti-Patterns to Avoid

These are rewriting mistakes that still trigger detectors or degrade quality:

❌ Simply replacing synonyms without changing sentence structure (detectors see through this)
❌ Over-hedging every clause — creates new AI fingerprint ("seems to appear to potentially suggest")
❌ Removing all passive voice from methodology — unnatural, flags as over-edited
❌ Making text deliberately ungrammatical — detectors ≠ grammar checkers; this backfires
❌ Adding citations that don't exist in the original
❌ Changing technical terms to lay terms (breaks scientific precision)
❌ Uniform burstiness injection (alternating short-long-short-long predictably = new pattern)

---

## Example Transformation

**Input (AI-typical):**
> "It is worth noting that the results obtained from the experiment were significantly different from the baseline. Furthermore, this finding suggests that the proposed method is effective in addressing the problem. In conclusion, the approach demonstrates considerable promise for future applications."

**Output (Humanized):**
> "The experimental results diverged markedly from the baseline — more so than we anticipated. This gap, we argue, reflects the core strength of the proposed method: it restructures the problem rather than approximating a solution. Whether this translates to scalable real-world performance remains an open question, though early indicators are encouraging."

**What changed:**
- Burstiness: 3 uniform medium sentences → varied (long, long, medium)
- Eliminated: "it is worth noting," "significantly," "furthermore," "in conclusion"
- Added: em-dash clause, hedged final sentence, active agency ("we argue")
- Perplexity: "diverged markedly," "restructures the problem" — unpredictable collocations

---

## Usage Examples

**User pastes paragraph, no instruction:**
→ Apply all 6 layers, return clean rewrite. Offer comparison at end.

**"Make my abstract sound less AI-generated":**
→ Apply all 6 layers to abstract, return rewrite. No preamble needed.

**"Review and improve this methods section":**
→ Light Layer 3 (keep appropriate passive), heavy Layer 1 & 2. Return rewrite.

**"Explain what you changed in my introduction":**
→ Before/After comparison with annotation by layer.
