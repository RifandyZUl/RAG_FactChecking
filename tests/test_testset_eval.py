"""
Uji offline evaluation.testset_eval -- TIDAK ADA panggilan API (ScriptedProvider palsu dari
tests/_fakes.py, retrieve_fn palsu). Menguji urutan acak per run, retry tingkat butir, jejak
retrieval, dan alur main() (resumability, penghentian saat kuota habis) tanpa menyentuh jaringan.
"""
import json
import sys

import pytest
from _fakes import ScriptedProvider, llm_json, make_hit

from evaluation import testset_eval as te
from generator import AnswerGenerator
from llm import LLMError, LLMQuotaExhaustedError


def test_shuffled_order_reproducible_and_covers_all_indices() -> None:
    order_a = te.shuffled_order(10, seed=42)
    order_b = te.shuffled_order(10, seed=42)
    assert order_a == order_b
    assert sorted(order_a) == list(range(10))


def test_shuffled_order_differs_across_seeds() -> None:
    orders = {run: te.shuffled_order(20, seed) for run, seed in te.RUN_SEEDS.items()}
    assert orders[1] != orders[2] != orders[3]
    assert orders[1] != orders[3]


def test_load_done_reads_run_idx_pairs(tmp_path) -> None:
    path = tmp_path / "out.jsonl"
    path.write_text(
        json.dumps({"run": 1, "idx": 0, "other": "x"}) + "\n"
        + json.dumps({"run": 1, "idx": 1, "other": "y"}) + "\n"
        + json.dumps({"run": 2, "idx": 0, "other": "z"}) + "\n",
        encoding="utf-8",
    )
    assert te.load_done(path) == {(1, 0), (1, 1), (2, 0)}


def test_load_done_missing_file_returns_empty(tmp_path) -> None:
    assert te.load_done(tmp_path / "nope.jsonl") == set()


