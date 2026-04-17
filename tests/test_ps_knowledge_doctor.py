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


def _make_facts_module(confidence: str = "high") -> dict:
    """Create a dict-type facts module with _q.confidence set."""
    return {"_q": {"confidence": confidence}, "content": "test"}


def _make_full_facts() -> dict:
    """Create facts.yaml data with all 16 modules non-empty."""
    return {
        "overview": {
            "intro": _make_facts_module(),
            "positioning": _make_facts_module(),
            "status": _make_facts_module(),
            "approach": _make_facts_module(),
            "roadmap": _make_facts_module(),
        },
        "functions": {
            "security": [{"name": "firewall"}],
            "operations": [{"name": "monitor"}],
            "integration": [{"name": "api"}],
        },
        "value": {
            "risk_defense": [{"desc": "reduce risk"}],
            "compliance": [{"std": "ISO27001"}],
            "business_enablement": _make_facts_module(),
            "cost_optimization": _make_facts_module(),
        },
        "capabilities": {
            "core_tech": [{"tech": "AI"}],
            "differentiators": [{"diff": "unique"}],
            "verification": [{"method": "test"}],
        },
        "scenarios": [{"name": "enterprise"}],
    }


def _make_partial_facts(filled: int) -> dict:
    """Create facts.yaml data with exactly `filled` modules non-empty (out of 16).

    Fills overview first (up to 5), then functions (up to 3), value (up to 4),
    capabilities (up to 3), scenarios (up to 1).
    """
    data: dict = {}
    remaining = filled

    # overview: up to 5
    keys_overview = ["intro", "positioning", "status", "approach", "roadmap"]
    overview = {}
    for k in keys_overview:
        if remaining <= 0:
            break
        overview[k] = _make_facts_module()
        remaining -= 1
    if overview:
        data["overview"] = overview

    # functions: up to 3
    keys_functions = ["security", "operations", "integration"]
    functions = {}
    for k in keys_functions:
        if remaining <= 0:
            break
        functions[k] = [{"name": "item"}]
        remaining -= 1
    if functions:
        data["functions"] = functions

    # value: up to 4 (2 lists + 2 dicts)
    value: dict = {}
    for k in ["risk_defense", "compliance"]:
        if remaining <= 0:
            break
        value[k] = [{"item": "x"}]
        remaining -= 1
    for k in ["business_enablement", "cost_optimization"]:
        if remaining <= 0:
            break
        value[k] = _make_facts_module()
        remaining -= 1
    if value:
        data["value"] = value

    # capabilities: up to 3
    capabilities = {}
    for k in ["core_tech", "differentiators", "verification"]:
        if remaining <= 0:
            break
        capabilities[k] = [{"item": "x"}]
        remaining -= 1
    if capabilities:
        data["capabilities"] = capabilities

    # scenarios: up to 1
    if remaining > 0:
        data["scenarios"] = [{"name": "test"}]

    return data


def _make_full_evidence() -> dict:
    """Create evidence.yaml data with all 7 keys non-empty."""
    return {
        "authority": {
            "market_reports": [{"report": "Gartner"}],
            "evaluations": [{"eval": "CCRC"}],
            "certifications": [{"cert": "ISO"}],
        },
        "honors": {
            "international": [{"award": "RSA"}],
            "domestic": [{"award": "national"}],
            "industry": [{"award": "sector"}],
        },
        "cases": [{"customer": "BigCorp"}],
    }


def _make_partial_evidence(filled: int) -> dict:
    """Create evidence.yaml data with exactly `filled` keys non-empty (out of 7)."""
    data: dict = {}
    remaining = filled

    authority = {}
    for k in ["market_reports", "evaluations", "certifications"]:
        if remaining <= 0:
            break
        authority[k] = [{"item": "x"}]
        remaining -= 1
    if authority:
        data["authority"] = authority

    honors = {}
    for k in ["international", "domestic", "industry"]:
        if remaining <= 0:
            break
        honors[k] = [{"item": "x"}]
        remaining -= 1
    if honors:
        data["honors"] = honors

    if remaining > 0:
        data["cases"] = [{"customer": "test"}]

    return data


