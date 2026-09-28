"""Deliberately simple, non-LLM baseline for P01: keyword retrieval, the §7 permission trim, extractive answers.

The interface a real system keeps (eval_harness.py only uses these):
    BaselineSystem(data_dir).answer(user_id, query, now) -> {"answer": str, "abstained": bool,
        "citations": [{"chunk_id", "doc_id", "version", "quote"}], "retrieved": [chunk_id, ...]}
    .delete_matter(matter_id), .erase_subject(name, matter_ids), .artefacts(text) for the deletion drill
    predict(item) wraps answer() for one {"user_id", "query", "now"} item.

Weak on purpose, so the harness has something to measure:
- entitlements are polled every POLL_S seconds; no wall-event push             -> AC-2 p50
- ingestion indexes the raw text layer; no hidden-text scan                     -> AC-8, AC-3
- chunks carry no breadcrumbs (matter, parties); OCR noise is left as it is     -> AC-6
- abstains only when keyword coverage is very low; always cites its top 2 hits   -> AC-7, AC-4
- delete_matter() drops the source only; erase_subject() does nothing           -> AC-11
Every permission decision still goes through permission_trim.py, which is why AC-1 holds.
"""
import hashlib
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path

from permission_trim import AnswerCache, Chunk, Entitlements, authorize, index_filter, matches_filter

POLL_S = 300          # entitlement snapshot refresh; equal to MAX_SNAPSHOT_AGE_S, so snapshots are never stale
ABSTAIN_BELOW = 0.35  # share of the query's keyword weight the best chunk must match before we answer
STOP = set("a an and are as at be by did do does for from how i in is it its me of on or our the this to was we "
           "were what when which who with".split())


def tokens(text):
    return [t for t in re.findall(r"\w+", text.lower()) if t not in STOP]


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class MockDMS:
    """The DMS's own ACL view: walls land here 2-10 minutes after the wall record; deletions are immediate."""

    def __init__(self, matters, users, walls, doc_matter):
        self.matters, self.users, self.doc_matter, self.deleted = matters, users, doc_matter, set()
        self.walls = defaultdict(list)
        for w in walls:
            self.walls[w["matter_id"]].append(w)

    def allowed(self, user_id, doc_ids, now):
        groups, out = set(self.users[user_id]["groups"]), set()
        for d in doc_ids:
            m = self.doc_matter.get(d)
            if m is None or d in self.deleted:
                continue
            if any(user_id in w["users"] and w["dms_applied_at"] <= now for w in self.walls[m]):
                continue
            if groups & set(self.matters[m]["allow_groups"]):
                out.add(d)
        return out


