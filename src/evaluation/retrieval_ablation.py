"""
Eksperimen ablasi retrieval pada set uji v1 beku -- PENGUKURAN, bukan penyetelan.

Menguji parameter retrieval yang selama ini ditetapkan dari penalaran: top_k, strategi
agregasi skor per artikel, seksi yang ikut dicari, dan ketahanan terhadap klaim panjang.

Aturan:
  - TIDAK ada panggilan LLM/API. Yang diukur hanya lapisan retrieval.
  - TIDAK mengubah generator.py, prompt, testset/v1.jsonl, maupun indeks ChromaDB (indeks hanya
    dibaca; lihat CLAUDE.md soal ChromaDB yang menulis ulang berkas saat dibuka).
  - Hasil TIDAK dipakai untuk mengubah parameter produksi tanpa persetujuan pemilik proyek.
  - Kebenaran dasar: `expected_retrieval_article` pada 54 butir set uji beku.

Metode: untuk tiap klaim dihitung kemiripan kosinus EKSAK (brute-force) terhadap SELURUH chunk
tersimpan, lalu semua kondisi (agregasi, subset seksi, k) diturunkan dari skor yang sama. Karena
tiap chunk di-embed sendiri-sendiri, membuang seksi saat kueri setara dengan indeks tanpa seksi
itu -- tidak perlu membangun ulang indeks. Kesetiaan terhadap produksi diperiksa: top-3 agregasi
maksimum dibandingkan dengan `retriever.retrieve` (HNSW, 30 chunk) dan dengan top-3 yang tercatat
di hasil evaluasi v1.

Pemakaian (dari root proyek; memuat bge-m3 di CPU, tanpa jaringan API):
  PYTHONPATH=src python -m evaluation.retrieval_ablation
"""

import argparse
import ast
import json
import math
import random
import statistics
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.metrics import wilson_interval
from paths import DATA_DIR, PROJECT_ROOT

V1_PATH = PROJECT_ROOT / "testset" / "v1.jsonl"
EVAL_PATH = DATA_DIR / "testset_v1_eval_gemini-3.5-flash-lite.jsonl"
OUT_JSON = PROJECT_ROOT / "testset" / "retrieval_ablation.json"
OUT_REPORT = PROJECT_ROOT / "testset" / "retrieval_ablation_report.txt"

K_VALUES = (1, 3, 5, 10, 20)
PRODUCTION_K = 3
V1_RECALL_FAILURES = ("v1-022", "v1-024", "v1-027", "v1-033")

SECTION_CONDITIONS: dict[str, frozenset[str] | None] = {
    "seluruh_seksi": None,  # kondisi produksi
    "hanya_narasi": frozenset({"narasi"}),
    "hanya_kesimpulan": frozenset({"kesimpulan"}),
    "narasi_dan_kesimpulan": frozenset({"narasi", "kesimpulan"}),
}

LENGTH_TARGETS = (1500, 3000, 5000)
PLACEMENTS = ("kedua_sisi", "belakang")  # "belakang" = pembanding: klaim di awal pesan

# Teks pengganggu SINTETIS bergaya pesan berantai: sapaan, ajakan menyebarkan, tanda baca
# berlebihan. Sengaja netral topik agar yang diuji adalah pengenceran, bukan topik baru.
FILLER_SENTENCES = (
    "Assalamualaikum wr wb, selamat pagi bapak ibu sekalian 🙏🙏🙏",
    "Mohon maaf bila mengganggu waktunya, saya hanya meneruskan info dari grup sebelah!!!",
    "SEBARKAN SEBELUM DIHAPUS!!!",
    "Tolong share ke semua grup keluarga dan teman-teman ya, jangan berhenti di kamu.",
    "Copas dari grup alumni, semoga bermanfaat untuk kita semua.",
    "Info penting!!! Baca sampai habis ya...",
    "Jangan lupa bagikan ke minimal 10 grup, biar semua orang tahu.",
    "Aamiin ya rabbal alamin 🤲🤲",
    "Hati-hati ya semuanya, jaga keluarga masing-masing.",
    "Saya dapat dari saudara yang kerja di sana, katanya ini beneran.",
    "Kalau tidak percaya silakan cek sendiri, saya cuma mengingatkan...",
    "Salam sehat selalu untuk kita semua, tetap semangat!!!",
    "Forward dari grup RT, mohon diteruskan.",
    "Mumpung belum viral, kasih tahu orang tua dan tetangga ya.",
    "Terima kasih sudah membaca, semoga Allah membalas kebaikan kalian 🙏",
    "Wassalamualaikum wr wb.",
    "!!!!! PENTING !!!!!",
    "Maaf kalau sudah ada yang kirim, sekadar mengingatkan saja.",
)

