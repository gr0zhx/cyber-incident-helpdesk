# Academic Database Reference

This reference covers search syntax and characteristics for major academic databases used in SLRs.

---

## Scopus

**Coverage**: Multidisciplinary. ~27,000 journals, 113,000+ conferences. Strong in engineering,
technology, health sciences, social sciences.

**Search syntax**:
- Field codes: `TITLE-ABS-KEY()` (title, abstract, keywords), `TITLE()`, `ABS()`, `KEY()`
- Boolean: `AND`, `OR`, `AND NOT`
- Wildcards: `*` (any characters), `?` (single character)
- Phrases: use double quotes `"machine learning"`
- Proximity: `W/n` (within n words), `PRE/n` (precedes within n words)

**Example**:
```
TITLE-ABS-KEY("systematic review" OR "literature review") 
AND TITLE-ABS-KEY("cybersecurity" OR "cyber security" OR "information security")
AND PUBYEAR > 2014
```

**Export**: CSV, BibTeX, RIS. Can export up to 2,000 records at a time.

---

## Web of Science

**Coverage**: Multidisciplinary. Core Collection covers ~21,000 journals. Strong citation indexing.

**Search syntax**:
- Field tags: `TS=` (topic: title + abstract + keywords), `TI=` (title), `AB=` (abstract)
- Boolean: `AND`, `OR`, `NOT`
- Wildcards: `*` (any characters), `?` (single character)
- Phrases: use double quotes
- Proximity: `NEAR/n` (within n words)

**Example**:
```
TS=("systematic review" OR "literature review") 
AND TS=("cybersecurity" OR "cyber security" OR "information security")
```

**Timespan**: Can be set in the interface or via `PY=` for publication year.

**Export**: Tab-delimited, CSV, BibTeX, RIS. Up to 1,000 records per export.

---

## PubMed

**Coverage**: Biomedical and life sciences. ~36 million citations. Includes MEDLINE.

**Search syntax**:
- Field tags: `[Title/Abstract]`, `[Title]`, `[MeSH Terms]`, `[Author]`
- Boolean: `AND`, `OR`, `NOT`
- Wildcards: `*` (truncation only, at end of word)
- Phrases: use double quotes
- MeSH: Use Medical Subject Headings for precise medical terminology

**Example**:
```
("systematic review"[Title/Abstract] OR "meta-analysis"[Title/Abstract])
AND ("cybersecurity"[Title/Abstract] OR "information security"[Title/Abstract])
AND ("2015"[Date - Publication] : "2025"[Date - Publication])
```

**Special features**: 
- MeSH terms provide standardized medical vocabulary
- Publication type filters (e.g., `"Review"[Publication Type]`)
- Clinical queries filters for therapy, diagnosis, prognosis

**Export**: CSV, MEDLINE, PMID list, RIS, BibTeX via PubMed's "Save" function.

---

## IEEE Xplore

**Coverage**: Electrical engineering, computer science, electronics. ~6 million documents.

**Search syntax**:
- Field-specific: "All Metadata", "Document Title", "Abstract", "Author Keywords"
- Boolean: `AND`, `OR`, `NOT`
- Wildcards: `*` (multi-character), `?` (single character)
- Phrases: use double quotes
- Proximity: `NEAR/n`

**Example**:
```
("All Metadata":"systematic review" OR "All Metadata":"literature review")
AND ("All Metadata":"cybersecurity" OR "All Metadata":"cyber security")
```

**Export**: CSV, BibTeX, RIS. Up to 2,000 records.

---

## ACM Digital Library

**Coverage**: Computing and information technology. ACM publications + selected others.

**Search syntax**:
- Field-specific: `Title`, `Abstract`, `Keyword`
- Boolean: `AND`, `OR`, `NOT`
- Phrases: use double quotes
- Uses a query builder interface; advanced syntax via the search box

**Example**:
```
[[All: "systematic review"] OR [All: "literature review"]]
AND [[All: "cybersecurity"] OR [All: "information security"]]
```

**Export**: BibTeX, CSV, RIS via the "Export Citations" option.

---

## Google Scholar

**Coverage**: Broad but unstructured. Includes journals, conferences, theses, books, grey
literature, preprints.

**Limitations for SLRs**:
- No field-specific search (can't search abstract-only)
- Cannot export more than ~1,000 results
- No API access for bulk export
- Results not fully reproducible (personalized, algorithm changes)
- No transparent selection criteria for included sources

**When to use in an SLR**:
- As a **supplementary** source (never the sole source)
- For finding grey literature, theses, and preprints
- For snowball searching (forward/backward citation tracking)
- When primary databases miss relevant work

**Search tips**:
- Use `allintitle:` to search titles only
- Use `author:` for author searches
- Date range filtering available in advanced search
- Use Publish or Perish software for better export capabilities

---

## Database Selection Strategy

For a rigorous SLR, select databases based on:

1. **Field coverage**: Choose databases that index the journals/conferences relevant to your topic
2. **Minimum 2 databases**: One database alone is insufficient; overlapping coverage helps catch
   what one might miss
3. **At least one multidisciplinary**: Scopus or Web of Science provides broad coverage
4. **At least one domain-specific**: IEEE Xplore for engineering, PubMed for health, etc.
5. **Consider grey literature**: Theses databases (ProQuest), preprint servers (arXiv, SSRN),
   organizational repositories

Document your rationale for database selection in the protocol.