class BaselineSystem:
    name = "baseline"

    def __init__(self, data_dir="data"):
        d = Path(data_dir)
        self.matters = {m["matter_id"]: m for m in load_jsonl(d / "matters.jsonl")}
        self.users = {u["user_id"]: u for u in load_jsonl(d / "users.jsonl")}
        self.walls = load_jsonl(d / "walls.jsonl")
        self.chunks, self.text, self.postings, self.sources = {}, {}, defaultdict(set), {}
        for doc in load_jsonl(d / "documents.jsonl"):
            self.ingest(doc)
        self.dms = MockDMS(self.matters, self.users, self.walls, dict(self.sources))
        self.cache, self.corpus_version = AnswerCache(), "corpus-v1"

    def ingest(self, doc):
        m = self.matters[doc["matter_id"]]
        self.sources[doc["doc_id"]] = m["matter_id"]
        for i, para in enumerate(doc["paragraphs"]):
            cid = f"{doc['doc_id']}@v{doc['version']}#p{i}"
            self.chunks[cid] = Chunk(cid, doc["doc_id"], m["matter_id"], frozenset(m["allow_groups"]), m["ai_permitted"])
            self.text[cid] = para["text"]  # the raw text layer: hidden text included, OCR noise kept
            for t in set(tokens(para["text"])):
                self.postings[t].add(cid)

    def entitlements(self, user_id, now):
        synced = now - now % POLL_S  # last poll of the walls system and the IdP
        screened = frozenset(w["matter_id"] for w in self.walls if user_id in w["users"] and w["recorded_at"] <= synced)
        groups = frozenset(self.users[user_id]["groups"])
        version = int(hashlib.sha256(repr((sorted(groups), sorted(screened))).encode()).hexdigest()[:12], 16)
        return Entitlements(user_id, groups, screened, version, synced)

    def search(self, query, flt, k=20):
        """Keyword (IDF) scoring. The permission filter is applied BEFORE top-k, never after."""
        n, scores, weight = len(self.chunks), defaultdict(float), 0.0
        for t in sorted(set(tokens(query))):
            post = self.postings.get(t)
            if not post or len(post) > 0.3 * n:
                continue
            idf = math.log(n / len(post))
            weight += idf
            for cid in post:
                scores[cid] += idf
        hits = sorted((c for c in scores if matches_filter(self.chunks[c], flt)), key=lambda c: (-scores[c], c))[:k]
        return [(c, scores[c] / weight) for c in hits]

    def answer(self, user_id, query, now=None):
        now = time.time() if now is None else now
        ent = self.entitlements(user_id, now)
        live = lambda uid, ids: self.dms.allowed(uid, ids, now)
        key = self.cache.key(ent, query, self.corpus_version)
        hit = self.cache.get(key, ent, live, now=now)
        if hit is not None:
            return hit
        ranked = self.search(query, index_filter(ent))
        score = dict(ranked)
        kept = authorize([self.chunks[c] for c, _ in ranked], ent, live, now=now)
        out = self.generate(query, [(c, score[c.chunk_id]) for c in kept])
        out["retrieved"] = [c.chunk_id for c in kept]
        self.cache.put(key, out, [self.chunks[c["chunk_id"]] for c in out["citations"]])
        return out

    def generate(self, query, scored):
        """Extractive: the best-matching sentence of each of the top 2 chunks. Replace this with a model."""
        if not scored or scored[0][1] < ABSTAIN_BELOW:
            return self.abstain()
        q, cites = set(tokens(query)), []
        for chunk, _ in scored[:2]:
            sentences = re.split(r"(?<=[.!?।])\s+", self.text[chunk.chunk_id])
            cites.append(self.cite(chunk.chunk_id, max(sentences, key=lambda s: len(q & set(tokens(s))))))
        return {"answer": " ".join(c["quote"] for c in cites), "abstained": False, "citations": cites}

    def abstain(self):
        return {"answer": "No supported answer in the documents you can access.", "abstained": True, "citations": []}

    def cite(self, chunk_id, quote):
        c = self.chunks[chunk_id]
        return {"chunk_id": chunk_id, "doc_id": c.doc_id, "version": int(chunk_id.split("@v")[1].split("#")[0]), "quote": quote}

    def delete_matter(self, matter_id):
        """BUG ON PURPOSE (brief §15): removes the source documents only; chunks, postings and cached answers stay."""
        for doc_id, m in list(self.sources.items()):
            if m == matter_id:
                del self.sources[doc_id]
                self.dms.deleted.add(doc_id)

    def erase_subject(self, name, matter_ids):
        """Not implemented. Students build the subject index (curveball 2) and purge every derived copy."""
        return None

    def artefacts(self, needle):
        """Verification sweep: every stored artefact whose text contains `needle`, with the matter it came from."""
        n = needle.lower()
        found = [{"store": "index", "id": c, "matter_id": self.chunks[c].matter_id}
                 for c, t in self.text.items() if n in t.lower()]
        for key, (out, cited) in self.cache.entries():
            if n in out["answer"].lower():
                found += [{"store": "answer_cache", "id": key, "matter_id": c.matter_id} for c in cited]
        return found


_default = None


def predict(item, data_dir=Path(__file__).resolve().parent / "data"):
    """One {"user_id", "query", "now" (optional)} item -> the answer dict."""
    global _default
    if _default is None:
        _default = BaselineSystem(data_dir)
    return _default.answer(item["user_id"], item["query"], item.get("now"))
