"""KV-cache and decode-speed maths from brief §6, so the capacity table can be recomputed (curveball 1: budget halved).

    python3 kv_capacity.py        # prints the brief's five configurations and the half-budget options

All figures are paper estimates (±30%). Replace them with `vllm bench serve` replay results in week 5.
"""
from dataclasses import dataclass

GB = 1e9
DESIGN = {"concurrent": 40, "seq_tokens": 4500, "min_tok_s": 20.0}   # 2 req/s × ~20 s decode; ≥ 20 tok/s per stream


@dataclass(frozen=True)
class GPU:
    name: str
    mem_gb: float
    bw_gbs: float


@dataclass(frozen=True)
class Model:
    name: str
    weights_gb: float       # FP8 weights
    layers: int             # layers that keep a full KV cache
    kv_heads: int
    head_dim: int
    experts: int = 0        # MoE: total experts and experts per token
    top_k: int = 0
    dense_gb: float = 0.0   # MoE: attention, embeddings and shared weights, read every step


L40S, H100_NVL = GPU("L40S", 48, 864), GPU("H100 NVL", 94, 3900)
DENSE_32B = Model("dense 32B-class GQA", 33, 64, 8, 128)
SARVAM_30B = Model("Sarvam-30B-class MoE", 32, 19, 4, 64, experts=128, top_k=6, dense_gb=2)


def kv_bytes_per_token(layers: int, kv_heads: int, head_dim: int, bytes_per_value: int = 2) -> int:
    """2 (K and V) × layers × KV heads × head_dim × bytes. BF16 = 2 bytes, FP8 = 1."""
    return 2 * layers * kv_heads * head_dim * bytes_per_value


def usable_gb(gpu: GPU) -> float:
    return 0.9 * gpu.mem_gb - 4          # check the engine's startup report


def plan(gpu: GPU, model: Model, n_gpus: int, tp: int = 1, kv_bytes: int = 2, concurrent: int = DESIGN["concurrent"],
         seq_tokens: int = DESIGN["seq_tokens"], efficiency: float = 0.6, tp_penalty: float = 0.15) -> dict:
    """Sequences that fit in KV room, and decode tokens/s per stream with `concurrent` streams spread over replicas."""
    replicas = n_gpus // tp
    per_replica = concurrent / replicas
    kv_seq_gb = kv_bytes_per_token(model.layers, model.kv_heads, model.head_dim, kv_bytes) * seq_tokens / GB
    room = usable_gb(gpu) * tp - model.weights_gb
    fits = int(room / kv_seq_gb) if room > 0 else 0
    frac = 1 - (1 - model.top_k / model.experts) ** per_replica if model.experts else 1.0  # experts read per step
    weights_read = model.dense_gb + (model.weights_gb - model.dense_gb) * frac
    step_s = (weights_read + per_replica * kv_seq_gb) / tp / (gpu.bw_gbs * efficiency)
    tok_s = (1 / step_s) * ((1 - tp_penalty) if tp > 1 else 1)
    fit = fits >= per_replica
    verdict = "passes" if fit and tok_s >= DESIGN["min_tok_s"] else (
        "marginal" if fit and tok_s >= 0.9 * DESIGN["min_tok_s"] else "fails")
    return {"config": f"{n_gpus}x {gpu.name}, {model.name}" + (f", TP={tp}" if tp > 1 else f", {replicas} replica(s)"),
            "kv_room_gb": round(room, 1), "seqs_per_replica": fits, "streams_per_replica": per_replica,
            "tok_s_per_stream": round(tok_s, 1), "verdict": verdict}


def brief_table(kv_dense: int = 1) -> list[dict]:
    """The five rows of the brief's table: dense rows use FP8 KV, MoE rows BF16 KV."""
    return [plan(L40S, DENSE_32B, 4, kv_bytes=kv_dense), plan(L40S, DENSE_32B, 4, tp=2, kv_bytes=kv_dense),
            plan(H100_NVL, DENSE_32B, 2, kv_bytes=kv_dense), plan(L40S, SARVAM_30B, 4),
            plan(H100_NVL, SARVAM_30B, 2)]


def half_budget() -> list[dict]:
    """Curveball 1: one server per site becomes 2× L40S or 1× H100 NVL. No N+1 on the single-GPU options."""
    return [plan(L40S, DENSE_32B, 2, kv_bytes=1), plan(L40S, DENSE_32B, 2, tp=2, kv_bytes=1),
            plan(L40S, SARVAM_30B, 2), plan(H100_NVL, DENSE_32B, 1, kv_bytes=1), plan(H100_NVL, SARVAM_30B, 1)]


if __name__ == "__main__":
    for title, rows in (("Brief §6 table", brief_table()), ("Curveball 1: half budget", half_budget())):
        print(title)
        for r in rows:
            print(f"  {r['config']:48} KV room {r['kv_room_gb']:6.1f} GB  fits {r['seqs_per_replica']:4} seqs/replica"
                  f"  {r['tok_s_per_stream']:6.1f} tok/s/stream  {r['verdict']}")
