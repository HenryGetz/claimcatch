"""Offline pytest suite for the ClaimCatch MCP server.

No live network: CLAIMCATCH_OFFLINE=1 is forced and each test gets its own SQLite file.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("CLAIMCATCH_OFFLINE", "1")

import claimcatch_mcp as ops  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "claimcatch_test.sqlite3"
    monkeypatch.setenv("CLAIMCATCH_DB_PATH", str(db_path))
    monkeypatch.setenv("CLAIMCATCH_OFFLINE", "1")
    ops._INITIALIZED.discard(str(db_path.resolve()))
    ops._ensure_db()
    return db_path


def row_count(db_path: Path, table: str) -> int:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def result_for(lookup: dict, raw: str) -> dict:
    for item in lookup["results"]:
        if item["input"] == raw:
            return item
    raise AssertionError(f"{raw} not present in results")


# ---------------------------------------------------------------------------
# Tool 1 - medical code lookup
# ---------------------------------------------------------------------------


def test_lookup_medical_code_known():
    out = ops.lookup_medical_code(["C91.02", "Q2042", "0256", "0110"])
    assert out["ok"] is True
    assert out["audit_id"].startswith("aud_")
    assert out["requested_count"] == 4
    assert out["recognized_count"] == 4
    assert out["unknown_codes"] == []

    q2042 = result_for(out, "Q2042")
    assert q2042["valid"] is True
    assert q2042["system"] == "HCPCS"
    assert "fda_labeled" in q2042["flags"]
    assert "ncd_110.24" in q2042["flags"]

    rev = result_for(out, "0256")
    assert rev["system"] == "UB-04 revenue"
    assert "investigational" in rev["flags"]

    icd = result_for(out, "C91.02")
    assert icd["system"] == "ICD-10-CM"
    assert "leukemia" in icd["description"].lower()


def test_lookup_medical_code_unknown_and_mixed():
    out = ops.lookup_medical_code([" c91.02 ", "Q2042", "ZZZ9", "99999"])
    assert out["ok"] is True
    assert out["requested_count"] == 4
    assert out["recognized_count"] == 2
    assert out["unknown_codes"] == ["ZZZ9", "99999"]
    assert result_for(out, " c91.02 ")["code"] == "C91.02"
    assert result_for(out, "ZZZ9")["valid"] is False
    assert result_for(out, "99999")["reason"] == "unrecognized_format"


def test_lookup_medical_code_rejects_bad_input():
    out = ops.lookup_medical_code([])
    assert out["ok"] is False
    assert "audit_id" in out


# ---------------------------------------------------------------------------
# Tool 2 - CMS coverage and FDA
# ---------------------------------------------------------------------------


def test_q2042_with_b_all_is_covered_offline():
    out = ops.check_cms_coverage_and_fda("q2042", "c91.02")
    assert out["ok"] is True
    assert out["coverage_status"] == "covered"
    assert out["indication_match"] is True
    assert out["ncd"]["ncd_id"] == "110.24"
    assert "cms.gov" in out["ncd"]["url"]
    assert out["fda"]["approval_date"] == "2017-08-30"
    assert "25" in out["fda"]["labeled_population"]
    assert out["source"] == "local_ncd_seed"
    assert out["determination_source"] == "local_ncd_seed"
    assert out["live_api_scope"] is None
    assert out["live_api_attempted"] is False
    assert out["cache_hit"] is False
    assert out["live_api_error"]
    assert out["reasons"]


def test_q2042_outside_label_is_not_covered():
    out = ops.check_cms_coverage_and_fda("Q2042", "J18.9")
    assert out["ok"] is True
    assert out["coverage_status"] == "not_covered_outside_label"
    assert out["indication_match"] is False


def test_j9999_is_non_covered():
    out = ops.check_cms_coverage_and_fda("J9999", "C91.02")
    assert out["ok"] is True
    assert out["coverage_status"] == "non_covered"
    assert any("unclassified" in reason.lower() for reason in out["reasons"])


def test_j3490_with_b_all_is_off_label_non_covered():
    out = ops.check_cms_coverage_and_fda("J3490", "C91.02")
    assert out["ok"] is True
    assert out["coverage_status"] == "non_covered"
    assert "off-label" in out["determination"].lower()


def test_revenue_0256_is_non_covered():
    out = ops.check_cms_coverage_and_fda("0256", "C91.02")
    assert out["ok"] is True
    assert out["coverage_status"] == "non_covered"
    assert "investigational" in out["determination"].lower()


def test_unknown_coverage_code_fails_cleanly():
    out = ops.check_cms_coverage_and_fda("J0000", "C91.02")
    assert out["ok"] is False
    assert out["coverage_status"] == "unknown_code"
    assert out["audit_id"].startswith("aud_")


def test_coverage_live_success_is_cached(monkeypatch):
    monkeypatch.setattr(ops, "_offline", lambda: False)
    monkeypatch.setattr(
        ops,
        "_live_ncd_lookup",
        lambda url: {"ok": True, "http_status": 200, "error": None, "record": ops._ncd_record()},
    )
    first = ops.check_cms_coverage_and_fda("Q2042", "C91.02")
    assert first["ok"] is True
    assert first["source"] == "cms_api_live"
    assert first["determination_source"] == "local_ncd_seed"
    assert "metadata" in first["live_api_scope"].lower()
    assert first["live_api_attempted"] is True
    assert first["cache_hit"] is False

    second = ops.check_cms_coverage_and_fda("Q2042", "C91.02")
    assert second["source"] == "cms_api_cache"
    assert second["determination_source"] == "local_ncd_seed"
    assert "metadata" in second["live_api_scope"].lower()
    assert second["cache_hit"] is True
    assert second["live_api_attempted"] is False


def test_coverage_live_failure_falls_back_honestly(monkeypatch):
    monkeypatch.setattr(ops, "_offline", lambda: False)
    monkeypatch.setattr(
        ops,
        "_live_ncd_lookup",
        lambda url: {"ok": False, "http_status": None, "error": "ReadTimeout: boom"},
    )
    out = ops.check_cms_coverage_and_fda("Q2042", "C91.02")
    assert out["ok"] is True
    assert out["source"] == "local_ncd_seed"
    assert out["live_api_attempted"] is True
    assert "boom" in out["live_api_error"]
    assert out["cache_hit"] is False


# ---------------------------------------------------------------------------
# Tool 3 - case law
# ---------------------------------------------------------------------------


def test_case_law_laser_matches_trustmark():
    out = ops.lookup_stoploss_case_law("laser endorsement separate specific deductible")
    assert out["ok"] is True
    assert out["matched_precedents"]
    first = out["matched_precedents"][0]
    assert first["case"] == "Trustmark Ins. Co. v. Citizens"
    assert first["citation_status"] == ops.CITATION_STATUS
    assert "laser" in first["matched_tags"]


def test_case_law_paid_basis_12_15_matches_run_out_cases():
    out = ops.lookup_stoploss_case_law("paid basis 12/15 run-out late payment")
    names = [item["case"] for item in out["matched_precedents"]]
    assert "Blue Cross of Idaho v. Scentsy" in names
    assert "BCBS NC v. Technibilt" in names


def test_case_law_experimental_matches_parsons():
    out = ops.lookup_stoploss_case_law("experimental investigational CAR-T exclusion")
    names = [item["case"] for item in out["matched_precedents"]]
    assert "Parsons" in names
    assert "no verified precedent" in out["practice_note"].lower()


def test_case_law_unmatched_returns_empty_list():
    out = ops.lookup_stoploss_case_law("zebra quantum flux")
    assert out["ok"] is True
    assert out["matched_precedents"] == []
    assert out["suggested_query_terms"]


# ---------------------------------------------------------------------------
# Tool 4 - reconciliation
# ---------------------------------------------------------------------------


def test_reconcile_demo_is_exact():
    out = ops.reconcile_funding_tranche(
        billed=3_050_000,
        non_covered_fl48=350_000,
        lasered_deductible=750_000,
        signature_hold=250_000,
        requested_advance=2_800_000,
    )
    assert out["ok"] is True
    assert out["eligible_billed"] == 2_700_000
    assert out["reimbursable_before_hold"] == 1_950_000
    assert out["approved_tranche_1"] == 1_700_000
    assert out["total_gap"] == 1_100_000
    assert out["laser_gap"] == 500_000
    assert out["trap_breakdown"]["laser_gap"] == 500_000
    assert out["trap_breakdown"]["non_covered_fl48"] == 350_000
    assert out["trap_breakdown"]["signature_hold"] == 250_000
    assert out["trap_breakdown"]["total"] == 1_100_000
    assert out["unrecovered_receivable_loss_prevented"] == 1_100_000
    assert out["tranche_2_hold_amount"] == 250_000
    for key in (
        "equation_balances",
        "gap_equals_traps",
        "approved_not_above_eligible",
        "all_inputs_non_negative",
        "lasered_deductible_at_or_above_base",
    ):
        assert out["checks"][key] is True, key
    narrative = " ".join(out["narrative"])
    assert "$500,000" in narrative
    assert "$1,100,000" in narrative


def test_reconcile_alternate_numbers_invariant():
    out = ops.reconcile_funding_tranche(
        billed=1_200_000,
        non_covered_fl48=100_000,
        lasered_deductible=400_000,
        signature_hold=50_000,
        requested_advance=950_000,
    )
    assert out["ok"] is True
    assert out["eligible_billed"] == 1_100_000
    assert out["reimbursable_before_hold"] == 700_000
    assert out["approved_tranche_1"] == 650_000
    assert out["total_gap"] == 300_000
    assert out["laser_gap"] == 150_000
    assert out["checks"]["gap_equals_traps"] is True
    assert out["trap_breakdown"]["total"] == 300_000


def test_reconcile_rejects_negative_input():
    out = ops.reconcile_funding_tranche(-1, 0, 250_000, 0, 100_000)
    assert out["ok"] is False
    assert out["validation_errors"]


def test_reconcile_records_laser_below_base_without_hard_fail():
    out = ops.reconcile_funding_tranche(500_000, 0, 100_000, 0, 400_000)
    assert out["ok"] is True
    assert out["deductible_check"]["meets_base"] is False
    assert out["checks"]["lasered_deductible_at_or_above_base"] is False


# ---------------------------------------------------------------------------
# Tool 5 - zero-PHI staging
# ---------------------------------------------------------------------------


def test_staging_envelope_is_dry_and_zero_phi():
    out = ops.stage_zero_phi_hubspot_and_teams_handoff(
        "9941", "Prairie States Administrators"
    )
    assert out["ok"] is True
    assert out["dry"] is True
    assert out["read_only"] is True
    assert out["status"] == "PENDING_APPROVAL"
    assert out["target"] == "/crm/v3/objects/catastrophic_claim"
    assert out["staged_payload_id"].startswith("stg_")
    assert out["idempotency_key"].startswith("idem_")
    assert out["approval"]["required"] is True
    assert out["approval"]["role"] == "VP, Client Partnerships - Growth"
    assert out["approval"]["action"] == "single_click"
    assert out["network_writes"] == 0

    payload = out["payload"]
    assert payload["claim_id"] == "9941"
    assert payload["claimant_key"] == "MPM-9941-07"
    assert payload["hs_pipeline_stage"] == "adjudication_hold_laser_flagged"
    assert payload["laser_flag"] == "flagged"
    assert payload["missing_signature_employer"] is True
    assert payload["missing_signature_tpa"] is False
    assert payload["missing_signature_carrier"] is True
    assert payload["open_issue_root_cause"] == "Unflagged Renewal Laser + Missing CFO Counter-Sign"
    assert payload["billed_amount"] == 3_050_000
    assert payload["fl48_non_covered_amount"] == 350_000
    assert payload["lasered_deductible"] == 750_000
    assert payload["approved_tranche_1"] == 1_700_000
    assert payload["tranche_2_hold_amount"] == 250_000
    assert payload["requested_advance"] == 2_800_000
    assert payload["next_action"]

    blob = json.dumps(payload)
    for forbidden in ("C91", "D89", "2017-08-30", "2026-08", "MRN", "SSN", "DOB", "A.R."):
        assert forbidden not in blob, forbidden

    scan = out["phi_scan"]
    assert scan["result"] == "PASS"
    assert scan["phi_detected"] is False
    assert scan["phi_field_count"] == 0
    assert scan["fields_stripped"] == []

    assert out["partner_health"]["funding_turnaround_hours"] == 24
    assert out["partner_health"]["mbr_status"] == "AT_RISK"
    assert out["partner_health"]["open_issue_root_cause"] == (
        "Unflagged Renewal Laser + Missing CFO Counter-Sign"
    )
    assert out["growth_expansion_signal"]["signal"] == "LASER_SHOCK"
    assert out["growth_expansion_signal"]["exposure"] == 500_000
    assert out["growth_expansion_signal"]["broker_follow_up"] is True


def test_staging_persists_and_ids_are_unique(isolated_db):
    first = ops.stage_zero_phi_hubspot_and_teams_handoff(
        "9941", "Prairie States Administrators"
    )
    second = ops.stage_zero_phi_hubspot_and_teams_handoff(
        "9941", "Prairie States Administrators"
    )
    assert first["staged_payload_id"] != second["staged_payload_id"]
    assert row_count(isolated_db, "staged_payloads") == 2

    with sqlite3.connect(isolated_db) as conn:
        row = conn.execute(
            "SELECT claim_id, status, payload_json FROM staged_payloads WHERE staged_payload_id = ?",
            (first["staged_payload_id"],),
        ).fetchone()
    assert row is not None
    assert row[0] == "9941"
    assert row[1] == "PENDING_APPROVAL"
    assert json.loads(row[2])["claimant_key"] == "MPM-9941-07"


def test_staging_redacts_phi_in_partner_text():
    out = ops.stage_zero_phi_hubspot_and_teams_handoff(
        "9941", "Prairie States Administrators C91.02"
    )
    assert out["ok"] is True
    scan = out["phi_scan"]
    assert scan["result"] == "PASS"
    assert scan["phi_detected"] is False
    assert scan["phi_field_count"] == 0
    assert scan["fields_stripped"]
    assert scan["input_redactions"] == scan["fields_stripped"]
    assert scan["redaction_count"] >= 1
    assert "C91.02" not in json.dumps(out["payload"])
    assert "[REDACTED]" in out["payload"]["partner_tpa"]


def test_payload_phi_scan_walks_nested_structures():
    findings = ops._scan_payload(
        {
            "top": "clean",
            "nested": {"dx": "C91.02"},
            "items": ["J18.9"],
        }
    )
    fields = {item["field"] for item in findings}
    assert "nested.dx" in fields
    assert "items[0]" in fields


def test_staged_sections_contain_no_phi_tokens():
    out = ops.stage_zero_phi_hubspot_and_teams_handoff(
        "9941", "Prairie States Administrators"
    )
    blob = json.dumps(
        {
            "payload": out["payload"],
            "partner_health": out["partner_health"],
            "growth_expansion_signal": out["growth_expansion_signal"],
        }
    )
    for token in ("C91", "D89", "D61", "D70", "N17", "J18", "MRN", "SSN", "DOB", "A.R."):
        assert token not in blob, token
    date_pattern = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b")
    assert not date_pattern.search(blob), "date found in staged sections"


# ---------------------------------------------------------------------------
# Tool 6 - partner resolution pack
# ---------------------------------------------------------------------------


def test_resolution_pack_is_zero_phi_with_exact_amounts():
    out = ops.generate_partner_resolution_pack("Prairie States Administrators", "9941")
    assert out["ok"] is True, out
    assert out["zero_phi"] is True
    assert out["phi_scan"]["result"] == "PASS"

    for key in ("tpa_message", "finance_memo", "playbook_update"):
        assert isinstance(out[key], str) and out[key].strip()

    combined = "\n".join(out[key] for key in ("tpa_message", "finance_memo", "playbook_update"))
    for amount in (
        "$1,700,000",
        "$250,000",
        "$350,000",
        "$500,000",
        "$850,000",
        "$1,100,000",
        "$2,800,000",
    ):
        assert amount in combined, amount

    assert "Subject:" in out["tpa_message"]
    assert "5 business days" in out["tpa_message"]
    assert "released for disbursement" not in out["tpa_message"]
    assert "subject to release by Finance" in out["tpa_message"]
    assert "draft, not an authorization" in out["finance_memo"]
    assert "Approve and release $1,700,000" in out["finance_memo"]
    assert "double approval" in out["finance_memo"].lower()
    assert "Patrick Feit" in out["playbook_update"]
    assert "acceptance criteria" in out["playbook_update"].lower()

    icd_pattern = re.compile(r"\b[A-TV-Z]\d{2}(?:\.[0-9A-Z]{1,4})?\b")
    date_pattern = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b")
    for key in ("tpa_message", "finance_memo", "playbook_update"):
        text = out[key]
        assert not icd_pattern.search(text), f"ICD code found in {key}"
        assert not date_pattern.search(text), f"service date found in {key}"
        assert "C91" not in text


def test_resolution_pack_rejects_invalid_claim_id():
    out = ops.generate_partner_resolution_pack("Prairie States Administrators", "C91.02")
    assert out["ok"] is False
    assert out["audit_id"].startswith("aud_")


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def test_every_tool_call_writes_one_audit_row(isolated_db):
    before = row_count(isolated_db, "audit_log")

    calls = [
        ops.lookup_medical_code(["C91.02", "Q2042"]),
        ops.check_cms_coverage_and_fda("Q2042", "C91.02"),
        ops.lookup_stoploss_case_law("laser"),
        ops.reconcile_funding_tranche(3_050_000, 350_000, 750_000, 250_000, 2_800_000),
        ops.stage_zero_phi_hubspot_and_teams_handoff("9941", "Prairie States Administrators"),
        ops.generate_partner_resolution_pack("Prairie States Administrators", "9941"),
    ]
    assert all(call["audit_id"].startswith("aud_") for call in calls)

    validation_error = ops.lookup_medical_code([])
    assert validation_error["ok"] is False

    after = row_count(isolated_db, "audit_log")
    assert after - before == 7

    with sqlite3.connect(isolated_db) as conn:
        rows = conn.execute(
            "SELECT audit_id, tool, ok FROM audit_log ORDER BY rowid"
        ).fetchall()
    audit_ids = {row[0] for row in rows}
    for call in calls:
        assert call["audit_id"] in audit_ids
    assert validation_error["audit_id"] in audit_ids
    assert {row[1] for row in rows} >= {
        "lookup_medical_code",
        "check_cms_coverage_and_fda",
        "lookup_stoploss_case_law",
        "reconcile_funding_tranche",
        "stage_zero_phi_hubspot_and_teams_handoff",
        "generate_partner_resolution_pack",
    }
    assert any(row[2] == 0 for row in rows)
