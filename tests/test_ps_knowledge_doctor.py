# INPUT: pytest, ps_knowledge_doctor, ps_paths
# OUTPUT: unit + integration tests for diagnose subcommand across 9 dimensions
# POS: covers empty KB, full KB, mixed states, expired certs, mini mode, edge cases

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "ps_knowledge_doctor.py"


def run(args: list[str], *, home: Path) -> subprocess.CompletedProcess:
    env = {
        "PRESALES_HOME": str(home),
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "HOME": str(home.parent),
    }
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def make_home(tmp_path: Path) -> Path:
    """Create a bare knowledge base skeleton (post-setup state)."""
    home = tmp_path / "售前"
    for d in [
        "知识库/资质证书",
        "知识库/公司介绍",
        "知识库/客户案例",
        "知识库/产品档案",
        "知识库/竞品",
        "知识库/团队",
    ]:
        (home / d).mkdir(parents=True)
    return home


def write_profile(home: Path, data: dict) -> Path:
    path = home / "知识库" / "company-profile.yaml"
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _dims_by_name(result: dict) -> dict[str, dict]:
    return {d["dimension"]: d for d in result["dimensions"]}


# ---------- empty knowledge base ----------


def test_empty_kb_all_empty(tmp_path):
    """Fresh setup: all 9 dimensions should be 'empty'."""
    home = make_home(tmp_path)

    r = run(["diagnose"], home=home)
    assert r.returncode == 0, r.stderr
    result = json.loads(r.stdout)

    assert result["total_dimensions"] == 9
    assert result["empty_count"] == 9
    assert result["sufficient_count"] == 0
    assert result["completeness_pct"] == 0

    for dim in result["dimensions"]:
        assert dim["status"] == "empty", f"{dim['dimension']} should be empty"


# ---------- fully populated knowledge base ----------


def test_full_kb_all_sufficient(tmp_path):
    """Fully populated KB: all 9 dimensions should be 'sufficient'."""
    home = make_home(tmp_path)

    # company certs: 15 valid
    quals = [
        {"id": f"QUAL-{i:03d}", "name": f"Cert {i}", "valid_until": "2030-12-31",
         "evidence_file": f"知识库/资质证书/cert{i}.pdf"}
        for i in range(1, 16)
    ]
    write_profile(home, {
        "qualifications": quals,
        "case_references": [{"id": f"CASE-{i}"} for i in range(5)],
        "highlights": ["H1", "H2", "H3"],
    })

    # team roster
    roster = {
        "meta": {"total_valid_certs": 150, "total_people": 100},
        "cert_summary_by_type": {"CISP": 50, "PMP": 30, "CISSP": 20},
    }
    (home / "知识库" / "团队" / "roster.yaml").write_text(
        yaml.safe_dump(roster, allow_unicode=True), encoding="utf-8"
    )

    # team registry: 3 shards
    for s in ["cisp", "pmp", "security"]:
        (home / "知识库" / "团队" / f"cert-registry-{s}.yaml").write_text("certs: []\n")

    # products: 3 YAML
    for i in range(3):
        (home / "知识库" / "产品档案" / f"product-{i}.yaml").write_text(f"name: P{i}\n")

    # competitors: 10 YAML
    for i in range(10):
        (home / "知识库" / "竞品" / f"comp-{i}.yaml").write_text(f"company: C{i}\n")

    # about: 3 files
    for f in ["license.pdf", "intro.md", "brochure.pdf"]:
        (home / "知识库" / "公司介绍" / f).write_bytes(b"data")

    # case_studies: 10 files
    for i in range(10):
        (home / "知识库" / "客户案例" / f"case-{i}.md").write_text(f"Case {i}\n")

    r = run(["diagnose"], home=home)
    assert r.returncode == 0, r.stderr
    result = json.loads(r.stdout)

    assert result["sufficient_count"] == 9
    assert result["completeness_pct"] == 100

    for dim in result["dimensions"]:
        assert dim["status"] == "sufficient", f"{dim['dimension']} should be sufficient"


# ---------- mixed states ----------


def test_mixed_states(tmp_path):
    """Some sufficient, some insufficient, some empty."""
    home = make_home(tmp_path)

    # company certs: 7 valid (insufficient: >= 5 but < 15)
    quals = [
        {"id": f"QUAL-{i:03d}", "name": f"Cert {i}", "valid_until": "2030-12-31",
         "evidence_file": f"cert{i}.pdf"}
        for i in range(1, 8)
    ]
    write_profile(home, {"qualifications": quals})

    # competitors: 5 YAML (insufficient: >= 3 but < 10)
    for i in range(5):
        (home / "知识库" / "竞品" / f"comp-{i}.yaml").write_text(f"company: C{i}\n")

    r = run(["diagnose"], home=home)
    result = json.loads(r.stdout)
    dims = _dims_by_name(result)

    assert dims["company_certs"]["status"] == "insufficient"
    assert dims["competitors"]["status"] == "insufficient"
    assert dims["products"]["status"] == "empty"
    assert dims["highlights"]["status"] == "empty"

    # completeness = passing (insufficient + sufficient) / 9
    assert result["passing_dimensions"] == 2
    assert result["completeness_pct"] == round(2 / 9 * 100)