# Ambang keputusan untuk "selisih bermakna": uji McNemar eksak (berpasangan, butir yang sama)
# DAN selisih bersih minimal 3 butir. Selisih 1-2 butir tidak pernah disimpulkan sebagai keunggulan.
ALPHA = 0.05
MIN_NET_DIFF = 3


# ---------------------------------------------------------------------------------------------
# Fungsi murni (diuji offline di tests/test_retrieval_ablation.py)
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ChunkScore:
    """Skor kemiripan satu chunk terhadap satu klaim."""

    article_id: str
    section: str
    score: float


def aggregate_max(scores: Sequence[float]) -> float:
    """Skor maksimum antar-chunk (strategi produksi, `retriever.aggregate_by_article`)."""
    return max(scores)


def aggregate_mean(scores: Sequence[float]) -> float:
    """Rata-rata skor seluruh chunk artikel."""
    return sum(scores) / len(scores)


def aggregate_mean_top2(scores: Sequence[float]) -> float:
    """Rata-rata dua skor tertinggi (satu skor bila artikel hanya punya satu chunk)."""
    top = sorted(scores, reverse=True)[:2]
    return sum(top) / len(top)


AGGREGATORS: dict[str, Callable[[Sequence[float]], float]] = {
    "maks": aggregate_max,
    "rata_rata": aggregate_mean,
    "rata_rata_dua_teratas": aggregate_mean_top2,
}


def rank_articles(
    chunks: Iterable[ChunkScore],
    aggregator: Callable[[Sequence[float]], float] = aggregate_max,
    sections: frozenset[str] | None = None,
) -> list[tuple[str, float]]:
    """
    Peringkat artikel dari skor chunk: (article_id, skor agregat), urut menurun.

    `sections` membatasi chunk yang ikut (None = semua seksi). Seri diurutkan berdasarkan
    article_id agar hasil deterministik.
    """
    by_article: dict[str, list[float]] = {}
    for c in chunks:
        if sections is None or c.section in sections:
            by_article.setdefault(c.article_id, []).append(c.score)
    ranked = [(aid, aggregator(s)) for aid, s in by_article.items()]
    return sorted(ranked, key=lambda x: (-x[1], x[0]))


def article_rank(ranking: Sequence[tuple[str, float]], article_id: str) -> int | None:
    """Peringkat (mulai 1) sebuah artikel dalam `ranking`; None bila tidak ada."""
    for i, (aid, _) in enumerate(ranking, start=1):
        if aid == article_id:
            return i
    return None


def hit_at_k(rank: int | None, k: int) -> bool:
    """Apakah artikel yang benar ada di top-k."""
    return rank is not None and rank <= k


def recall_summary(ranks: Sequence[int | None], k: int) -> dict[str, Any]:
    """Recall@k beserta interval Wilson 95%."""
    hits = sum(hit_at_k(r, k) for r in ranks)
    lo, hi = wilson_interval(hits, len(ranks))
    return {"benar": hits, "n": len(ranks), "proporsi": round(hits / len(ranks), 4) if ranks else None,
            "wilson95": [round(lo, 3), round(hi, 3)]}


def mcnemar_exact_p(gained: int, lost: int) -> float:
    """
    p dua sisi uji McNemar eksak (binomial pada pasangan sumbang, p=0,5).

    `gained` = butir yang berubah salah -> benar, `lost` = benar -> salah.
    """
    n = gained + lost
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(gained, lost) + 1)) / 2**n
    return min(1.0, 2 * tail)


def paired_comparison(base: Sequence[bool], other: Sequence[bool]) -> dict[str, Any]:
    """Bandingkan dua kondisi pada butir yang sama: berubah naik/turun, McNemar, dan kesimpulan."""
    gained = sum((not b) and o for b, o in zip(base, other))
    lost = sum(b and (not o) for b, o in zip(base, other))
    p = mcnemar_exact_p(gained, lost)
    net = gained - lost
    meaningful = p < ALPHA and abs(net) >= MIN_NET_DIFF
    return {
        "naik": gained, "turun": lost, "selisih_bersih": net, "p_mcnemar": round(p, 4),
        "kesimpulan": (
            "selisih bermakna" if meaningful else
            "tidak dapat dibedakan dari kebetulan" if net != 0 else "identik"
        ),
    }


