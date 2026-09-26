# Template 02 · Data-Readiness Scorecard

Rate every data source RED, AMBER or GREEN on each dimension, and support each rating with a real sample, an access test and an owner interview.
Curriculum links: Turn 115 (data readiness), 52 (lineage and deletion), 81 (privacy law), 42 (parsing).

| Source | Exists | Access | Quality | Owner | Legal use | Sensitivity | Evaluability | Overall |
|---|---|---|---|---|---|---|---|---|
| e.g. SharePoint matter files | G | A (only a service account; OBO not approved) | A (30% scanned PDFs) | G | A (client confidentiality clauses) | R (privileged) | G | AMBER |

## Dimension checklist
- **Exists**: Is the data actually captured, and over what time span? Are there gaps?
- **Access**: Can we read it programmatically, with the right identity? Do we know the rate limits? Is there a sandbox copy?
- **Quality**: Profile 50 to 200 real samples: formats, OCR needs, duplicates, missing fields, language mix and code-mixing.
- **Owner**: A named person who can answer questions and approve use.
- **Legal use**: Legal basis and purpose limitation; licences; contracts; residency; consent for training versus inference.
- **Sensitivity**: PII, PHI, PCI, privileged or confidential data, children's data, special-category data.
- **Evaluability**: Can we build a labelled test set? Do experts agree with each other? (Measure the agreement rate on 30+ items.)
- **Permissions**: Are source ACLs available, and can we propagate them to the index? How fast do permission changes propagate? (This is a critical question for RAG projects.)
- **Freshness**: How often does the data change, and is change-data-capture or a webhook available?
- **Deletion**: If a record is deleted or a data subject asks for erasure, can we find every derived copy (chunks, embeddings, caches, eval sets, logs)?

## Output
1. The scorecard above
2. A "minimum viable data" plan: which GREEN sources to start with
3. A remediation plan for AMBER and RED sources, with owners and dates
4. An updated scope, estimate and risk list (feed these into the SOW, Template 03)