def test_load_done_raises_on_corrupt_line(tmp_path) -> None:
    path = tmp_path / "out.jsonl"
    path.write_text("{not valid json\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        te.load_done(path)


def test_retrieval_trace_recall_hit_and_miss() -> None:
    hits = [make_hit("100"), make_hit("200"), make_hit("300")]
    trace_hit = te.retrieval_trace(hits, "200")
    assert trace_hit["recall_at_3"] is True
    assert len(trace_hit["retrieval_top3"]) == 3
    assert trace_hit["retrieval_best_section_top1"] == "narasi"

    trace_miss = te.retrieval_trace(hits, "999")
    assert trace_miss["recall_at_3"] is False

    trace_no_expected = te.retrieval_trace(hits, None)
    assert trace_no_expected["recall_at_3"] is None


def test_retrieval_trace_empty_hits() -> None:
    trace = te.retrieval_trace([], "100")
    assert trace["retrieval_top3"] == []
    assert trace["retrieval_best_section_top1"] is None
    assert trace["recall_at_3"] is False


def test_serialize_call_fields() -> None:
    from llm.base import CallRecord

    rec = CallRecord(provider="gemini", model="gemini-3.5-flash-lite", latency_s=1.2345, ok=True,
                     attempts=2, input_tokens=100, output_tokens=50, thought_tokens=10,
                     structured_mode="schema", rate_limited=1, error="", model_version="v1")
    s = te.serialize_call(rec)
    assert s["ok"] is True and s["attempts"] == 2 and s["latency_s"] == 1.234
    assert s["input_tokens"] == 100 and s["rate_limited"] == 1 and s["model_version"] == "v1"


def _fake_gen(outputs: list) -> tuple[AnswerGenerator, ScriptedProvider]:
    hits = [make_hit("100")]
    provider = ScriptedProvider(outputs)
    provider.model = "gemma-test"
    gen = AnswerGenerator(provider, lambda claim, k: hits[:k])
    return gen, provider


def test_answer_with_item_retries_succeeds_first_try() -> None:
    out = llm_json(artikel_terpilih="100", klaim_sama=True, alasan="a", klarifikasi="k")
    gen, _ = _fake_gen([out])
    ans, percobaan, status = te.answer_with_item_retries(gen, "klaim")
    assert status == "selesai"
    assert len(percobaan) == 1
    assert ans.verdict == "ditemukan"


def test_answer_with_item_retries_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(te.time, "sleep", lambda _s: None)
    ok = llm_json(artikel_terpilih="100", klaim_sama=True, alasan="a", klarifikasi="k")
    gen, _ = _fake_gen([LLMError("transient"), ok])
    ans, percobaan, status = te.answer_with_item_retries(gen, "klaim")
    assert status == "selesai"
    assert len(percobaan) == 2
    assert percobaan[0]["verdict"] == "gagal"
    assert ans.verdict == "ditemukan"


def test_answer_with_item_retries_exhausted_marks_tak_terjawab(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(te.time, "sleep", lambda _s: None)
    gen, _ = _fake_gen([LLMError("persistent")])
    ans, percobaan, status = te.answer_with_item_retries(gen, "klaim")
    assert status == "tak_terjawab"
    assert len(percobaan) == te.MAX_ITEM_RETRIES + 1
    assert all(p["verdict"] == "gagal" for p in percobaan)


def test_answer_with_item_retries_quota_exhausted_stops_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(te.time, "sleep", lambda _s: (_ for _ in ()).throw(AssertionError("tidak boleh tidur")))
    gen, _ = _fake_gen([LLMQuotaExhaustedError("habis")])
    ans, percobaan, status = te.answer_with_item_retries(gen, "klaim")
    assert status == "kuota_habis"
    assert len(percobaan) == 1  # TIDAK diulang


# -- main(): alur penuh dengan monkeypatch, tanpa panggilan API sungguhan --------------------

MINI_CASES = [
    {"id": "v1-001", "klaim": "klaim satu", "tipe": "positif", "subtipe": None,
     "expected_retrieval_article": "100", "expected_verdict": "ditemukan", "expected_label": "SALAH",
     "kekhususan": "spesifik", "batas": False},
    {"id": "v1-002", "klaim": "klaim dua", "tipe": "negatif_mudah", "subtipe": None,
     "expected_retrieval_article": None, "expected_verdict": "belum_ditemukan", "expected_label": None,
     "kekhususan": "jauh", "batas": False},
]


def _write_mini_v1(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    v1_file = tmp_path / "v1.jsonl"
    v1_file.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in MINI_CASES) + "\n", encoding="utf-8")
    monkeypatch.setattr(te, "V1_PATH", v1_file)
    monkeypatch.setattr(te, "DATA_DIR", tmp_path)
    monkeypatch.setattr(te, "N_RUNS", 1)  # 1 run x 2 butir = 2 pasangan, cukup untuk uji alur


def _patch_pipeline(monkeypatch: pytest.MonkeyPatch, provider: ScriptedProvider) -> None:
    hits = [make_hit("100")]
    monkeypatch.setattr(te, "get_provider", lambda **kw: provider)
    monkeypatch.setattr(te, "load_articles", lambda: [])
    monkeypatch.setattr(te, "load_model", lambda: object())
    monkeypatch.setattr(te, "get_collection", lambda: object())
    monkeypatch.setattr(te, "retrieve", lambda claim, model, collection, top_k: hits[:top_k])
    monkeypatch.setattr(te.time, "sleep", lambda _s: None)


def test_main_runs_all_pairs_and_writes_results(tmp_path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _write_mini_v1(tmp_path, monkeypatch)
    out_ok = llm_json(artikel_terpilih="100", klaim_sama=True, alasan="a", klarifikasi="k")
    provider = ScriptedProvider([out_ok])
    provider.model = "gemma-test-main"
    _patch_pipeline(monkeypatch, provider)
    monkeypatch.setattr(sys, "argv", ["testset_eval", "--run", "1"])

    rc = te.main()
    assert rc == 0

    out_file = te.out_path(provider.model)
    lines = [json.loads(x) for x in out_file.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(lines) == 2
    assert {(r["run"], r["idx"]) for r in lines} == {(1, 0), (1, 1)}
    assert all(r["status"] == "selesai" for r in lines)
    assert all("retrieval_top3" in r and "percobaan" in r for r in lines)


def test_main_resumes_and_skips_done_pairs(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_mini_v1(tmp_path, monkeypatch)
    out_ok = llm_json(artikel_terpilih="100", klaim_sama=True, alasan="a", klarifikasi="k")
    provider = ScriptedProvider([out_ok])
    provider.model = "gemma-test-resume"
    _patch_pipeline(monkeypatch, provider)
    monkeypatch.setattr(sys, "argv", ["testset_eval", "--run", "1"])

    out_file = te.out_path(provider.model)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({"run": 1, "idx": 0, "id": "v1-001", "status": "selesai"}) + "\n",
                        encoding="utf-8")

    rc = te.main()
    assert rc == 0
    lines = [json.loads(x) for x in out_file.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(lines) == 2  # 1 lama + 1 baru
    assert {(r["run"], r["idx"]) for r in lines} == {(1, 0), (1, 1)}


def test_main_stops_on_quota_exhausted_without_marking_wrong(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_mini_v1(tmp_path, monkeypatch)
    provider = ScriptedProvider([LLMQuotaExhaustedError("habis hari ini")])
    provider.model = "gemma-test-quota"
    _patch_pipeline(monkeypatch, provider)
    monkeypatch.setattr(sys, "argv", ["testset_eval"])

    rc = te.main()
    assert rc == 3
    out_file = te.out_path(provider.model)
    if out_file.exists():
        lines = [json.loads(x) for x in out_file.read_text(encoding="utf-8").splitlines() if x.strip()]
        assert all(r["status"] != "selesai" or r.get("verdict") != "gagal" for r in lines)


def test_main_check_budget_makes_no_calls(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_mini_v1(tmp_path, monkeypatch)
    provider = ScriptedProvider([Exception("tidak boleh dipanggil")])
    provider.model = "gemma-test-budget"
    _patch_pipeline(monkeypatch, provider)
    monkeypatch.setattr(sys, "argv", ["testset_eval", "--check-budget"])

    rc = te.main()
    assert rc == 0
    assert provider.prompts == []  # tidak ada panggilan .generate()


def test_run_flag_restricts_to_single_run(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--run N membatasi cakupan ke run N saja -- dipakai untuk melapor per run sebagai
    proses terpisah (instruksi pemilik proyek 2026-09-23)."""
    _write_mini_v1(tmp_path, monkeypatch)
    out_ok = llm_json(artikel_terpilih="100", klaim_sama=True, alasan="a", klarifikasi="k")
    provider = ScriptedProvider([out_ok])
    provider.model = "gemma-test-run2"
    _patch_pipeline(monkeypatch, provider)
    monkeypatch.setattr(sys, "argv", ["testset_eval", "--run", "2"])

    rc = te.main()
    assert rc == 0
    out_file = te.out_path(provider.model)
    lines = [json.loads(x) for x in out_file.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert {r["run"] for r in lines} == {2}
    assert {(r["run"], r["idx"]) for r in lines} == {(2, 0), (2, 1)}


def test_circuit_breaker_stops_after_two_consecutive_unanswered(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """2 butir berturut-turut tak_terjawab menghentikan proses (instruksi pemilik proyek
    2026-09-23: jangan diteruskan sampai kuota habis)."""
    v1_file = tmp_path / "v1.jsonl"
    three_cases = MINI_CASES + [
        {"id": "v1-003", "klaim": "klaim tiga", "tipe": "negatif_mudah", "subtipe": None,
         "expected_retrieval_article": None, "expected_verdict": "belum_ditemukan", "expected_label": None,
         "kekhususan": "jauh", "batas": False},
    ]
    v1_file.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in three_cases) + "\n", encoding="utf-8")
    monkeypatch.setattr(te, "V1_PATH", v1_file)
    monkeypatch.setattr(te, "DATA_DIR", tmp_path)

    provider = ScriptedProvider([LLMError("persistent")])  # SEMUA percobaan gagal -> tiap butir tak_terjawab
    provider.model = "gemma-test-circuit"
    _patch_pipeline(monkeypatch, provider)
    monkeypatch.setattr(sys, "argv", ["testset_eval", "--run", "1"])

    rc = te.main()
    assert rc == 3
    out_file = te.out_path(provider.model)
    lines = [json.loads(x) for x in out_file.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(lines) == 2  # berhenti setelah 2 tak_terjawab beruntun, butir ke-3 TIDAK dicoba
    assert all(r["status"] == "tak_terjawab" for r in lines)
