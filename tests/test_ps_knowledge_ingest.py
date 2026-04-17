# INPUT: pytest, ps_knowledge_ingest, ps_paths
# OUTPUT: unit + integration tests for scan/apply subcommands
# POS: covers all 9 scan scenarios + 9 apply scenarios + 2 integration cases from plan

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "ps_knowledge_ingest.py"


def run(args: list[str], *, home: Path, stdin: str | None = None) -> subprocess.CompletedProcess:
    env = {
        "PRESALES_HOME": str(home),
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "HOME": str(home.parent),
    }
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        input=stdin,
        env=env,
    )


def make_home(tmp_path: Path) -> Path:
    home = tmp_path / "售前"
    (home / "知识库" / "资质证书").mkdir(parents=True)
    return home


def write_profile(home: Path, data: dict) -> Path:
    path = home / "知识库" / "company-profile.yaml"
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def touch_pdfs(home: Path, names: list[str]) -> None:
    certs = home / "知识库" / "资质证书"
    for n in names:
        (certs / n).write_bytes(b"%PDF-1.4 fake\n")


# ---------- scan ----------


def test_scan_all_new(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf", "b.pdf", "c.pdf"])

    r = run(["scan", "--type", "certs"], home=home)

    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["new_files"] == ["a.pdf", "b.pdf", "c.pdf"]
    assert out["already_registered"] == 0
    assert out["over_limit"] is False


def test_scan_some_registered(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf", "b.pdf", "c.pdf"])
    write_profile(
        home,
        {
            "qualifications": [
                {"id": "QUAL-001", "name": "X", "evidence_file": "知识库/资质证书/b.pdf"},
            ]
        },
    )

    r = run(["scan", "--type", "certs"], home=home)

    out = json.loads(r.stdout)
    assert sorted(out["new_files"]) == ["a.pdf", "c.pdf"]
    assert out["already_registered"] == 1


def test_scan_empty_dir(tmp_path):
    home = make_home(tmp_path)

    r = run(["scan", "--type", "certs"], home=home)

    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["new_files"] == []
    assert out["already_registered"] == 0


def test_scan_over_limit(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, [f"cert-{i:02d}.pdf" for i in range(25)])

    r = run(["scan", "--type", "certs"], home=home)

    out = json.loads(r.stdout)
    assert out["over_limit"] is True
    assert len(out["new_files"]) == 20


def test_scan_ignores_readme_and_hidden(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["real.pdf"])
    (home / "知识库" / "资质证书" / "README.md").write_text("guide")
    (home / "知识库" / "资质证书" / ".DS_Store").write_bytes(b"\x00")

    r = run(["scan", "--type", "certs"], home=home)

    out = json.loads(r.stdout)
    assert out["new_files"] == ["real.pdf"]


def test_scan_missing_profile_treated_as_empty(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf"])
    # no company-profile.yaml

    r = run(["scan", "--type", "certs"], home=home)

    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["new_files"] == ["a.pdf"]


def test_scan_dir_missing(tmp_path):
    home = tmp_path / "售前"
    home.mkdir()
    # no 知识库/资质证书 created

    r = run(["scan", "--type", "certs"], home=home)

    assert r.returncode == 3
    assert "资质证书目录不存在" in r.stderr


def test_scan_corrupt_yaml(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf"])
    (home / "知识库" / "company-profile.yaml").write_text(
        "qualifications:\n  - [broken", encoding="utf-8"
    )

    r = run(["scan", "--type", "certs"], home=home)

    assert r.returncode == 4
    assert "YAML 解析失败" in r.stderr


def test_scan_case_insensitive_match(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["ISO27001.PDF"])
    write_profile(
        home,
        {
            "qualifications": [
                {"id": "QUAL-001", "evidence_file": "知识库/资质证书/iso27001.pdf"}
            ]
        },
    )

    r = run(["scan", "--type", "certs"], home=home)

    out = json.loads(r.stdout)
    assert out["new_files"] == []
    assert out["already_registered"] == 1


# ---------- apply ----------


def minimal_item(file="a.pdf", name="ISO 27001", issuer="CNAS", valid_until="2027-06-30", **kw):
    return dict(file=file, name=name, issuer=issuer, valid_until=valid_until, **kw)


def test_apply_empty_profile_two_entries(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf", "b.pdf"])
    payload = [minimal_item(file="a.pdf"), minimal_item(file="b.pdf", name="等保三级")]

    r = run(
        ["apply", "--payload-file", "-"],
        home=home,
        stdin=json.dumps(payload),
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["added"] == 2
    assert out["ids"] == ["QUAL-001", "QUAL-002"]

    profile = yaml.safe_load((home / "知识库" / "company-profile.yaml").read_text(encoding="utf-8"))
    assert len(profile["qualifications"]) == 2
    assert profile["qualifications"][0]["evidence_file"] == "知识库/资质证书/a.pdf"
    assert profile["qualifications"][0]["ingested_at"]


def test_apply_continues_from_max_id(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf"])
    write_profile(
        home,
        {
            "qualifications": [
                {"id": "QUAL-005", "name": "existing", "evidence_file": "知识库/资质证书/old.pdf"}
            ]
        },
    )

    r = run(
        ["apply", "--payload-file", "-"],
        home=home,
        stdin=json.dumps([minimal_item()]),
    )
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["ids"] == ["QUAL-006"]


def test_apply_ignores_non_standard_id(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf"])
    write_profile(
        home,
        {
            "qualifications": [
                {"id": "CERT-ABC", "evidence_file": "知识库/资质证书/x.pdf"}
            ]
        },
    )

    r = run(["apply", "--payload-file", "-"], home=home, stdin=json.dumps([minimal_item()]))
    out = json.loads(r.stdout)
    assert out["ids"] == ["QUAL-001"]


def test_apply_preserves_chinese(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf"])
    payload = [minimal_item(name="信息安全管理体系认证", issuer="中国信息安全测评中心")]

    r = run(["apply", "--payload-file", "-"], home=home, stdin=json.dumps(payload))
    assert r.returncode == 0

    raw = (home / "知识库" / "company-profile.yaml").read_text(encoding="utf-8")
    assert "信息安全管理体系认证" in raw
    assert "\\u" not in raw  # no unicode escape


def test_apply_empty_payload_no_write(tmp_path):
    home = make_home(tmp_path)
    profile_path = write_profile(home, {"company": {"name_zh": "X"}, "qualifications": []})
    before = profile_path.read_text(encoding="utf-8")

    r = run(["apply", "--payload-file", "-"], home=home, stdin="[]")
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out == {"added": 0, "ids": []}

    assert profile_path.read_text(encoding="utf-8") == before
    assert not profile_path.with_suffix(".yaml.bak").exists()


def test_apply_missing_required_field(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf"])
    profile_path = write_profile(home, {"qualifications": []})
    before = profile_path.read_text(encoding="utf-8")

    bad = [{"file": "a.pdf", "name": "X", "issuer": "Y"}]  # no valid_until
    r = run(["apply", "--payload-file", "-"], home=home, stdin=json.dumps(bad))

    assert r.returncode == 5
    assert "valid_until" in r.stderr
    assert profile_path.read_text(encoding="utf-8") == before  # untouched


def test_apply_creates_bak_before_write(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf"])
    profile_path = write_profile(
        home,
        {"qualifications": [{"id": "QUAL-001", "name": "X", "evidence_file": "知识库/资质证书/x.pdf"}]},
    )

    r = run(["apply", "--payload-file", "-"], home=home, stdin=json.dumps([minimal_item()]))
    assert r.returncode == 0

    bak = profile_path.with_suffix(".yaml.bak")
    assert bak.exists()
    bak_data = yaml.safe_load(bak.read_text(encoding="utf-8"))
    assert len(bak_data["qualifications"]) == 1  # pre-apply state


def test_apply_invalid_json(tmp_path):
    home = make_home(tmp_path)
    r = run(["apply", "--payload-file", "-"], home=home, stdin="not json")
    assert r.returncode == 5
    assert "JSON" in r.stderr


def test_apply_root_not_list(tmp_path):
    home = make_home(tmp_path)
    r = run(["apply", "--payload-file", "-"], home=home, stdin='{"a": 1}')
    assert r.returncode == 5
    assert "list" in r.stderr


# ---------- integration: scan -> apply -> scan ----------


def test_integration_idempotency(tmp_path):
    home = make_home(tmp_path)
    touch_pdfs(home, ["a.pdf", "b.pdf", "c.pdf"])

    # First scan: all 3 new
    r1 = run(["scan", "--type", "certs"], home=home)
    s1 = json.loads(r1.stdout)
    assert len(s1["new_files"]) == 3

    # Apply them
    payload = [minimal_item(file=f) for f in s1["new_files"]]
    r_apply = run(["apply", "--payload-file", "-"], home=home, stdin=json.dumps(payload))
    assert r_apply.returncode == 0

    # Second scan: all registered, zero new
    r2 = run(["scan", "--type", "certs"], home=home)
    s2 = json.loads(r2.stdout)
    assert s2["new_files"] == []
    assert s2["already_registered"] == 3


def test_integration_apply_then_scan_matches_evidence_path_format(tmp_path):
    """Regression guard: apply writes 知识库/资质证书/X.pdf, scan normalizes back to basename."""
    home = make_home(tmp_path)
    touch_pdfs(home, ["奇-怪.name.pdf"])

    r_apply = run(
        ["apply", "--payload-file", "-"],
        home=home,
        stdin=json.dumps([minimal_item(file="奇-怪.name.pdf")]),
    )
    assert r_apply.returncode == 0

    r_scan = run(["scan", "--type", "certs"], home=home)
    assert json.loads(r_scan.stdout)["new_files"] == []


# ---------- products helpers ----------


def make_products_dir(home: Path) -> Path:
    """Ensure 知识库/产品档案/ exists in home."""
    d = home / "知识库" / "产品档案"
    d.mkdir(parents=True, exist_ok=True)
    return d


def make_product_source(tmp_path: Path, files: list[str], dirname: str = "my-product") -> Path:
    """Create a source directory with fake files for product scan testing."""
    src = tmp_path / dirname
    src.mkdir(parents=True, exist_ok=True)
    for f in files:
        (src / f).write_bytes(b"fake content for testing\n")
    return src


def make_product_payload(
    facts_yaml: str = "name: Test Product\n",
    facts_md: str = "# Test Product\n",
    evidence_yaml: str = "sources: []\n",
    evidence_md: str = "# Evidence\n",
) -> dict:
    return {
        "facts_yaml": facts_yaml,
        "facts_md": facts_md,
        "evidence_yaml": evidence_yaml,
        "evidence_md": evidence_md,
    }


# ---------- products scan ----------


def test_scan_products_three_pdfs(tmp_path):
    home = make_home(tmp_path)
    make_products_dir(home)
    src = make_product_source(tmp_path, ["a.pdf", "b.pdf", "c.pdf"])

    r = run(["scan", "--type", "products", "--source", str(src)], home=home)

    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert len(out["files"]) == 3
    assert out["status"] == "new"
    assert out["slug"] == "my-product"
    names = [f["name"] for f in out["files"]]
    assert sorted(names) == ["a.pdf", "b.pdf", "c.pdf"]


def test_scan_products_source_not_exist(tmp_path):
    home = make_home(tmp_path)
    make_products_dir(home)

    r = run(["scan", "--type", "products", "--source", str(tmp_path / "nonexistent")], home=home)

    assert r.returncode == 3
    assert "产品材料目录不存在" in r.stderr


def test_scan_products_slug_exists(tmp_path):
    home = make_home(tmp_path)
    products = make_products_dir(home)
    slug_dir = products / "my-product"
    slug_dir.mkdir()
    (slug_dir / "facts.yaml").write_text("name: Old\n")

    src = make_product_source(tmp_path, ["a.pdf"])

    r = run(["scan", "--type", "products", "--source", str(src)], home=home)

    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["status"] == "exists"


def test_scan_products_slug_exists_force(tmp_path):
    home = make_home(tmp_path)
    products = make_products_dir(home)
    slug_dir = products / "my-product"
    slug_dir.mkdir()
    (slug_dir / "facts.yaml").write_text("name: Old\n")

    src = make_product_source(tmp_path, ["a.pdf"])

    r = run(["scan", "--type", "products", "--source", str(src), "--force"], home=home)

    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["status"] == "new"


def test_scan_products_mixed_formats(tmp_path):
    home = make_home(tmp_path)
    make_products_dir(home)
    src = make_product_source(
        tmp_path,
        ["doc.pdf", "sheet.xlsx", "slides.pptx", "notes.md", "image.png", "data.csv", "word.docx"],
    )

    r = run(["scan", "--type", "products", "--source", str(src)], home=home)

    assert r.returncode == 0
    out = json.loads(r.stdout)
    names = sorted(f["name"] for f in out["files"])
    # Only supported extensions: pdf, docx, xlsx, pptx, md
    assert names == ["doc.pdf", "notes.md", "sheet.xlsx", "slides.pptx", "word.docx"]


def test_scan_products_empty_dir(tmp_path):
    home = make_home(tmp_path)
    make_products_dir(home)
    src = make_product_source(tmp_path, [])

    r = run(["scan", "--type", "products", "--source", str(src)], home=home)

    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["files"] == []


# ---------- products apply ----------


def test_apply_products_valid_payload(tmp_path):
    home = make_home(tmp_path)
    make_products_dir(home)
    payload = make_product_payload()
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")

    r = run(
        ["apply", "--type", "products", "--slug", "test-prod", "--payload-file", str(payload_file)],
        home=home,
    )

    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["slug"] == "test-prod"
    assert sorted(out["files_written"]) == ["evidence.md", "evidence.yaml", "facts.md", "facts.yaml"]

    slug_dir = home / "知识库" / "产品档案" / "test-prod"
    assert slug_dir.exists()
    assert (slug_dir / "facts.yaml").exists()
    assert (slug_dir / "facts.md").exists()
    assert (slug_dir / "evidence.yaml").exists()
    assert (slug_dir / "evidence.md").exists()

    # facts.yaml should be parseable YAML
    facts = yaml.safe_load((slug_dir / "facts.yaml").read_text(encoding="utf-8"))
    assert facts["name"] == "Test Product"


def test_apply_products_slug_exists_no_force(tmp_path):
    home = make_home(tmp_path)
    products = make_products_dir(home)
    slug_dir = products / "existing-prod"
    slug_dir.mkdir()
    (slug_dir / "facts.yaml").write_text("name: Old\n")

    payload = make_product_payload()

    r = run(
        ["apply", "--type", "products", "--slug", "existing-prod", "--payload-file", "-"],
        home=home,
        stdin=json.dumps(payload),
    )

    assert r.returncode == 5
    assert "产品已存在" in r.stderr


def test_apply_products_slug_exists_force(tmp_path):
    home = make_home(tmp_path)
    products = make_products_dir(home)
    slug_dir = products / "existing-prod"
    slug_dir.mkdir()
    (slug_dir / "facts.yaml").write_text("name: Old\n")

    payload = make_product_payload(facts_yaml="name: New Product\n")

    r = run(
        ["apply", "--type", "products", "--slug", "existing-prod", "--payload-file", "-", "--force"],
        home=home,
        stdin=json.dumps(payload),
    )

    assert r.returncode == 0
    facts = yaml.safe_load((slug_dir / "facts.yaml").read_text(encoding="utf-8"))
    assert facts["name"] == "New Product"


def test_apply_products_missing_payload_key(tmp_path):
    home = make_home(tmp_path)
    make_products_dir(home)
    # Missing evidence_md
    bad_payload = {"facts_yaml": "x", "facts_md": "x", "evidence_yaml": "x"}

    r = run(
        ["apply", "--type", "products", "--slug", "bad-prod", "--payload-file", "-"],
        home=home,
        stdin=json.dumps(bad_payload),
    )

    assert r.returncode == 5
    assert "evidence_md" in r.stderr


def test_apply_products_invalid_json(tmp_path):
    home = make_home(tmp_path)
    make_products_dir(home)

    r = run(
        ["apply", "--type", "products", "--slug", "bad-prod", "--payload-file", "-"],
        home=home,
        stdin="not valid json{{{",
    )

    assert r.returncode == 5
    assert "JSON" in r.stderr


# ---------- products integration ----------


def test_products_integration_scan_apply_rescan(tmp_path):
    """Full cycle: scan source → apply payload → rescan → status exists."""
    home = make_home(tmp_path)
    make_products_dir(home)
    src = make_product_source(tmp_path, ["spec.pdf", "datasheet.docx"])

    # Step 1: scan
    r_scan1 = run(["scan", "--type", "products", "--source", str(src)], home=home)
    assert r_scan1.returncode == 0
    scan1 = json.loads(r_scan1.stdout)
    assert scan1["status"] == "new"
    assert len(scan1["files"]) == 2
    slug = scan1["slug"]

    # Step 2: apply
    payload = make_product_payload()
    r_apply = run(
        ["apply", "--type", "products", "--slug", slug, "--payload-file", "-"],
        home=home,
        stdin=json.dumps(payload),
    )
    assert r_apply.returncode == 0

    # Step 3: verify directory structure
    slug_dir = home / "知识库" / "产品档案" / slug
    assert slug_dir.is_dir()
    for fname in ["facts.yaml", "facts.md", "evidence.yaml", "evidence.md"]:
        assert (slug_dir / fname).exists(), f"Missing {fname}"

    # Step 4: rescan → status "exists"
    r_scan2 = run(["scan", "--type", "products", "--source", str(src)], home=home)
    assert r_scan2.returncode == 0
    scan2 = json.loads(r_scan2.stdout)
    assert scan2["status"] == "exists"
