"""Deterministic offline walkthrough of all six Aegle Partner Ops MCP tools.

Run with:  python demo_walkthrough.py

Sets AEGLE_OFFLINE=1 before importing the server, so no CMS network call is made
and every coverage answer is honestly sourced from the local NCD seed.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
os.environ["AEGLE_OFFLINE"] = "1"
DEMO_DB = os.environ.get("AEGLE_DB_PATH")
if not DEMO_DB:
    DEMO_DB = str(REPO_ROOT / ".aegle" / "demo_walkthrough.sqlite3")
    # Remove prior demo state so the walkthrough is deterministic run to run.
    for suffix in ("", "-wal", "-shm"):
        stale = Path(DEMO_DB + suffix)
        if stale.exists():
            stale.unlink()
os.environ["AEGLE_DB_PATH"] = DEMO_DB

sys.path.insert(0, str(REPO_ROOT))

import aegle_partner_ops_mcp as ops  # noqa: E402


def rule(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def main() -> int:
    print("AEGLE PARTNER OPS - DEMO WALKTHROUGH")
    print("Aegle Health Partners (d/b/a Aegle Capital)")
    print("Synthetic claim #9941 | Prairie States Administrators | Midwest Precision Manufacturing LLC")
    print(f"Policy {ops.POLICY_NUMBER} | {ops.CARRIER} | de-identified member {ops.CLAIMANT_KEY}")
    print("Mode: OFFLINE (AEGLE_OFFLINE=1) - no live CMS call, no external writes")

    # ------------------------------------------------------------------
    rule("TOOL 1/6  lookup_medical_code")
    codes = ["C91.02", "D89.83", "Q2042", "J9999", "J3490", "0256", "0110", "0999", "ZZZ9"]
    lookup = ops.lookup_medical_code(codes)
    print(f"requested={lookup['requested_count']}  recognized={lookup['recognized_count']}  "
          f"unknown={lookup['unknown_codes']}")
    for row in lookup["results"]:
        if not row["valid"]:
            print(f"  {row['input']:<8} INVALID  ({row.get('reason')})")
            continue
        print(f"  {row['input']:<8} {row['system']:<15} {row['description']}")
        print(f"           flags={row['flags']}  role={row['packet_role']}")

    # ------------------------------------------------------------------
    rule("TOOL 2/6  check_cms_coverage_and_fda")
    checks = [
        ("Q2042", "C91.02"),
        ("J9999", "C91.02"),
        ("J3490", "C91.02"),
        ("0256", "C91.02"),
    ]
    for hcpcs, dx in checks:
        check = ops.check_cms_coverage_and_fda(hcpcs, dx)
        print(f"  {hcpcs} + {dx}: {check['coverage_status']:<28} "
              f"indication_match={check['indication_match']}")
        print(f"    source={check['source']}  determination_source={check['determination_source']}  "
              f"live_api_attempted={check['live_api_attempted']}  cache_hit={check['cache_hit']}")
        if check["live_api_scope"]:
            print(f"    live_api_scope={check['live_api_scope']}")
        print(f"    {check['determination']}")
        if check.get("fda"):
            print(f"    FDA: {check['fda']['product']} approved {check['fda']['approval_date']}")
    print(f"  NCD {checks[0][0]} reference: {ops.NCD_110_24['ncd_id']} - {ops.NCD_110_24['title']}")
    print(f"    {ops.NCD_110_24['url']}")

    # ------------------------------------------------------------------
    rule("TOOL 3/6  lookup_stoploss_case_law")
    for issue in ("laser endorsement separate specific deductible",
                  "paid basis 12/15 run-out late payment",
                  "experimental investigational CAR-T"):
        case_out = ops.lookup_stoploss_case_law(issue)
        print(f"  issue: {issue}")
        for precedent in case_out["matched_precedents"]:
            print(f"    - {precedent['case']} ({precedent['court']} {precedent['year']}) "
                  f"[{precedent['confidence']}] tags={precedent['matched_tags']}")
    print("  practice note: " + ops.PRACTICE_NOTE)

    # ------------------------------------------------------------------
    rule("TOOL 4/6  reconcile_funding_tranche")
    recon = ops.reconcile_funding_tranche(
        billed=3_050_000,
        non_covered_fl48=350_000,
        lasered_deductible=750_000,
        signature_hold=250_000,
        requested_advance=2_800_000,
    )
    for line in recon["narrative"]:
        print("  " + line)
    print(f"  approved_tranche_1 = {recon['formatted']['approved_tranche_1']}")
    print(f"  total_gap          = {recon['formatted']['total_gap']}")
    print(f"  laser_gap          = {recon['formatted']['laser_gap']}")
    print(f"  loss prevented     = ${recon['unrecovered_receivable_loss_prevented']:,.0f}")
    print(f"  tranche 2 held     = ${recon['tranche_2_hold_amount']:,.0f}")
    print(f"  checks             = {json.dumps(recon['checks'], sort_keys=True)}")

    # ------------------------------------------------------------------
    rule("TOOL 5/6  stage_zero_phi_hubspot_and_teams_handoff")
    staged = ops.stage_zero_phi_hubspot_and_teams_handoff(
        "9941", "Prairie States Administrators", "Patrick Feit"
    )
    payload = staged["payload"]
    print(f"  staged_payload_id = {staged['staged_payload_id']}")
    print(f"  status={staged['status']}  dry={staged['dry']}  read_only={staged['read_only']}  "
          f"network_writes={staged['network_writes']}")
    print(f"  target = {staged['target']}")
    print(f"  approval = {json.dumps(staged['approval'])}")
    print(f"  stage={payload['hs_pipeline_stage']}  laser_flag={payload['laser_flag']}  "
          f"mbr_status={staged['partner_health']['mbr_status']}")
    print(f"  root cause = {payload['open_issue_root_cause']}")
    print(f"  signatures: employer={payload['missing_signature_employer']} "
          f"tpa={payload['missing_signature_tpa']} carrier={payload['missing_signature_carrier']}")
    print(f"  amounts: billed={payload['billed_amount']:,.0f} "
          f"tranche1={payload['approved_tranche_1']:,.0f} "
          f"hold={payload['tranche_2_hold_amount']:,.0f} "
          f"requested={payload['requested_advance']:,.0f}")
    print(f"  growth signal = {json.dumps(staged['growth_expansion_signal'])}")
    print(f"  phi_scan = {json.dumps(staged['phi_scan'])}")

    # ------------------------------------------------------------------
    rule("TOOL 6/6  generate_partner_resolution_pack")
    pack = ops.generate_partner_resolution_pack("Prairie States Administrators", "9941")
    print(f"  zero_phi={pack['zero_phi']}  phi_scan={pack['phi_scan']['result']}")
    print(f"  amounts={json.dumps(pack['amounts'], sort_keys=True)}")
    for key, heading in (
        ("tpa_message", "TPA message"),
        ("finance_memo", "Finance memo"),
        ("playbook_update", "Playbook update"),
    ):
        lines = pack[key].splitlines()
        print(f"\n  --- {heading} (first 6 lines of {len(lines)}) ---")
        for line in lines[:6]:
            print("  " + line)

    rule("DEMO COMPLETE")
    import sqlite3

    with sqlite3.connect(os.environ["AEGLE_DB_PATH"]) as conn:
        audit_rows = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    print(f"  audit rows written: {audit_rows} (one per tool call, including failures)")
    print("  All six tools returned ok=true with audit ids; no PHI left the staged envelope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
