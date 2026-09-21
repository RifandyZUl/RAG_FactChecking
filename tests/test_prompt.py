"""Uji isi prompt sistem generator: definisi resmi "klaim sama" tertulis di dalam sistem, dan contohnya bersih."""

import re

from evaluation.retrieval_eval import NEGATIVE_QUERIES, QUERIES
from generator import RESPONSE_SCHEMA, SYSTEM_PROMPT


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _shingles(words: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def test_prompt_states_the_written_definition_of_same_claim() -> None:
    p = SYSTEM_PROMPT
    for needle in ("KLAIM INTI", "Judul", "Kesimpulan", "Narasi", "Unsur inti", "Unsur perifer",
                   "Uji dua arah", "Uji Kesimpulan", "UMUM", "SPESIFIK", "SEBAGIAN", "Sinonim",
                   "Bentuk pertanyaan", "lebih dari satu kandidat"):
        assert needle in p, f"prompt tidak memuat: {needle}"
    assert "BUKAN kesamaan klaim" in p
    assert p.index("KLAIM INTI") < p.index("Narasi"), "klaim inti (Judul) harus didefinisikan sebelum Narasi"


def test_prompt_examples_do_not_reuse_development_queries() -> None:
    """Contoh tidak boleh berasal dari 10 kueri set pengembangan (tak ada 4 kata berurutan yang sama)."""
    prompt_shingles = _shingles(_words(SYSTEM_PROMPT), 4)
    dev = [q for q, _ in QUERIES] + [q for q, _, _ in NEGATIVE_QUERIES]
    assert len(dev) == 10
    for q in dev:
        overlap = _shingles(_words(q), 4) & prompt_shingles
        assert not overlap, f"prompt memakai potongan kueri pengembangan {q!r}: {sorted(overlap)[:2]}"
    assert "vaksin flu" not in SYSTEM_PROMPT.lower()


def test_no_third_verdict_and_schema_shape_unchanged() -> None:
    """Tidak ada verdict ketiga 'artikel terkait' (kandidat fitur Versi 2); skema tetap empat bidang."""
    assert set(RESPONSE_SCHEMA["properties"]) == {"artikel_terpilih", "klaim_sama", "alasan", "klarifikasi"}
    assert RESPONSE_SCHEMA["properties"]["klaim_sama"]["type"] == "boolean"
    assert "artikel terkait" not in SYSTEM_PROMPT.lower()
