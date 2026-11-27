"""L1 acceptance tests for the official APMCM LaTeX paper scaffold."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
OFFICIAL = ROOT / "official_template"

OFFICIAL_HASHES = {
    "main.tex": "35ef7b39a32b6ddd7bf851a732644d0fba972f7d1251881489c717214b8fc5bf",
    "apmcmthesis.cls": "22bb5c34ee56760d2cd6af3286083e05084ea5bddf78160d8e7a4ef9b7220f26",
    "apmcmthesis.cfg": "5977897c04bcdcf0e34dbd7958ddbf636cd9d2413f2250a126e8b0bbd5fc882a",
    "ControlSheet.tex": "4ee85a304372f31f2b1a1effbcedcc0ce4ba57100069190c75655c81d104d89c",
}

SECTIONS = [
    "01_introduction.tex",
    "02_problem_formulation.tex",
    "03_data_and_audit.tex",
    "04_q1_surrogate.tex",
    "05_q2_qubo.tex",
    "06_q3_qubo.tex",
    "07_hardware_and_precision.tex",
    "08_results_and_discussion.tex",
    "09_conclusion.tex",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_official_source_files_are_byte_exact() -> None:
    for name, expected in OFFICIAL_HASHES.items():
        assert sha256(OFFICIAL / name) == expected


def test_l1_tree_is_complete() -> None:
    required = [
        "README.md",
        "main.tex",
        "apmcmthesis.cls",
        "apmcmthesis.cfg",
        "references.bib",
        "appendix/appendix.tex",
        "appendix/source_code_inventory.md",
        "compliance/official_rules_checklist.md",
        "compliance/page_count_check.md",
        "compliance/reference_audit.md",
        "compliance/final_pdf_checklist.md",
        "compliance/latex_environment_report.md",
        "compliance/official_template_acceptance.md",
        "compliance/template_manifest.json",
        "scripts/build.sh",
        "scripts/check_pdf.py",
        "L1_completion_report.md",
    ]
    missing = [name for name in required if not (PAPER / name).is_file()]
    missing += [f"sections/{name}" for name in SECTIONS if not (PAPER / "sections" / name).is_file()]
    assert not missing, f"missing L1 files: {missing}"


def test_template_snapshot_and_working_class_are_unmodified() -> None:
    for name in ("main.tex", "apmcmthesis.cls", "apmcmthesis.cfg"):
        assert sha256(PAPER / "template_original" / name) == OFFICIAL_HASHES[name]
    for name in ("apmcmthesis.cls", "apmcmthesis.cfg"):
        assert sha256(PAPER / name) == OFFICIAL_HASHES[name]


def test_modular_main_preserves_template_contract() -> None:
    source = (PAPER / "main.tex").read_text(encoding="utf-8")
    assert r"\documentclass{apmcmthesis}" in source
    assert r"\tihao{D}" in source
    assert "TEAM-NUMBER-PLACEHOLDER" in source
    assert r"\begin{abstract}" in source
    assert r"\tableofcontents" in source
    assert source.index(r"\begin{abstract}") < source.index(r"\tableofcontents")
    assert source.index(r"\tableofcontents") < source.index(r"\pagestyle{mainmatterstyle}")
    for name in SECTIONS:
        stem = name.removesuffix(".tex")
        assert rf"\input{{sections/{stem}}}" in source


def test_pending_results_are_traceable_and_not_presented_as_complete() -> None:
    pending_ids = {"O-08", "O-09", "O-10", "O-11", "O-12", "O-13", "O-14", "O-15"}
    paper_text = "\n".join(path.read_text(encoding="utf-8") for path in (PAPER / "sections").glob("*.tex"))
    for task_id in pending_ids:
        assert task_id in paper_text
    assert "successful quantum optimization" not in paper_text.lower()
    assert "quantum advantage" not in paper_text.lower()


def test_manifest_is_valid_and_matches_official_files() -> None:
    manifest = json.loads((PAPER / "compliance" / "template_manifest.json").read_text(encoding="utf-8"))
    records = {record["path"]: record["sha256"] for record in manifest["files"]}
    for name, expected in OFFICIAL_HASHES.items():
        assert records[f"official_template/{name}"] == expected


def test_build_artifacts_are_ignored() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/paper/build/" in ignore


def test_pdf_checker_uses_stable_official_header_markers() -> None:
    source = (PAPER / "scripts" / "check_pdf.py").read_text(encoding="utf-8")
    assert '"Team #"' in source
    assert '"Page 1 of"' in source
    assert '"Research question"' not in source


def test_dataset_table_is_referenced_in_text() -> None:
    source = (PAPER / "sections" / "03_data_and_audit.tex").read_text(encoding="utf-8")
    assert source.count(r"\label{tab:dataset-roles}") == 1
    assert source.count(r"\ref{tab:dataset-roles}") >= 1


def test_pdf_checker_rejects_short_pdf_without_traceback() -> None:
    pytest.importorskip("pypdf")
    result = subprocess.run(
        [sys.executable, str(PAPER / "scripts" / "check_pdf.py"), str(OFFICIAL / "ControlSheet.pdf")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "expected at least Summary Sheet, contents, and one body page" in result.stdout
    assert "Traceback" not in result.stderr

