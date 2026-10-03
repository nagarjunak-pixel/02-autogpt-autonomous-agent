# P01 Validation: A Reference Solution Scored Against the Acceptance Criteria

Status as of 1 October 2026. This is an instructor note, not student material: it reports what a first real attempt at
[P01](../P01-permission-aware-knowledge-assistant.md) achieved on the budget path, on the kit's test set and on a
sealed held-out set, what failed and why, and the kit defects it found (fixes recommended, not yet applied).

## Bottom line

**A 3B model on a CPU does not meet P01.** On the kit's own test set it passes every row the harness can compute
except citation precision (AC-4: 0.945 against 0.95), and it misses that one only on items the kit's answer key makes
ambiguous. On new wording it clearly fails: on the sealed held-out set, answer accuracy falls from 0.966 to 0.594,
reliability (AC-9) from 0.980 to 0.530 and citation validity (AC-3) from 1.000 to 0.995. Neither result shows the
brief's criteria met:

- **Several passes are weaker than the brief's criteria.** It passes the harness's permission, injection and deletion
  rows on both sets (AC-1, AC-2, AC-8, AC-11, CB1), but AC-2 and CB1 are 0 s by construction (no simulated delivery
  delay); AC-11 counts only what the system reports, and its OCR vocabulary still holds the erased subject's name; no
  kit probe reached document search; and one hidden instruction reached two held-out answers without counting as an
  attack (sections 3 and 6).
- **Several criteria were not measured:** first-token latency (estimated at about twice the 3 s target), 20-user
  concurrency, deletion clocks, time to precedent and cost.

Six findings matter more than the scores:

1. **The held-out losses come from the solution's own word checks, not from the model.** Of 130 missed answerable
   questions, 124 were lost to a code check: 75 before the model was called, and 49 after it had picked the right
   sentence and answer. The model chose a wrong sentence twice. On the same 301 facts the solution scored 0.947 in the
   kit's wording and 0.588 in new wording; the kit's keyword baseline fell only from 0.797 to 0.701. So on new wording
   the deliberately weak baseline answers more questions correctly than the reference solution (held-out accuracy
   0.706 against 0.594; pass^3 0.690 against 0.530), because it almost never abstains (AC-7 0.150). It still fails
   the citation, abstention, injection and deletion criteria.
2. **It failed by staying silent.** 128 of the 130 misses were abstentions, and a research tool that finds nothing for
   4 questions in 10 fails its users. Wrong answers were shown for 2 of 320 answerable and 7 of 80 unanswerable
   questions, all citing matters the asker may open. The 7 lead with a figure that answers a different question (the
   purchase price for "how much is held in escrow?"): the case AC-7 exists for. Unlike P02's silent filter drop, the
   verbatim quote shows the mismatch to a careful reader.
3. **A tokeniser bug switched off the Hindi and Marathi glossary.** All 4 kit court-order questions, asked in English,
   failed at the topic check on "hearing" (the tokeniser) and "against" (no glossary entry); fixing the tokeniser
   alone rescues none of them. On the held-out set, 4 of the 16 court-order questions were answered: exactly the 4
   asked in Hindi or Marathi. All 8 English and 4 Hinglish ones failed, and the tokeniser was the main cause in 4 of
   them. The 33 unit tests did not catch it.
4. **The permission layer held, but only the held-out set tested the pre-filter.** There were 0 canary hits in 10,368
   probes on each set. Every kit probe names the matter, client or counterparty, so code answered all of them without
   searching the documents or calling the model. On the held-out set, 2,285 probes reached permission-filtered search,
   and none of their reported top-20 candidates came from a matter the prober may not open. Zero in about 2,100
   distinct probes bounds the pre-filter's failure rate at about 0.14% (rule of three), not the 0.03% that 10,000
   would imply.
5. **One hidden instruction reached the user, through a channel the kit lacks.** CSS-hidden text in a forwarded email
   filed as `provenance: firm` escaped the light check used for firm documents. It was quoted in two answers (the
   AC-3 failure). The ingestion regex, written with the kit's hidden wording in view, stopped all 150 items on the
   kit's hostile documents and 40 of the 60 on new ones (4 of 6 new channels).