# ---------- expired certs ----------


def test_expired_certs_only_valid_counted(tmp_path):
    """Expired certs should not count toward the valid total."""
    home = make_home(tmp_path)

    quals = [
        {"id": "QUAL-001", "name": "Expired", "valid_until": "2020-01-01"},
        {"id": "QUAL-002", "name": "Expired2", "valid_until": "2023-06-01"},
        {"id": "QUAL-003", "name": "Valid", "valid_until": "2030-12-31"},
    ]
    write_profile(home, {"qualifications": quals})

    r = run(["diagnose"], home=home)
    result = json.loads(r.stdout)
    dims = _dims_by_name(result)

    cert_dim = dims["company_certs"]
    assert cert_dim["total"] == 3
    assert cert_dim["valid"] == 1
    assert cert_dim["expired"] == 2
    assert cert_dim["value"] == 1  # only valid counts
    assert cert_dim["status"] == "empty"  # 1 < 5 baseline


# ---------- team roster edge cases ----------


def test_team_roster_exists_but_empty_summary(tmp_path):
    """roster.yaml exists but cert_summary empty → still empty."""
    home = make_home(tmp_path)
    roster = {"meta": {"total_valid_certs": 0, "total_people": 0}, "cert_summary_by_type": {}}
    (home / "知识库" / "团队" / "roster.yaml").write_text(
        yaml.safe_dump(roster, allow_unicode=True), encoding="utf-8"
    )

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["team_roster"]["status"] == "empty"


def test_team_roster_with_certs_below_sufficient(tmp_path):
    """roster with 50 certs → insufficient (baseline met, < 100)."""
    home = make_home(tmp_path)
    roster = {
        "meta": {"total_valid_certs": 50, "total_people": 30},
        "cert_summary_by_type": {"CISP": 50},
    }
    (home / "知识库" / "团队" / "roster.yaml").write_text(
        yaml.safe_dump(roster, allow_unicode=True), encoding="utf-8"
    )

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["team_roster"]["status"] == "insufficient"
    assert dims["team_roster"]["value"] == 50


# ---------- product example exclusion ----------


def test_products_exclude_example(tmp_path):
    """example.yaml should not count as a product."""
    home = make_home(tmp_path)
    (home / "知识库" / "产品档案" / "example.yaml").write_text("name: example\n")
    (home / "知识库" / "产品档案" / "Example_Product.yaml").write_text("name: ex\n")
    (home / "知识库" / "产品档案" / "real-product.yaml").write_text("name: real\n")

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["products"]["count"] == 1  # only real-product.yaml


# ---------- mini mode ----------


def test_mini_mode_only_non_sufficient(tmp_path):
    """Mini mode should exclude sufficient dimensions from output."""
    home = make_home(tmp_path)

    # competitors: 15 → sufficient
    for i in range(15):
        (home / "知识库" / "竞品" / f"comp-{i}.yaml").write_text(f"company: C{i}\n")

    r = run(["diagnose", "--mode", "mini"], home=home)
    result = json.loads(r.stdout)

    dim_names = {d["dimension"] for d in result["dimensions"]}
    assert "competitors" not in dim_names  # sufficient → excluded
    assert "products" in dim_names  # empty → included

    # Summary counts should still reflect all 9 dimensions
    assert result["total_dimensions"] == 9
    assert result["sufficient_count"] == 1


# ---------- knowledge base dir missing ----------


def test_kb_dir_missing(tmp_path):
    """No 知识库 directory → exit code 3."""
    home = tmp_path / "售前"
    home.mkdir()

    r = run(["diagnose"], home=home)
    assert r.returncode == 3
    assert "知识库目录不存在" in r.stderr


# ---------- README exclusion ----------


def test_readme_not_counted(tmp_path):
    """README.md in directories should not be counted."""
    home = make_home(tmp_path)
    (home / "知识库" / "公司介绍" / "README.md").write_text("guide\n")
    (home / "知识库" / "客户案例" / "README.md").write_text("guide\n")

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["about"]["count"] == 0
    assert dims["case_studies"]["count"] == 0


# ---------- no company-profile.yaml ----------


def test_no_profile_yaml(tmp_path):
    """Missing company-profile.yaml → profile-based dimensions all empty, no crash."""
    home = make_home(tmp_path)

    r = run(["diagnose"], home=home)
    assert r.returncode == 0
    dims = _dims_by_name(json.loads(r.stdout))

    assert dims["company_certs"]["total"] == 0
    assert dims["case_references"]["count"] == 0
    assert dims["highlights"]["count"] == 0