def filler_text(length: int, rng: random.Random) -> str:
    """Teks pengganggu sintetis sepanjang tepat `length` karakter (dipotong di batas kata)."""
    if length <= 0:
        return ""
    parts: list[str] = []
    total = 0
    while total < length + 80:
        sentences = list(FILLER_SENTENCES)
        rng.shuffle(sentences)
        for s in sentences:
            parts.append(s)
            total += len(s) + 1
    text = " ".join(parts)[:length]
    cut = text.rfind(" ")
    text = text[:cut] if cut > length * 0.9 else text
    return text.ljust(length, "!")


def pad_claim(claim: str, target_chars: int, rng: random.Random,
              placement: str = "kedua_sisi") -> tuple[str, int]:
    """
    Sisipkan teks pengganggu hingga panjang total = `target_chars`.

    Mengembalikan (teks, offset karakter awal klaim). "kedua_sisi" membagi pengganggu kira-kira
    sama di depan dan belakang klaim; "belakang" menaruh semuanya setelah klaim (klaim di awal).
    Klaim tidak diubah. Bila klaim sudah >= target, dikembalikan apa adanya.
    """
    sep = "\n\n"
    if len(claim) >= target_chars:
        return claim, 0
    if placement == "belakang":
        tail = filler_text(target_chars - len(claim) - len(sep), rng)
        return claim + sep + tail, 0
    if placement != "kedua_sisi":
        raise ValueError(f"penempatan tidak dikenal: {placement}")
    budget = target_chars - len(claim) - 2 * len(sep)
    head = filler_text(budget // 2, rng)
    tail = filler_text(budget - len(head), rng)
    return head + sep + claim + sep + tail, len(head) + len(sep)


def claim_visibility(tokens_before: int, claim_tokens: int, max_tokens: int) -> str:
    """
    Seberapa banyak klaim yang masih terbaca model embedding setelah dipotong `max_tokens`.

    `tokens_before` dan `claim_tokens` tanpa token khusus; satu token pembuka ([CLS]/<s>) dihitung.
    """
    start = 1 + tokens_before
    end = start + claim_tokens
    if end <= max_tokens:
        return "utuh"
    if start >= max_tokens:
        return "terpotong_seluruhnya"
    return "sebagian"


def best_section_of(chunks: Iterable[ChunkScore], article_id: str) -> str | None:
    """Seksi asal chunk berskor tertinggi pada artikel tertentu."""
    own = [c for c in chunks if c.article_id == article_id]
    return max(own, key=lambda c: c.score).section if own else None


def group_items(items: Sequence[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Kelompok pelaporan: non-batas, batas, per tipe dan per subtipe (non-batas)."""
    groups: dict[str, list[dict[str, Any]]] = {
        "non_batas": [i for i in items if not i["batas"]],
        "batas": [i for i in items if i["batas"]],
    }
    for i in items:
        if i["batas"]:
            continue
        groups.setdefault(f"tipe:{i['tipe']}", []).append(i)
        if i.get("subtipe"):
            groups.setdefault(f"subtipe:{i['subtipe']}", []).append(i)
    return groups


def targeted_items(items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Butir yang punya artikel sasaran retrieval; hanya ini yang masuk hitungan recall."""
    return [i for i in items if i.get("expected_retrieval_article")]


def parse_recorded_top3(value: Any) -> list[str]:
    """article_id top-3 dari kolom `retrieval_top3` hasil evaluasi (list atau repr string)."""
    data = ast.literal_eval(value) if isinstance(value, str) else value
    return [str(d["article_id"]) for d in data]


# ---------------------------------------------------------------------------------------------
# Eksperimen (butuh model dan indeks; tanpa API)
# ---------------------------------------------------------------------------------------------

def load_items(path: Path = V1_PATH) -> list[dict[str, Any]]:
    """Butir set uji beku, urut id."""
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return sorted(rows, key=lambda r: r["id"])


def load_recorded_top3(path: Path = EVAL_PATH) -> dict[str, list[str]] | None:
    """Top-3 retrieval yang tercatat pada evaluasi v1 (run 1); None bila berkas tidak ada."""
    if not path.exists():
        return None
    out: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if str(r["run"]) == "1":
                out[r["id"]] = parse_recorded_top3(r["retrieval_top3"])
    return out


class ChunkMatrix:
    """Seluruh embedding chunk tersimpan (dibaca sekali) untuk skor kosinus eksak."""

    def __init__(self, collection: Any) -> None:
        import numpy as np

        data = collection.get(include=["embeddings", "metadatas"])
        emb = np.asarray(data["embeddings"], dtype=np.float64)
        self.vectors = emb / np.linalg.norm(emb, axis=1, keepdims=True)
        self.meta = [(str(m["article_id"]), str(m["section"])) for m in data["metadatas"]]

    def scores(self, query_vector: Any) -> list[ChunkScore]:
        """Skor kosinus eksak klaim terhadap setiap chunk."""
        import numpy as np

        q = np.asarray(query_vector, dtype=np.float64)
        sims = self.vectors @ (q / np.linalg.norm(q))
        return [ChunkScore(aid, sec, float(s)) for (aid, sec), s in zip(self.meta, sims)]


def _ranks(items: Sequence[dict[str, Any]], rankings: dict[str, list[tuple[str, float]]]) -> list[int | None]:
    return [article_rank(rankings[i["id"]], i["expected_retrieval_article"]) for i in items]


def experiment_top_k(items: list[dict], chunks: dict[str, list[ChunkScore]]) -> dict[str, Any]:
    """Eksperimen 1: Recall@k untuk beberapa k (agregasi maksimum, seluruh seksi)."""
    rankings = {i["id"]: rank_articles(chunks[i["id"]]) for i in items}
    per_group = {}
    for name, members in group_items(items).items():
        ranks = _ranks(members, rankings)
        per_group[name] = {f"recall@{k}": recall_summary(ranks, k) for k in K_VALUES}
    nonb = group_items(items)["non_batas"]
    base = [hit_at_k(r, PRODUCTION_K) for r in _ranks(nonb, rankings)]
    vs_k3 = {
        f"k={k}_vs_k=3": paired_comparison(base, [hit_at_k(r, k) for r in _ranks(nonb, rankings)])
        for k in K_VALUES if k != PRODUCTION_K
    }
    failures = {}
    for iid in V1_RECALL_FAILURES:
        item = next(i for i in items if i["id"] == iid)
        rank = article_rank(rankings[iid], item["expected_retrieval_article"])
        failures[iid] = {
            "subtipe": item.get("subtipe"), "artikel_diharapkan": item["expected_retrieval_article"],
            "peringkat_sebenarnya": rank,
            "masuk_mulai_k": next((k for k in K_VALUES if hit_at_k(rank, k)), None),
        }
    return {"per_kelompok": per_group, "perbandingan_non_batas_terhadap_k3": vs_k3,
            "kegagalan_recall3_v1": failures,
            "peringkat_per_butir": {i["id"]: article_rank(rankings[i["id"]], i["expected_retrieval_article"])
                                    for i in items}}


def experiment_aggregation(items: list[dict], chunks: dict[str, list[ChunkScore]]) -> dict[str, Any]:
    """Eksperimen 2: strategi agregasi skor per artikel (seluruh seksi)."""
    groups = group_items(items)
    result: dict[str, Any] = {"strategi": {}, "perbandingan_terhadap_maks": {}}
    hits: dict[tuple[str, str, int], list[bool]] = {}
    for name, agg in AGGREGATORS.items():
        rankings = {i["id"]: rank_articles(chunks[i["id"]], agg) for i in items}
        result["strategi"][name] = {}
        for gname in ("non_batas", "batas"):
            ranks = _ranks(groups[gname], rankings)
            result["strategi"][name][gname] = {f"recall@{k}": recall_summary(ranks, k) for k in (3, 5)}
            for k in (3, 5):
                hits[(name, gname, k)] = [hit_at_k(r, k) for r in ranks]
        result["strategi"][name]["peringkat_per_butir"] = {
            i["id"]: article_rank(rankings[i["id"]], i["expected_retrieval_article"]) for i in items}
    for name in AGGREGATORS:
        if name == "maks":
            continue
        comp: dict[str, Any] = {}
        for k in (3, 5):
            comp[f"recall@{k}_non_batas"] = paired_comparison(
                hits[("maks", "non_batas", k)], hits[(name, "non_batas", k)])
            moved = []
            for gname in ("non_batas", "batas"):
                for item, b, o in zip(groups[gname], hits[("maks", gname, k)], hits[(name, gname, k)]):
                    if b != o:
                        moved.append({"id": item["id"], "subtipe": item.get("subtipe") or item["tipe"],
                                      "perubahan": "salah->benar" if o else "benar->salah"})
            comp[f"butir_berpindah@{k}"] = moved
        result["perbandingan_terhadap_maks"][name] = comp
    return result


def experiment_sections(items: list[dict], chunks: dict[str, list[ChunkScore]]) -> dict[str, Any]:
    """Eksperimen 3: seksi pemenang pada artikel benar, dan Recall@3 per subset seksi."""
    groups = group_items(items)
    best = {i["id"]: best_section_of(chunks[i["id"]], i["expected_retrieval_article"]) for i in items}
    result: dict[str, Any] = {
        "seksi_terbaik_artikel_benar": {
            "non_batas": dict(Counter(best[i["id"]] for i in groups["non_batas"])),
            "batas": dict(Counter(best[i["id"]] for i in groups["batas"])),
            "per_tipe_non_batas": {
                g.split(":", 1)[1]: dict(Counter(best[i["id"]] for i in m))
                for g, m in groups.items() if g.startswith("tipe:")},
            "per_butir": best,
        },
        "kondisi": {}, "perbandingan_terhadap_seluruh_seksi": {},
    }
    hits: dict[str, list[bool]] = {}
    for cname, secs in SECTION_CONDITIONS.items():
        rankings = {i["id"]: rank_articles(chunks[i["id"]], sections=secs) for i in items}
        entry = {}
        for gname in ("non_batas", "batas"):
            ranks = _ranks(groups[gname], rankings)
            entry[gname] = {"recall@3": recall_summary(ranks, 3), "recall@5": recall_summary(ranks, 5)}
        for g, members in groups.items():
            if g.startswith(("tipe:", "subtipe:")):
                entry[g] = {"recall@3": recall_summary(_ranks(members, rankings), 3)}
        hits[cname] = [hit_at_k(r, 3) for r in _ranks(groups["non_batas"], rankings)]
        result["kondisi"][cname] = entry
    for cname in SECTION_CONDITIONS:
        if cname != "seluruh_seksi":
            comp = paired_comparison(hits["seluruh_seksi"], hits[cname])
            comp["butir_berpindah"] = [
                {"id": i["id"], "perubahan": "salah->benar" if o else "benar->salah"}
                for i, b, o in zip(groups["non_batas"], hits["seluruh_seksi"], hits[cname]) if b != o]
            result["perbandingan_terhadap_seluruh_seksi"][cname] = comp
    return result


def experiment_length(items: list[dict], model: Any, matrix: ChunkMatrix,
                      original_chunks: dict[str, list[ChunkScore]]) -> dict[str, Any]:
    """Eksperimen 4: Recall@3 butir positif (non-batas) saat klaim disisipi teks pengganggu."""
    positives = [i for i in items if i["tipe"] == "positif" and not i["batas"]]
    tokenizer = model.tokenizer
    max_tokens = int(model.max_seq_length)

    def ntok(text: str) -> int:
        return len(tokenizer(text, add_special_tokens=False)["input_ids"])

    base_ranks = [article_rank(rank_articles(original_chunks[i["id"]]), i["expected_retrieval_article"])
                  for i in positives]
    base_hits = [hit_at_k(r, 3) for r in base_ranks]
    result: dict[str, Any] = {
        "n_butir_positif": len(positives),
        "klaim_asli": {"recall@3": recall_summary(base_ranks, 3),
                       "panjang_karakter": [len(i["klaim"]) for i in positives]},
        "batas_token_embedding": max_tokens,
        "kondisi": {}, "per_butir": {},
    }
    for placement in PLACEMENTS:
        for target in LENGTH_TARGETS:
            texts, visibility = [], []
            for item in positives:
                rng = random.Random(f"{item['id']}|{target}|{placement}")
                text, offset = pad_claim(item["klaim"], target, rng, placement)
                texts.append(text)
                visibility.append(claim_visibility(ntok(text[:offset]), ntok(item["klaim"]), max_tokens))
            vectors = model.encode(texts, normalize_embeddings=True, batch_size=4)
            ranks, scores = [], []
            for item, vec in zip(positives, vectors):
                chunks = matrix.scores(vec)
                ranking = rank_articles(chunks)
                ranks.append(article_rank(ranking, item["expected_retrieval_article"]))
                scores.append(dict(ranking)[item["expected_retrieval_article"]])
            key = f"{placement}_{target}"
            result["kondisi"][key] = {
                "penempatan": placement, "target_karakter": target,
                "panjang_karakter_aktual": [min(len(t) for t in texts), max(len(t) for t in texts)],
                "token_total_median": statistics.median(ntok(t) for t in texts),
                "keterbacaan_klaim": dict(Counter(visibility)),
                "recall@3": recall_summary(ranks, 3),
                "perbandingan_terhadap_klaim_asli": paired_comparison(base_hits, [hit_at_k(r, 3) for r in ranks]),
            }
            for item, r, s, v in zip(positives, ranks, scores, visibility):
                result["per_butir"].setdefault(item["id"], {})[key] = {
                    "peringkat": r, "skor_artikel_benar": round(s, 4), "keterbacaan_klaim": v}
    for item, r in zip(positives, base_ranks):
        result["per_butir"].setdefault(item["id"], {})["asli"] = {"peringkat": r}
    return result


def fidelity_check(items: list[dict], chunks: dict[str, list[ChunkScore]], model: Any,
                   collection: Any) -> dict[str, Any]:
    """Top-3 eksak (agregasi maks) vs `retriever.retrieve` produksi vs top-3 tercatat evaluasi v1."""
    from retriever import retrieve

    exact = {i["id"]: [a for a, _ in rank_articles(chunks[i["id"]])[:3]] for i in items}
    prod = {i["id"]: [h.article_id for h in retrieve(i["klaim"], model, collection, top_k=3)] for i in items}
    recorded = load_recorded_top3()
    out: dict[str, Any] = {
        "eksak_sama_dengan_retrieve_produksi": sum(exact[k] == prod[k] for k in exact),
        "n": len(items),
        "berbeda_dari_produksi": [k for k in exact if exact[k] != prod[k]],
    }
    if recorded is None:
        out["tercatat_evaluasi_v1"] = "berkas hasil evaluasi tidak tersedia"
    else:
        out["eksak_sama_dengan_tercatat_evaluasi_v1"] = sum(exact[k] == recorded.get(k) for k in exact)
        out["berbeda_dari_tercatat"] = [k for k in exact if exact[k] != recorded.get(k)]
    return out


# ---------------------------------------------------------------------------------------------
# Laporan
# ---------------------------------------------------------------------------------------------

def _fmt(summary: dict[str, Any]) -> str:
    lo, hi = summary["wilson95"]
    return f"{summary['benar']:>2}/{summary['n']:<2} [{lo:.2f}-{hi:.2f}]"


def _cmp(c: dict[str, Any]) -> str:
    return (f"naik {c['naik']}, turun {c['turun']}, bersih {c['selisih_bersih']:+d}, "
            f"p McNemar {c['p_mcnemar']:.3f} -> {c['kesimpulan']}")


def build_report(res: dict[str, Any]) -> str:
    """Laporan terbaca manusia dari hasil JSON."""
    L: list[str] = []
    add = L.append
    add("=" * 94)
    add("EKSPERIMEN ABLASI RETRIEVAL -- SET UJI V1 BEKU (54 butir)")
    add("=" * 94)
    add(f"Tanggal: {res['meta']['tanggal']} | model embedding: {res['meta']['model_embedding']} | "
        f"chunk: {res['meta']['jumlah_chunk']} | batas token: {res['meta']['batas_token']}")
    add("")
    add("HANYA MENGUKUR RETRIEVAL. Tidak ada panggilan LLM. Pengaruh pada AKURASI AKHIR belum terukur:")
    add("mengukurnya butuh menjalankan generator dengan parameter lain, dan itu akan membatalkan")
    add("keabsahan baseline Versi 1 (set uji v1 sudah dipakai; perubahan harus diuji pada set uji baru).")
    add("Hasil ini PENGUKURAN, bukan penyetelan: parameter produksi tidak diubah.")
    add("")
    add("Aturan membaca selisih: dua kondisi dibandingkan pada butir yang SAMA dengan uji McNemar eksak.")
    add(f"'Selisih bermakna' hanya bila p < {ALPHA} DAN selisih bersih >= {MIN_NET_DIFF} butir. Selisih 1-2")
    add("butir TIDAK disimpulkan sebagai keunggulan. Caveat tambahan: 44% butir berbagi artikel jangkar")
    add("(tidak saling bebas), jadi interval Wilson dan p di bawah cenderung terlalu percaya diri.")
    add("Recall hanya dihitung pada butir yang punya expected_retrieval_article: 40 non-batas")
    add("(20 positif + 20 negatif sulit) dan 4 batas; 10 negatif mudah tidak punya artikel sasaran")
    add("dan TIDAK masuk hitungan (sama dengan Recall@3 36/40 pada evaluasi Versi 1).")
    add("")
    fid = res["validasi_kesetiaan"]
    add("VALIDASI KESETIAAN (skor eksak brute-force vs sistem produksi)")
    add(f"  top-3 eksak (agregasi maks) = retriever.retrieve produksi: "
        f"{fid['eksak_sama_dengan_retrieve_produksi']}/{fid['n']} butir {fid['berbeda_dari_produksi'] or ''}")
    if "eksak_sama_dengan_tercatat_evaluasi_v1" in fid:
        add(f"  top-3 eksak = top-3 tercatat evaluasi v1:                 "
            f"{fid['eksak_sama_dengan_tercatat_evaluasi_v1']}/{fid['n']} butir {fid['berbeda_dari_tercatat'] or ''}")
    add("")

    e1 = res["eksperimen_1_top_k"]
    add("-" * 94)
    add("EKSPERIMEN 1 -- Recall@k (agregasi maks, seluruh seksi). Format: benar/n [Wilson95]")
    add("-" * 94)
    add(f"{'kelompok':34}" + "".join(f"{'@' + str(k):>12}" for k in K_VALUES))
    for g, v in e1["per_kelompok"].items():
        add(f"{g:34}" + "".join(f"{v[f'recall@{k}']['benar']:>5}/{v[f'recall@{k}']['n']:<6}" for k in K_VALUES))
    add("")
    add("Non-batas, detail Wilson95:")
    for k in K_VALUES:
        add(f"  Recall@{k:<2} {_fmt(e1['per_kelompok']['non_batas'][f'recall@{k}'])}")
    add("")
    add("Perbandingan terhadap k=3 (non-batas; k lebih besar hanya bisa menambah):")
    for name, c in e1["perbandingan_non_batas_terhadap_k3"].items():
        add(f"  {name:12} {_cmp(c)}")
    add("")
    add("Empat kegagalan Recall@3 Versi 1 -- peringkat sebenarnya dan k pertama yang memuatnya:")
    for iid, f in e1["kegagalan_recall3_v1"].items():
        add(f"  {iid} ({f['subtipe']}): artikel {f['artikel_diharapkan']} peringkat {f['peringkat_sebenarnya']}, "
            f"masuk mulai k={f['masuk_mulai_k']} (dari k yang diuji {list(K_VALUES)})")
    add("")
    add("CATATAN: menaikkan k punya konsekuensi yang TIDAK diukur di sini -- konteks ke LLM membesar")
    add("(token dan biaya per panggilan), dan kandidat yang saling mirip dapat menaikkan risiko")
    add("kecocokan palsu. k yang memaksimalkan recall belum tentu k terbaik untuk sistem keseluruhan.")
    add("")

    e2 = res["eksperimen_2_agregasi"]
    add("-" * 94)
    add("EKSPERIMEN 2 -- Strategi agregasi skor per artikel (seluruh seksi)")
    add("-" * 94)
    add(f"{'strategi':24}{'non-batas @3':>22}{'non-batas @5':>22}{'batas @3':>16}{'batas @5':>16}")
    for name, v in e2["strategi"].items():
        add(f"{name:24}{_fmt(v['non_batas']['recall@3']):>22}{_fmt(v['non_batas']['recall@5']):>22}"
            f"{_fmt(v['batas']['recall@3']):>16}{_fmt(v['batas']['recall@5']):>16}")
    for name, c in e2["perbandingan_terhadap_maks"].items():
        add(f"  {name} vs maks:")
        for k in (3, 5):
            add(f"    @{k} non-batas: {_cmp(c[f'recall@{k}_non_batas'])}")
            moved = c[f"butir_berpindah@{k}"]
            add(f"    @{k} butir berpindah (termasuk batas): "
                + (", ".join(f"{m['id']}[{m['subtipe']}] {m['perubahan']}" for m in moved) or "tidak ada"))
    add("")

    e3 = res["eksperimen_3_seksi"]
    add("-" * 94)
    add("EKSPERIMEN 3 -- Kontribusi seksi")
    add("-" * 94)
    sb = e3["seksi_terbaik_artikel_benar"]
    add(f"Seksi chunk berskor tertinggi pada artikel yang BENAR (non-batas, n=40): {sb['non_batas']}")
    add("   (Ukuran ini BERBEDA dari 'seksi pemenang top-1 chunk' pada 10 kueri set pengembangan di")
    add("   CLAUDE.md, yang menghitung seksi chunk teratas SECARA KESELURUHAN, artikel apa pun.)")
    for t, v in sb["per_tipe_non_batas"].items():
        add(f"   {t}: {v}")
    add(f"   batas (n=4): {sb['batas']}")
    add("")
    add(f"{'kondisi':26}{'non-batas @3':>22}{'non-batas @5':>22}{'batas @3':>16}")
    for name, v in e3["kondisi"].items():
        add(f"{name:26}{_fmt(v['non_batas']['recall@3']):>22}{_fmt(v['non_batas']['recall@5']):>22}"
            f"{_fmt(v['batas']['recall@3']):>16}")
    add("  Recall@3 per tipe/subtipe (non-batas):")
    keys = [k for k in e3["kondisi"]["seluruh_seksi"] if k.startswith(("tipe:", "subtipe:"))]
    for key in keys:
        add(f"    {key:34}" + "".join(
            f"{e3['kondisi'][c][key]['recall@3']['benar']:>4}/{e3['kondisi'][c][key]['recall@3']['n']:<4}"
            for c in SECTION_CONDITIONS) + "   (urutan kolom: " + ", ".join(SECTION_CONDITIONS) + ")")
    for name, c in e3["perbandingan_terhadap_seluruh_seksi"].items():
        add(f"  {name} vs seluruh_seksi (@3 non-batas): {_cmp(c)}")
        add("     berpindah: " + (", ".join(f"{m['id']} {m['perubahan']}" for m in c["butir_berpindah"]) or "tidak ada"))
    add("")

    e4 = res["eksperimen_4_panjang_klaim"]
    add("-" * 94)
    add(f"EKSPERIMEN 4 -- Panjang klaim (butir positif non-batas, n={e4['n_butir_positif']}); "
        f"batas token embedding {e4['batas_token_embedding']}")
    add("-" * 94)
    add("Teks pengganggu SINTETIS (sapaan, ajakan menyebarkan, tanda baca berlebihan), bukan pesan asli:")
    add("hasilnya INDIKATIF. 'kedua_sisi' = pengganggu dibagi ke depan dan belakang klaim (skenario diminta);")
    add("'belakang' = pembanding, klaim di awal pesan, untuk memisahkan efek pengenceran dari pemotongan token.")
    add(f"  klaim asli: Recall@3 {_fmt(e4['klaim_asli']['recall@3'])}, panjang "
        f"{min(e4['klaim_asli']['panjang_karakter'])}-{max(e4['klaim_asli']['panjang_karakter'])} karakter")
    for key, v in e4["kondisi"].items():
        add(f"  {key:18} Recall@3 {_fmt(v['recall@3'])} | token median {v['token_total_median']:.0f} | "
            f"klaim terbaca: {v['keterbacaan_klaim']}")
        add(f"  {'':18} vs asli: {_cmp(v['perbandingan_terhadap_klaim_asli'])}")
    add("")
    add("Keterbacaan klaim: 'utuh' = seluruh token klaim di dalam batas embedding; 'sebagian' = terpotong;")
    add("'terpotong_seluruhnya' = klaim di luar batas (model hanya melihat pengganggu).")
    add("")
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------
# Utama
# ---------------------------------------------------------------------------------------------

def main() -> int:
    """Jalankan keempat eksperimen dan tulis JSON + laporan. Tanpa panggilan API."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-report", type=Path, default=OUT_REPORT)
    args = parser.parse_args()

    from ingest import MODEL_NAME, get_collection, load_model

    items = load_items()
    model = load_model()
    collection = get_collection()
    matrix = ChunkMatrix(collection)
    vectors = model.encode([i["klaim"] for i in items], normalize_embeddings=True, batch_size=8)
    chunks = {i["id"]: matrix.scores(v) for i, v in zip(items, vectors)}

    res: dict[str, Any] = {
        "meta": {
            "tanggal": datetime.now(timezone.utc).date().isoformat(),
            "model_embedding": MODEL_NAME,
            "jumlah_chunk": len(matrix.meta),
            "batas_token": int(model.max_seq_length),
            "jumlah_butir": len(items),
            "catatan": ("Hanya retrieval; tanpa panggilan LLM. Skor kosinus eksak terhadap seluruh chunk. "
                        "Pengukuran, bukan penyetelan: parameter produksi tidak diubah."),
            "aturan_selisih": {"alpha": ALPHA, "selisih_bersih_minimal": MIN_NET_DIFF,
                               "uji": "McNemar eksak dua sisi, berpasangan per butir"},
        },
        "validasi_kesetiaan": fidelity_check(items, chunks, model, collection),
        "eksperimen_1_top_k": experiment_top_k(targeted_items(items), chunks),
        "eksperimen_2_agregasi": experiment_aggregation(targeted_items(items), chunks),
        "eksperimen_3_seksi": experiment_sections(targeted_items(items), chunks),
        "eksperimen_4_panjang_klaim": experiment_length(items, model, matrix, chunks),
    }
    args.out_json.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = build_report(res)
    args.out_report.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"Ditulis: {args.out_json} dan {args.out_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