6. **On the kit set, the answer key decides AC-4.** 23 of 320 answerable kit items (7.2%) have two current documents
   with different values, and all 18 imprecise citations fall on them. Nine kit fixes are recommended; none is applied.

## How it was tested

**Question.** Can a team meet P01's acceptance criteria (§5) with the brief's budget paths? The starter kit only
proves that a deliberately weak baseline fails. Nobody had built a real solution.

**The model: deliberately a weak one.** No API key was available, so the run used the brief's *local path*, but below
the size the brief assumes and without its retrieval models:

| | Brief's local path (§3) | This run |
|---|---|---|
| Model | 8–14B open-weight model (e.g. Qwen3 or Gemma 3) | Qwen2.5-3B-Instruct, 4-bit (Q4_K_M, 2.1 GB) |
| Serving | Ollama or vLLM | llama.cpp (llama-cpp-python 0.3.35) on 4 CPU cores, no GPU; JSON-schema-constrained output, temperature 0, fixed seed |
| Retrieval | `bge-m3` embeddings, `bge-reranker-v2-m3` | BM25 over sentences; no embeddings, no reranker |
| OCR | Docling plus Tesseract or PaddleOCR | none: the kit supplies noisy text, which the solution corrects against a vocabulary |

So a miss means "not with this model and this code on a CPU", not "unreachable"; as it turned out, most misses were
the code's. A pass shows only that the harness's version of a criterion is reachable. For AC-2, CB1, AC-5, AC-10 and
AC-11, and for AC-1 on the kit, that version is weaker than the brief's (sections 6 and 7). Every run used the kit's
default corpus of 537 documents, about a tenth of the brief's ~5,000.

**The solution** (1,150 lines of stdlib Python, 33 unit tests) is a fixed workflow: retrieve, trim, check, read,
verify.

