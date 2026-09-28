# Template 07 · Compliance Obligations → Engineering Controls Map

Engineers do not need to memorise laws. They need to turn each **obligation that applies** into a **control they can build and evidence**.
Fill this in with the customer's legal/compliance owner; never self-certify legal conclusions.
Curriculum links: Turns 79–85 (EU AI Act, NIST/ISO, privacy, sector, responsible AI, provenance, copyright), 128 (governance-as-code), plus the gap register's regulation entries (global map, EU CRA and PLD, companion/minor laws, India SGI rules, employment-AI laws).

## 1. Applicability screen

| Question | Answer | Consequence |
|---|---|---|
| Where are the users, and where is the data processed? | e.g. India + EU | DPDP + GDPR; check residency |
| Does the system interact directly with people or generate synthetic content? | Yes | Transparency and labelling duties (EU AI Act Art. 50; India SGI rules; China and Korea labelling rules) |
| Does it make or influence decisions about individuals (employment, credit, insurance, health, education, essential services)? | | High-risk / automated decision-making regimes (EU AI Act Annex III; US state ADMT/employment laws) |
| Could a minor use it? Is it companion-like? | | Companion/minor-safety laws (e.g. California SB 243, New York's AI companion law), age assurance, children's-data rules (DPDP verifiable parental consent) |
| Is it a product with digital elements sold in the EU? | | EU Cyber Resilience Act (vulnerability/incident reporting from 11 Sep 2026); revised Product Liability Directive |
| Is it a regulated sector (health, finance, insurance, public sector)? | | Sector rules (HIPAA, PCI DSS, model-risk management, RBI/IRDAI/SEBI guidance) |

## 2. Obligation → control → evidence

| Obligation (source, article) | Engineering control | Owner | Evidence produced automatically? | Status |
|---|---|---|---|---|
| Tell users they are talking to an AI | UI disclosure + voice disclosure at call start; tested in E2E suite | PM + FDE | E2E test report | |
| Label synthetic media / embed provenance | C2PA manifest + visible label at generation time; strip-resistance test | FDE | Build artefact + test | |
| Keep logs for traceability | Structured traces with retention policy X; tamper-evident storage | Platform | Retention config in IaC | |
| Human oversight for high-impact decisions | Approval queue; reviewer UI shows evidence; seeded-error monitoring | FDE + Ops | Reviewer metrics dashboard | |
| Data-subject rights (access/erasure) | Lineage IDs on every chunk/embedding/cache/memory/log; deletion job with verification | FDE | Deletion job report | |
| Report actively exploited vulnerabilities within 24h/72h (CRA) | Vuln intake → triage → reporting clock in incident tooling | Security | Ticket timestamps | |
| Crisis protocol for self-harm signals (companion laws) | Classifier + escalation to crisis resources; annual reporting data | Trust & Safety | Protocol doc + test logs | |

## 3. Frameworks for structure (voluntary)
NIST AI RMF (Govern, Map, Measure, Manage, plus the Generative AI Profile), ISO/IEC 42001 (a certifiable AI management system), and the OWASP LLM and Agentic Top 10s as security checklists. Map each control once and reuse the evidence across frameworks.

## 4. Review cadence
Laws in this area change monthly. Put an **as-of date** on this sheet and schedule a re-check before each release and at least quarterly.
