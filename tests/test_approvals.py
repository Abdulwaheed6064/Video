"""tools/approvals.py: digest binding, expiry, compliance PASS, owner approval, consume once."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.approvals import main
from tools.common import load_yaml, sha256_path

SLUG = "_demo-barber"
BATCH = "gbp/changes/2026-11-06-batch.yaml"
REPORT = "reviews/compliance/2026-11-06-batch-2026-11-06.md"
NOW = "2026-11-06T10:00:00-05:00"
APPROVAL_ID = "A2026-11-06-gbp-apply-batch"

BATCH_TEXT = """schema_version: 1
synthetic: true
client: _demo-barber
date: 2026-11-06
changes:
  - field: description
    current: ""
    proposed: "Skin fades and beard trims in Bradford. Book online or call."
    reason: "Description missing (synthetic audit)"
    fact_refs: [F005, F006]
    ui_path: "Edit profile > About > Description"
    risk: low
  - field: hours
    current: null
    proposed: "Tue-Fri 10:00-19:00; Sat 09:00-17:00; Sun-Mon closed"
    reason: "Hours missing"
    fact_refs: [F004]
    ui_path: "Edit profile > Hours"
    risk: low
"""


def write_report(client: Path, digest: str, result: str = "PASS", file: str = BATCH) -> None:
    path = client / REPORT
    path.write_text(
        f"---\nresult: {result}\nsha256: {digest}\nfile: {file}\ndate: 2026-11-06\nreviewer: test\n---\n"
        f"# Compliance review\n\nRESULT: {result}\n\nNo issues.\n",
        encoding="utf-8",
    )


@pytest.fixture
def client(root: Path) -> Path:
    c = root / "clients" / SLUG
    (c / BATCH).write_text(BATCH_TEXT, encoding="utf-8")
    write_report(c, sha256_path(c / BATCH))
    return c


def run(root: Path, *args: str) -> int:
    return main(["--root", str(root), *args])


def request(root: Path, *extra: str) -> int:
    return run(root, "request", "--client", SLUG, "--action", "gbp_apply_batch", "--artifact", BATCH,
               "--compliance-report", REPORT, "--requested-by", "agent:gbp-optimizer", "--now", NOW, *extra)


def approve_with_owner(root: Path, now: str = NOW) -> int:
    return run(root, "approve", APPROVAL_ID, "--by", "A", "--owner-by", "owner via WhatsApp",
               "--owner-at", "2026-11-06T09:30:00-05:00", "--now", now)


def approval(client: Path) -> dict:
    return load_yaml(client / "approvals" / f"{APPROVAL_ID}.yaml")


def test_happy_path_request_approve_verify_consume(root: Path, client: Path) -> None:
    assert request(root) == 0
    a = approval(client)
    assert a["status"] == "requested" and a["synthetic"] is True
    assert a["artifact_sha256"] == sha256_path(client / BATCH)
    assert a["owner_approval"]["required"] is True
    assert approve_with_owner(root) == 0
    assert run(root, "verify", APPROVAL_ID, "--now", NOW) == 0
    assert run(root, "consume", APPROVAL_ID, "--by", "A", "--fields", "description", "--now", NOW) == 0
    a = approval(client)
    assert a["status"] == "consumed" and a["applied_fields"] == ["description"]
    log = (client / "gbp" / "applied.log").read_text(encoding="utf-8").splitlines()
    assert len(log) == 1 and log[0].split("\t")[4] == "description"


def test_approved_file_validates(root: Path, client: Path) -> None:
    from tools.validate import validate_client_dir

    assert request(root) == 0
    assert approve_with_owner(root) == 0
    assert validate_client_dir(client).errors == []


def test_approval_invalid_after_artifact_edit(root: Path, client: Path) -> None:
    assert request(root) == 0
    assert approve_with_owner(root) == 0
    (client / BATCH).write_text(BATCH_TEXT.replace("Book online", "Book now"), encoding="utf-8")
    assert run(root, "verify", APPROVAL_ID, "--now", NOW) == 1
    assert run(root, "consume", APPROVAL_ID, "--by", "A", "--now", NOW) == 1
    assert approval(client)["status"] == "approved"


def test_expired_approval_rejected(root: Path, client: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert request(root, "--expires-days", "3") == 0
    assert approve_with_owner(root) == 0
    late = "2026-11-10T09:00:00-05:00"
    assert run(root, "verify", APPROVAL_ID, "--now", late) == 1
    assert "expired on 2026-11-09" in capsys.readouterr().out
    assert run(root, "consume", APPROVAL_ID, "--by", "A", "--now", late) == 1


def test_cannot_approve_after_expiry(root: Path, client: Path) -> None:
    assert request(root) == 0
    assert approve_with_owner(root, now="2026-11-12T09:00:00-05:00") == 1


def test_consume_twice_rejected(root: Path, client: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert request(root) == 0
    assert approve_with_owner(root) == 0
    assert run(root, "consume", APPROVAL_ID, "--by", "A", "--now", NOW) == 0
    assert run(root, "consume", APPROVAL_ID, "--by", "A", "--now", NOW) == 1
    assert "already consumed" in capsys.readouterr().out
    assert len((client / "gbp" / "applied.log").read_text(encoding="utf-8").splitlines()) == 2


def test_missing_compliance_pass_rejected(root: Path, client: Path) -> None:
    (client / REPORT).unlink()
    assert request(root) == 1
    assert not (client / "approvals" / f"{APPROVAL_ID}.yaml").exists()


def test_compliance_fail_rejected(root: Path, client: Path) -> None:
    write_report(client, sha256_path(client / BATCH), result="FAIL")
    assert request(root) == 1


def test_compliance_for_other_digest_rejected(root: Path, client: Path) -> None:
    write_report(client, "0" * 64)
    assert request(root) == 1


def test_compliance_report_removed_after_request(root: Path, client: Path) -> None:
    assert request(root) == 0
    assert approve_with_owner(root) == 0
    (client / REPORT).unlink()
    assert run(root, "verify", APPROVAL_ID, "--now", NOW) == 1


def test_owner_approval_missing_when_required(root: Path, client: Path) -> None:
    assert request(root) == 0
    assert run(root, "approve", APPROVAL_ID, "--by", "A", "--now", NOW) == 1
    assert approval(client)["status"] == "requested"


def test_owner_not_required_when_overridden(root: Path, client: Path) -> None:
    assert request(root, "--owner-required", "no") == 0
    assert run(root, "approve", APPROVAL_ID, "--by", "A", "--now", NOW) == 0
    assert run(root, "verify", APPROVAL_ID, "--now", NOW) == 0


def test_verify_requested_but_not_approved(root: Path, client: Path) -> None:
    assert request(root) == 0
    assert run(root, "verify", APPROVAL_ID, "--now", NOW) == 1


def test_rejected_cannot_be_consumed(root: Path, client: Path) -> None:
    assert request(root) == 0
    assert run(root, "reject", APPROVAL_ID, "--by", "A", "--reason", "owner wants other wording",
               "--now", NOW) == 0
    assert run(root, "consume", APPROVAL_ID, "--by", "A", "--now", NOW) == 1


def test_consume_unknown_field_refused(root: Path, client: Path) -> None:
    assert request(root) == 0
    assert approve_with_owner(root) == 0
    assert run(root, "consume", APPROVAL_ID, "--by", "A", "--fields", "name", "--now", NOW) == 1
    assert approval(client)["status"] == "approved"


def test_artifact_outside_client_refused(root: Path, client: Path) -> None:
    assert run(root, "request", "--client", SLUG, "--action", "post_publish", "--artifact", "../../x.md",
               "--compliance-report", REPORT, "--requested-by", "agent:content", "--now", NOW) in {1, 2}


def test_directory_digest_changes_on_edit(tmp_path: Path) -> None:
    d = tmp_path / "kit"
    d.mkdir()
    (d / "a.txt").write_text("one", encoding="utf-8")
    first = sha256_path(d)
    (d / "b.txt").write_text("two", encoding="utf-8")
    assert sha256_path(d) != first


def test_hash_cli(client: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hash", str(client / BATCH)]) == 0
    assert capsys.readouterr().out.strip() == sha256_path(client / BATCH)