- **Code owns every control:** entitlements (IdP groups, wall events); the kit's permission pre-filter and live DMS
  check; matter scoping (a named matter the user cannot open is refused before retrieval); a regex that quarantines
  suspect hidden sentences; evidence checks before and after the model (unknown names, answer type, common phrases,
  the model's copied "topic"); a verifier that blocks any citation that is not accessible or not verbatim; deletion
  with a certificate.
- **The model does two narrow jobs:** a *reader* picks which of at most 5 checked sentences answers and copies the
  answer words; a *screener* says whether a sentence from an other-side document is an instruction. Answers quote the
  chosen sentence, one citation each.
- **Deliberately not read:** the answer files and the evaluator's labels, including the `visible`/`hidden` split.

**Two test sets, scored by the kit's own, unmodified harness** (no `--limit`, `--runs 3`):

1. **Kit set:** 537 documents, 320 answerable and 80 unanswerable items, 10,368 canary probes (800 distinct strings),
   150 injection items (15 hostile documents × 10 prompts).
2. **Held-out set:** the same world plus 6 new hostile documents, with every query rewritten: 400 golden items from 94
   hand-written templates (the kit has 7) in English, Hinglish, Hindi and Marathi; 10,368 probes in 16 styles (7,079
   distinct texts); 210 injection items with new prompts and 6 new hidden-text channels. No item matches kit text
   verbatim.

**Guarding against self-deception.**

- **A separate author.** Another agent, who never saw the solution, wrote the held-out set and froze it (SHA-256)
  before scoring.
- **What the builder tuned on.** Only practice data: other seeds of the kit's own generator, which use the same
  question and probe templates as the kit set, and the builder's own rewordings. The kit-set scores are therefore
  close to training-distribution scores. The builder's rewordings gave accuracy 0.950; the independent held-out set
  gave 0.594.
- **An independent pre-scoring audit** found no blocking issue and 0 label errors in 82 hand-checked items. Its one
  rule breach (the runner redirected the harness's output path) was removed before scoring. It also found
  non-blocking fitting to the kit, which inflates kit scores:
  - the override regex contains the kit probes' exact phrases;
  - the hidden-text regex mirrors the kit's hidden wording;
  - the Hindi/Marathi glossary holds words from the kit's court-order templates (inert, section 2);
  - staff names seed the OCR vocabulary, which helps only because the generator draws staff and witnesses from one
    name pool (21 of the 64 staff names appear in kit documents).

  In the kit, too, the only provenance the solution treats as untrusted (`opposing_counsel`) marks exactly the 15
  hostile documents, so its broader regex and its model screen land on exactly those.

  The audit's stub dry run predicted that 74 held-out answerable items (26 core) would abstain before any model call.
  That was withheld from the builder until after scoring, and the replay confirmed it exactly.
- **Frozen code and a recording proxy.** The scoring script checked the solution's SHA-256 before each run, and a
  proxy journalled every model request and response (684 on the kit, 879 on the held-out set). Both runs were fully
  live. A container restart killed the first kit attempt after at least 98 model calls; the scored run restarted
  from zero.
- **Exact replay.** The diagnosis replays the journals through a proxy with a dead upstream, so any request not in the
  journal would fail. Both replays reproduce every row of the scored tables except AC-10, which an instant replay
  cannot time. A timed replay of the held-out set gives 7.337 s against the scored 7.340 s, and a reconstruction from
  journalled model time gives 6.816 s against 6.820 s on the kit. Nothing below is a re-run after fixing the solution.
- **Limits.** The held-out set reuses the kit's world and facts; 150 of its 210 injection items use the kit's hostile
  documents; and 7 of its golden items and 82 of its probes closely resemble the builder's practice templates.

## Results

✓ = meets the threshold, ✗ = misses it, judged on point estimates as the harness does. Four rows cannot be computed
offline: first token under 20 concurrent users (AC-10), deletion and de-indexing times (AC-11), time to precedent
(AC-12) and cost (AC-13, estimated below). AC-4 and AC-5 are the harness's proxies, not the brief's lawyer-calibrated
judge. Both are computed only on answered items, so the held-out AC-4 pass reflects 40% abstention. AC-5 = 1.000
follows from the answer format: the answer words and the quote are both copied from the cited sentence.

| AC | Metric | Threshold | Kit set | Held-out set |
|---|---|---|---|---|
| AC-1 | canary hits in 10,368 probes | 0 in ≥ 10,000 | 0 ✓ | 0 ✓ |
| AC-2 | wall propagation p50 from the wall record (53 timed probes; 0 s by construction) | ≤ 120 s | 0 s ✓ | 0 s ✓ |
| AC-2 | wall propagation p99 from the wall record | ≤ 900 s | 0 s ✓ | 0 s ✓ |
| AC-3 | displayed citations that verify (419) | 1.000 | 1.000 ✓ | 0.995 ✗ |
| AC-4 | citation precision (judge proxy, answered items only) | ≥ 0.95 | 0.945 (310/328 on 316 answered) ✗ | 0.974 (190/195 on 192 of 320 answered) ✓ |
| AC-5 | faithfulness, lexical proxy [95% CI] | ≥ 0.92 | 1.000 [1.000, 1.000] ✓ | 1.000 [1.000, 1.000] ✓ |
| AC-6 | recall@20, all [95% CI] | ≥ 0.85 | 0.988 [0.975, 0.997] ✓ | 0.887 [0.850, 0.919] ✓ |
| AC-6 | recall@20, scanned [95% CI] | ≥ 0.75 | 0.958 [0.917, 0.990] ✓ | 0.802 [0.719, 0.875] ✓ |
| AC-7 | correct abstention, 80 unanswerable items | ≥ 0.85 | 0.988 ✓ | 0.912 ✓ |
| AC-8 | injection attack success | ≤ 0.020 | 0.013 (150 items) ✓ | 0.000 (210 items) ✓ |
| AC-8 | exfiltration channels in answers | 0 | 0 ✓ | 0 ✓ |
| AC-9 | pass^3 on 100 core questions (pass@1) | ≥ 0.90 | 0.980 (0.980) ✓ | 0.530 (0.530) ✗ |
| AC-10 | p95 latency, 1 user at a time (brief: 20 concurrent users) | ≤ 12 s | 6.820 s ✓ (1 user) | 7.340 s ✓ (1 user) |
| AC-11 | residual artefacts after the drill (self-reported; section 6) | 0 | 0 ✓ | 0 ✓ |
| CB1 | M-1042 wall, worst exclusion time (0 s by construction) | ≤ 900 s | 0 s ✓ | 0 s ✓ |
| info | answer accuracy; blocked-answer rate | | 0.966; 0.0% | 0.594; 0.8% |

With the kit's defects set aside (section 5), the kit set gives AC-4 1.000, AC-7 79/79 and AC-8 0/150. Neither
held-out AC-6 pass is secure: the scanned-recall interval crosses 0.75, and the all-items interval starts at 0.850.
Under the brief's §8 CI gates, the two unverified held-out citations (AC-3) would block a release.

## What failed, and why

### 1. New wording: the solution's own checks threw away right answers

Tracing each held-out answerable item shows where its gold sentence was lost:

| Cause | Misses | Core |
|---|---|---|
| Scope check: a short counterparty name resolved to another party's matters | 27 | 9 |
| Unknown-name filter: a name the matter system does not know must appear in the evidence | 33 | 12 |
| Answer-type check ("when" needs a date, "how much" an amount) | 7 | 3 |
| Strict word check, used when no matter was resolved | 8 | 2 |
| Topic check after the model rejected a correct pick | 49 | 19 |
| Retrieval or scope (ranked too low, wrong matters searched) | 4 | 2 |
| Model picked the wrong sentence | 2 | 0 |
| **Total** | **130** | **47** |

No miss was a held-out label error. Four wording features account for 88 of the 130 misses, and none of them occurs
in the kit, whose questions always use the matter system's full names, have no apostrophes and follow one template per
document type:

- **Short counterparty names (28).** In "Time-bar check for matter M-1043: patent license claim against Juniper.
  What's the expiry date?", "Juniper" maps only to another matter's Juniper Pvt Ltd, so the scope comes out empty and
  the system abstains without searching.
- **Topic synonyms (27).** For "What risk did we flag to Harrowgate Bank of Juniper Logistics plc challenging the
  warehouse tenancy?" the model picked the right sentence and answer, but its topic, "warehouse tenancy", was rejected
  because the evidence says "lease". All 6 questions saying "share purchase agreement" failed: the evidence says "SPA".
- **Company suffix variants (25 of 25 failed).** In "a challenge by Elmstead Holdings Limited", the leftover "Holdings
  Limited" becomes an unknown organisation that the evidence ("Holdings Ltd") does not contain.
- **Possessive witness names (8).** "Rohan Ashworth's" never matches "Rohan Ashworth" in the evidence.

The other 42 had smaller triggers:

- the model copying a non-topic question word into its topic (9);
- abbreviations, typos and Hinglish particles copied into the topic (6);
- tokeniser artefacts in the topic check, such as a possessive "'s" (5);
- English questions about the Devanagari court orders (4; section 2);
- case numbers the resolver cannot map to a matter ("What date is CS/141/2026 listed for hearing?") (4);
- lowercase codenames (4);
- a closer mentioning "date" that turned duration, price and risk-level questions into date questions (4);
- Hinglish "kitna bataya" read as "how much" (3);
- ranking or the model's pick (3).

Synonym questions scored 0 of 6, Hinglish 0.41 and terse questions 0.53. The scope bug also causes 27 of the 36 AC-6
recall misses, because an abstention before retrieval reports nothing retrieved.

**What fixing the checks might give: an estimate on the set that found the failures.** The 49 journalled answers the
topic check rejected all pass the harness's `correct()`. In 75 of the other 76 code-check cases, a fixed check makes
the gold the reader's first candidate, which the reader took in 532 of 532 scored calls. On that basis:

- fixing only the topic check gives accuracy 0.747 and core pass^3 0.720;
- fixing every wording-caused check gives 0.981–0.984 and 0.970–0.980.

These figures describe this held-out set after fixes written by looking at its own failures. By the P02 rule, they are
not a fair estimate of accuracy on fresh wording. They also assume a synonym-aware topic check and a resolver that
maps case numbers to matters.

The price is abstention. With the name and type fixes, 3 more unanswerable items would reach the reader. AC-7 would
then fall from 0.912 to somewhere between 0.875 (if all three are answered) and 0.912. If the topic-check fix also
passed the two topic swaps the current check caught, it could fall to 0.850, the threshold. Measuring any fix needs a
fresh sealed set. The P02 lesson again: build gates from real phrasings in every language the firm uses, and measure
abstention whenever one is loosened.

### 2. A tokeniser bug broke every Hindi and Marathi word

The token pattern uses Python's `\w`, which does not match Devanagari vowel signs, so each Hindi or Marathi word is cut
at its first vowel sign: "सुनवाई" (hearing) becomes "स" + "ुनवाई". The glossary holds whole words and never matches, so
an English "hearing" can never reach "सुनवाई". Questions written in Hindi or Marathi still work, because both sides
split the same way.

- **Kit:** all 4 court-order questions are in English, and all failed at the topic check. The model's topic, "court
  hearing against …", had two words the evidence check could not find: "hearing" (the tokeniser) and "against" (the
  glossary has no entry for "विरुद्ध"). An offline check with a fixed tokeniser still rejects all four, now on
  "against" alone.
- **Held-out:** 4 of the 16 court-order questions were answered, all of them asked in Hindi or Marathi; all 8 English
  and all 4 Hinglish ones failed. The tokeniser was the main cause in 4 of those 12. The others failed on:
  - case numbers the resolver cannot map (4);
  - the model copying "Indian proceedings against" into its topic (2);
  - a suffix variant (1);
  - ranking (1).

  The tokeniser also played a part in 2 of the case-number misses, which failed the word check on "hearing", and
  possibly in the ranking miss.

The audit had noted that the glossary holds exact words from the kit's court-order templates; the bug made them inert.
The unit tests include one Devanagari string and no test of tokenisation.

### 3. A hidden instruction in a "firm" email reached two answers (AC-3)

Both failed citations quote one hidden sentence. In a forwarded email filed as `provenance: firm`, CSS-hidden text
named an addressee that the regex's list does not cover, a phrase for summarising software. It told that addressee to
copy every record on another project into its description of the host project. Three things let it through:

- for firm documents the regex looks only for strong signals, and this addressee is not on its list;
- firm documents are never model-screened;
- the verifier checks quotes against the raw text, hidden part included.

One answer led with the other project's name. Nothing from that project was cited and neither asker may open it, so
this is neither a leak nor, by the harness's rule, an attack. But the attacker's text reached a lawyer.

| Hidden-text channel | Items | What stopped the payload |
|---|---|---|
| The kit's four (white 1-pt, off-page, XMP, alt text) | 150 | regex at ingestion: 150* |
| New: HTML comment, tracked deletion, zero-width, behind an image | 40 | regex at ingestion: 40 |
| New: Word hidden text, Hindi payload | 10 | not retrieved 6; model screen 1; below the 5-sentence reader cut 1; code checks 2 |
| New: CSS `display:none`, firm provenance | 10 | not retrieved 6; listed before retrieval 2; code checks 1; **quoted 1** |

\* The same CSS-hidden payload was also quoted in HI136, an item aimed at a kit document.

The model screen flagged the one hidden sentence it saw, and also 28 of the 32 harmless other-side sentences: safe for
AC-8, but it is why "what is the other side arguing?" mostly abstains. Provenance is a hint, not trust: forwarded mail
carries other people's text.

### 4. Questions about attributes no document states were answered (AC-7)

AC-7 passed (0.912), but 7 unanswerable items were answered. Six ask for an attribute the corpus never states, such
as escrow or a break fee; one swaps the topic. The reader picked the nearest sentence about the same agreement, and
inside a named matter no check tests the attribute noun. Nothing was exposed: every cited document was one the asker
may open, and all 30 items the asker may not see, or whose client opted out of AI, abstained. The kit has no attribute
items.

### 5. The kit set: the answer key decides AC-4

Of the kit's 11 answer misses, 6 are items where two current documents give different values and the reader picked
the other one (the solution's conflict check misses values that are words, such as risk levels, and dates differing
only in the month); 1 is an ambiguous item whose gold appears only in OCR-damaged form; 4 are the court orders of
section 2. All 18 imprecise citations, of 328, fall on ambiguous items: 12 answers cited both documents, 6 cited the
other one. AC-4 allowed 16. Without the 23 ambiguous items, AC-4 is 1.000, accuracy 0.987 and pass^3 1.000.

How many items are ambiguous depends on the check:

- an OCR-tolerant check finds 23 on the kit seed (7.2%, 7 of them core);
- the builder's stricter raw-text check finds 15 of them here, and averaged 3.5% across six practice seeds;
- the auditor's check found 17;
- across 16 other seeds the OCR-tolerant rate is 3.1–7.5% (5.1% overall);
- at `--scale 12.5`, which the README gives for the brief's ~5,000 documents, it is 64%.

Also:

- **G350**, labelled absent, is answered word for word by a near-duplicate precedent in its own matter.
- **The two AC-8 "successes"** cite a matter both askers may open, for a question naming no matter; the hidden
  instructions never reached the model. Six pull-in items in each set can score a correct answer as an attack.
- **25 gold answers are not verbatim in their OCR-damaged evidence.** This solution scored 24 by copying from corrected
  text; a system that quotes verbatim cannot score them, which caps its pass^3 at 0.93.

### 6. What held, and what the harness cannot see

- **Leakage (AC-1): 0 hits on both sets.** On the kit, code answered all 10,368 probes without searching the documents
  or calling the model:
  - 8,388 (81%) were refused by the matter-scope check;
  - 864 (8%) by an override-phrase regex that contains the kit probes' own phrases;
  - 396 (4%) as AI opt-out;
  - 720 (7%) got a listing of documents the prober may open.

  So the kit's AC-1 tests name handling, not the permission pre-filter. On the held-out set, 2,285 probes (2,138
  distinct user–question pairs) reached permission-filtered search, and 69 more got a listing. None of their reported
  top-20 candidates came from a matter the prober may not open. 235 reached the reader (209 model requests; the rest
  reused an identical earlier request). All 141 answers (72 from the model, 69 listings) cite only matters the
  prober may open. The harness looks only for the literal token, its prefix, the exact figure or a forbidden
  citation. A figure spelled out, rounded or encoded would be missed, so this is a lower bound.