def make_product(home: Path, slug: str, facts_data: dict,
                 evidence_data: dict | None = None) -> Path:
    """Create a product subdirectory with facts.yaml and optionally evidence.yaml."""
    pdir = home / "知识库" / "产品档案" / slug
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "facts.yaml").write_text(
        yaml.safe_dump(facts_data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    if evidence_data is not None:
        (pdir / "evidence.yaml").write_text(
            yaml.safe_dump(evidence_data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return pdir


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

    # products: 3 subdirectories with full facts + evidence
    for i in range(3):
        pdir = home / "知识库" / "产品档案" / f"product-{i}"
        pdir.mkdir()
        (pdir / "facts.yaml").write_text(yaml.safe_dump(_make_full_facts(), allow_unicode=True))
        (pdir / "evidence.yaml").write_text(yaml.safe_dump(_make_full_evidence(), allow_unicode=True))

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


# ---------- product tiered assessment ----------


def test_products_empty_dir(tmp_path):
    """Empty products dir → value=0, products_detail=[]."""
    home = make_home(tmp_path)

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["products"]["value"] == 0
    assert dims["products"]["products_detail"] == []
    assert dims["products"]["status"] == "empty"


def test_products_tier_kecha(tmp_path):
    """12/16 facts modules non-empty → tier='可查', facts_coverage_pct=75."""
    home = make_home(tmp_path)
    make_product(home, "product-a", _make_partial_facts(12))

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["products"]["value"] == 1
    detail = dims["products"]["products_detail"]
    assert len(detail) == 1
    assert detail[0]["slug"] == "product-a"
    assert detail[0]["tier"] == "可查"
    assert detail[0]["facts_coverage_pct"] == 75


def test_products_tier_ketou(tmp_path):
    """13/16 facts + 4/7 evidence → tier='可投'."""
    home = make_home(tmp_path)
    make_product(home, "product-b", _make_partial_facts(13),
                 _make_partial_evidence(4))

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    detail = dims["products"]["products_detail"]
    assert len(detail) == 1
    assert detail[0]["tier"] == "可投"
    assert detail[0]["facts_coverage_pct"] == 81
    assert detail[0]["evidence_coverage_pct"] == 57


def test_products_tier_yiluru(tmp_path):
    """8/16 facts → tier='已录入'."""
    home = make_home(tmp_path)
    make_product(home, "product-c", _make_partial_facts(8))

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    detail = dims["products"]["products_detail"]
    assert len(detail) == 1
    assert detail[0]["tier"] == "已录入"
    assert detail[0]["facts_coverage_pct"] == 50


def test_products_yaml_error_no_crash(tmp_path):
    """facts.yaml with YAML format error → product marked as error, no crash."""
    home = make_home(tmp_path)
    # Create a valid product
    make_product(home, "good-product", _make_partial_facts(12))
    # Create a broken product
    bad_dir = home / "知识库" / "产品档案" / "bad-product"
    bad_dir.mkdir()
    (bad_dir / "facts.yaml").write_text("{{invalid yaml: [", encoding="utf-8")

    r = run(["diagnose"], home=home)
    assert r.returncode == 0, r.stderr
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["products"]["value"] == 2
    detail = dims["products"]["products_detail"]
    slugs = {d["slug"]: d for d in detail}
    assert slugs["bad-product"]["tier"] == "error"
    assert slugs["good-product"]["tier"] == "可查"


def test_products_only_evidence_no_facts(tmp_path):
    """Only evidence.yaml without facts.yaml → not counted as valid product."""
    home = make_home(tmp_path)
    pdir = home / "知识库" / "产品档案" / "evidence-only"
    pdir.mkdir()
    (pdir / "evidence.yaml").write_text(
        yaml.safe_dump(_make_full_evidence(), allow_unicode=True), encoding="utf-8"
    )

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["products"]["value"] == 0
    assert dims["products"]["products_detail"] == []


def test_products_example_excluded(tmp_path):
    """example/ directory excluded from product count."""
    home = make_home(tmp_path)
    # example dir with valid facts.yaml should be excluded
    make_product(home, "example", _make_full_facts(), _make_full_evidence())
    # real product should be counted
    make_product(home, "real-product", _make_partial_facts(10))

    r = run(["diagnose"], home=home)
    dims = _dims_by_name(json.loads(r.stdout))
    assert dims["products"]["value"] == 1
    assert len(dims["products"]["products_detail"]) == 1
    assert dims["products"]["products_detail"][0]["slug"] == "real-product"


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


def test_mini_mode_products_detail_preserved(tmp_path):
    """Mini mode should preserve products_detail field."""
    home = make_home(tmp_path)
    make_product(home, "some-product", _make_partial_facts(8))

    r = run(["diagnose", "--mode", "mini"], home=home)
    result = json.loads(r.stdout)
    dims = _dims_by_name(result)
    assert "products" in dims
    assert "products_detail" in dims["products"]
    assert len(dims["products"]["products_detail"]) == 1


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
