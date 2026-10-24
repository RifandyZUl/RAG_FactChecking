"""Variabel lingkungan Hugging Face disetel di titik masuk (hf_env.prepare_hf_env), bukan saat modul diimpor."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HF_KEYS = ("HF_HUB_OFFLINE", "DISABLE_SAFETENSORS_CONVERSION", "HF_HUB_DISABLE_SYMLINKS_WARNING")
ENTRY_POINTS = ["src/ingest.py"] + [f"src/evaluation/{m}.py" for m in (
    "index_check", "retriever_exactness", "retrieval_ablation", "index_comparison", "testset_eval", "external_eval",
    "external_analysis", "generation_eval", "repeat_eval", "retrieval_eval", "embedding_proof")] + [
    "src/labeling/candidates/screen.py", "src/labeling/candidates/chain_sample.py", "src/labeling/gap/gap_review.py",
    "src/webapp/serve.py"]
IMPORTED_MODULES = ["paths", "hf_env", "chunker", "ingest", "retriever", "generator", "webapp.settings",
                    "webapp.resources", "webapp.service", "webapp.presentation", "webapp.evaluation_facts",
                    "scraping.scheduled"] + [p.removeprefix("src/").removesuffix(".py").replace("/", ".") for p in ENTRY_POINTS]


def _run(code: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in HF_KEYS}
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=300,
                          cwd=ROOT, check=False)


def test_importing_project_modules_does_not_change_os_environ() -> None:
    code = ("import importlib, os, sys\nbefore = dict(os.environ)\n"
            f"for m in {IMPORTED_MODULES!r}:\n    importlib.import_module(m)\n"
            "changed = sorted(k for k in set(before) | set(os.environ) if before.get(k) != os.environ.get(k))\n"
            "print('BERUBAH', changed)\n"
            "print('TERMUAT', [m for m in ('huggingface_hub', 'transformers') if m in sys.modules])")
    out = _run(code)
    assert out.returncode == 0, out.stderr[-2000:]
    assert "BERUBAH []" in out.stdout, out.stdout
    assert "TERMUAT []" in out.stdout, "mengimpor modul proyek tidak boleh memuat pustaka Hugging Face"


@pytest.mark.parametrize("path", ENTRY_POINTS)
def test_every_entry_point_prepares_the_environment_first(path: str) -> None:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    body = [s for s in main.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    first = body[0]
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call)
    assert getattr(first.value.func, "id", None) == "prepare_hf_env", f"{path}: main() harus diawali prepare_hf_env()"


def test_demo_entry_prepares_the_environment_before_other_imports() -> None:
    tree = ast.parse((ROOT / "src" / "webapp" / "app.py").read_text(encoding="utf-8"))
    stmts = [s for s in tree.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    assert isinstance(stmts[0], ast.ImportFrom) and stmts[0].module == "hf_env"
    assert isinstance(stmts[1], ast.Expr) and getattr(stmts[1].value.func, "id", None) == "prepare_hf_env"


def test_entry_point_runs_offline() -> None:
    """Titik masuk sungguhan (ingest --help): setelah main() dimulai, Hub dalam mode offline."""
    out = _run("import os, sys\nsys.argv = ['ingest', '--help']\nimport ingest\n"
               "try:\n    ingest.main()\nexcept SystemExit:\n    pass\n"
               "import huggingface_hub.constants as c\n"
               "print('OFFLINE', os.environ.get('HF_HUB_OFFLINE'), c.HF_HUB_OFFLINE)")
    assert out.returncode == 0, out.stderr[-2000:]
    assert "OFFLINE 1 True" in out.stdout


def test_offline_can_be_overridden_for_the_first_download() -> None:
    env_code = "import os\nos.environ['HF_HUB_OFFLINE'] = '0'\nfrom hf_env import prepare_hf_env\nprepare_hf_env()\n"
    out = _run(env_code + "print('NILAI', os.environ['HF_HUB_OFFLINE'])")
    assert "NILAI 0" in out.stdout


def test_calling_too_late_fails_loudly_and_repeat_calls_are_harmless() -> None:
    late = _run("import huggingface_hub\nfrom hf_env import prepare_hf_env\nprepare_hf_env()")
    assert late.returncode != 0 and "dipanggil setelah huggingface_hub" in late.stderr
    again = _run("from hf_env import prepare_hf_env\nprepare_hf_env()\nimport transformers\nprepare_hf_env()\nprint('OK')")
    assert again.returncode == 0 and "OK" in again.stdout, again.stderr[-2000:]