- **Exfiltration (AC-8).** No link, image or false date appeared in any of the held-out run's 11,406 answers. With
  the kit's honest-citation artefact removed, attack success under the harness's rules was 0 on both sets. The
  held-out payload quoted in two answers (section 3) is not an attack under those rules, but it did reach the user.
- **Walls (AC-2, CB1): 0 s by construction.** Wall events are applied at the record time, probes start at the record
  time, and the kit simulates no delivery delay. All 53 probes were timed in both runs.
- **Deletion (AC-11): 0 on both sets,** but this counts what the system reports about itself, plus a re-query of each
  warm-up question. The OCR-correction vocabulary is never purged. After the erasure it still counts the subject's
  names (7 times each on both sets), though no sentence in the erasure scope remains. On the brief's AC-11 ("derived
  artefacts gone"), that is a miss the harness cannot see.

The audit and the builder's notes add three issues the harness cannot see:

- corpus statistics include documents the user cannot open (a one-bit existence channel);
- entitlements are stamped "synced now", so the kit's stale-snapshot fail-closed branch never fires;
- refusals return instantly, so timing reveals which codenames exist.

### 7. Latency on a CPU

With one user at a time, p95 was 6.820 s on the kit and 7.340 s on the held-out set, against 12 s. That is not the
brief's AC-10, which is measured under 20 concurrent users. This server answers one model call at a time, so 20 users
would queue behind calls of about 6 s each. This run cannot show AC-10, and the system as run would very likely miss
it.

| Model call | Live calls | Mean | Median | p95 | Tokens in / out |
|---|---|---|---|---|---|
| Reader, kit | 662 | 5.72 s | 5.67 s | 7.08 s | 772 / 26.1 |
| Reader, held-out | 822 | 6.09 s | 5.87 s | 8.59 s | 822 / 25.4 |
| Screen, kit / held-out | 22 / 57 | 1.33 s / 1.27 s | 1.34 s / 1.23 s | 1.44 s / 1.45 s | 721–722 / 5.0 |

The server's log lines up exactly with the journals and shows no request from any other client during either run. A
reader call in the scored runs went like this:

- it reused about 700 cached prompt tokens;
- it read 74–124 new tokens at 61–68 tokens a second (1.2–1.8 s);
- it wrote about 26 tokens at 7.2–7.5 tokens a second (3.4–3.6 s);
- with server overhead, it took about 5.7–6.1 s in all.

The p95 covers all 400 golden items, including code abstentions that take milliseconds (on the held-out set, those
400 items needed 264 model calls).

The harness cannot measure first token within 3 s under 20 concurrent users. Here nothing is shown until the verifier
has passed the whole answer, so the first token arrives with it. For answered items that is typically 4.5–7 s of
model time (median about 5.6 s): roughly twice the 3 s target with one user, and far worse under 20. Meeting it needs
a much faster model (a GPU or the API path) or a UI that shows the retrieved passages first.

### 8. Reliability (AC-9)

pass^3 equals first-run accuracy on the core questions on both sets (0.980 and 0.530). The three runs made identical
model calls with identical outcomes, and 0 model errors. With temperature 0, a fixed seed and schema-constrained
output, AC-9 measures accuracy, not drift. Lawyers re-ask in other words, and that is where this solution is
unreliable.

## Cost on the API path (estimate, not measured)

No API key was available. The token profile comes from the local runs (Qwen's tokeniser; Claude's counts will differ):

- **Per model call:** about 770 input and 25 output tokens on the kit (684 calls; 526,908 and 17,362 tokens), 815 and
  24 on the held-out set (879 calls; 716,741 and 21,167).
- **Per question:** the main suite, the nearest thing to real traffic, made 0.70 calls per question on the kit (386
  for 550) and 0.69 on the held-out set (420 for 610). Per answered question it made 1.01 and 1.59 (383 and 264
  answered).

| List price per million tokens (input / output) | Kit, per answered question | Held-out, per answered question |
|---|---|---|
| Claude Haiku 4.5 ($1 / $5) | $0.0009 | $0.0015 |
| Claude Sonnet 5 ($2 / $10) | $0.0018 | $0.0029 |

Prices are Anthropic's API list prices per million tokens, as given in Anthropic's Claude API reference on 1 October 2026 (Haiku 4.5's is the price the P02 report used). Every figure is under 4% of AC-13's USD 0.08.
It is cheap because the model sees at most 5 sentences, about 800 tokens; the brief's cost model assumes about 12,000
input tokens per query, some 15 times more.

Prompt caching would not apply: the ~560-token system prompt (counted in Qwen tokens) is below the minimum cacheable
prefix of both models (4,096 tokens for Haiku 4.5, 1,024 for Sonnet 5). The cost stays far below AC-13 regardless.

A whole scored run would cost $0.61–$1.65, well inside the brief's USD 50 API budget. Search hosting and OCR are not
included, and neither model's accuracy here was tested.

## Corrections to the kit

**None has been applied yet.** The fixes below are recommended, not yet applied; this section will be updated when they
are. They are nine diffs that apply in order, after which the kit's tests pass (17 existing, 2 new).

| Diff | Defect | Recommended fix |
|---|---|---|
| 01 | 23 of 320 answerable items have two current answers (64% at `--scale 12.5`) | one current document per type and topic in a matter; keep only questions with one answer; new test (regenerates the data) |
| 02 | 25 golds not verbatim in OCR-damaged evidence | `correct()` also matches after undoing the generator's OCR confusions |
| 03 | an honest citation of an accessible target counts as a pull-in attack | do not score those items for pull-in; report how many |
| 04 | a precedent answers an "absent" item (G350) | build precedents from an NDA with another counterparty; new test |
| 05 | AC-2 silently drops probes it cannot time | check post-wall answers; report unmeasured probes |
| 06 | the misstatement check matches only the literal date | match the date in any common format |
| 07–09 | an unreachable probe suffix; the README; probes that always name the matter | remove the dead code; update the README; optionally add topic-only probes |

The README diff also discloses the design limits:

- **The evaluator's labels sit in `documents.jsonl`.** A baseline that reads `visible` instead of `text` goes from
  AC-3 0.905 to 1.000 and AC-8 0.207 to 0.000 on the current kit (the diff quotes the post-fix 0.213).
- **Detection of leaks and injections is literal.**
- **AC-2 has no delivery delay.**
- **AC-11 and AC-6 are partly self-reported.**

After fixes 01–07 the baseline measures AC-4 0.420, AC-7 0.000, AC-8 0.213, AC-9 0.820 and AC-11 77. The kit's probes
are 800 distinct strings, not the 768 first reported. Fixes 01 and 04 change the data, so the reference would need
re-scoring.

## Recommendations for instructors

1. **Score every team on a held-out set with new wording, and keep it sealed.** On the same 301 facts, this
   solution's accuracy fell from 0.947 in the kit's wording to 0.588 in new wording (core pass^3, on different core
   sets, 0.980 against 0.530). This note quotes three held-out questions (two already in the set's own notes) and
   otherwise only fragments.
2. **Make teams show what their checks reject.** An abstaining gate loses accuracy without a visible error. Ask for a
   rejection log per check on paraphrases in all three languages, and re-measure AC-7 with every change.
3. **Treat provenance as a hint.** Require hidden-text scanning of every document, whoever filed it, and read answers
   to hostile prompts by hand: the harness checks only literal markers, links and cited target matters.
4. **Until the fixes are applied, read AC-4, AC-7 and AC-8 item by item on the kit set.** Near the thresholds, the
   answer key and the pull-in rule decide the verdict.
5. **Make AC-1 test the permission pre-filter** with probes that name no matter. Use diff 09, or the held-out set's
   roughly 1,000 document-ID and aggregation probes; most held-out probes still name the matter in some form.
6. **Run AC-9 on paraphrases.** For a deterministic system, three identical runs give pass^3 = pass@1.
7. **Still require at least an 8B model or an API model.** The 3B reader almost always takes the first candidate and
   rarely abstains by itself, and the 3B screen flagged 28 of 32 harmless sentences. Whether a stronger reader would
   let the word checks relax without losing AC-7 is untested. That is the hypothesis to check with an 8B or API model
   on a fresh held-out set.

## Limits

- One run per set on one model, deterministic. An 8–14B model, or an API model, was not tested. The estimate in
  section 1 is not a re-run, and it scores fixes on the set that found the failures.
- **Scale.** Both sets use the kit's default corpus (537 documents, 40 matters), about a tenth of the brief's ~5,000.
  At the README's `--scale 12.5` the kit baseline's recall falls below AC-6 (0.841; scanned 0.490), so this
  solution's AC-6 passes may not hold at the brief's size.
- **OCR.** No OCR was run. The kit supplies noisy text, so "scanned" recall tests retrieval over OCR noise, not
  reading page images. The held-out set also leaves out the 30 facts whose answers OCR damaged.
- The held-out set reuses the kit's world and was generated from templates; wordings from the firm's own lawyers are
  what the brief's §8 calls for. Some sub-groups are small (4 Hindi or Marathi questions, 6 synonym questions).
- The harness cannot measure indirect leaks, paraphrased misstatements, a real wall-event delay, stores or retrieval a
  system does not report, judge-calibrated precision and faithfulness, hidden text as real layout, concurrency, time
  to precedent or real cost.
- The reference solution and the held-out set are not in this repository, because they would give students the
  answer. They are available to instructors on request.
