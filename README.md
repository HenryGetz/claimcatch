# ClaimCatch

ClaimCatch — partner-side stop-loss claim operations for Aegle Capital.

Live demo: https://henrygetz.github.io/claimcatch/

> **Synthetic data.** Claim `9941`, policy `MPM-SL-2026-0147`, and every adjudication figure in this repo are fabricated for demonstration. No real member, employer, TPA, carrier, or claim data is included. Nothing here is clinical, legal, or coverage advice.

---

## What it is

A high-speed claim-triage workspace with humans in the loop. ClaimCatch parses a claim packet, attributes every dollar of the funding gap, and produces a **draft** advance for human sign-off. It does not wire funds, and no output is released without a reviewer.

The demo runs on static files. The browser parses PDFs locally; the six FastMCP tools run separately over stdio for the LibreChat prompt.

---

## Current features

### Real PDF intake, parsed locally

- Multiple PDFs per packet, with page count, extracted text, and a combined SHA-256 shown in the intake panel.
- Invalid files are rejected with a message: non-PDF names, missing `%PDF-` headers, and parser-unavailable states.
- A first-page text preview is capped at 1,200 characters and stays in the browser session.
- PDF bytes are never uploaded; parsing runs through the vendored PDF.js build in `web/vendor/pdfjs/`.
- **Simulate Upload: Claim #9941 Packet (4 PDFs · 312 Pages)** loads the demo packet without a file.
- Adjudication figures remain the synthetic claim #9941 values regardless of which PDF is dropped.

### Workbench

- Hero banner reads the advance as a **draft for sign-off** ($1,700,000), not a release.
- Trap attribution of the $1,100,000 gap: $500,000 Endorsement L-1 laser, $350,000 FL48, $250,000 signature hold.
- Cure checkboxes for the Employer CFO signature and carrier countersignature move the draft from $1,700,000 to $1,950,000, set the hold to $0, and mark Tranche 2 ready for human sign-off. Unchecking reverses the state.
- Evidence drawer renders policy, UB-04, and TPA pages with highlighted clauses, plus a toggle to the extracted Markdown with page and bbox metadata.
- Resolution panel: cure checklist, **Drafted Outbound Pack** (TPA cure notice, finance memo, 1/1 playbook update), and a staged HubSpot `catastrophic_claim` record with a raw JSON toggle.
- Actions open confirmation dialogs and record receipts plus audit timestamps. HubSpot remains a staged, read-only record.

### Ask Packet

A topbar drawer answers from the indexed packet with three starter prompts: policy No-New-Laser / anti-assignment, Kymriah vs CD22 coverage, and a zero-PHI Teams update. Answers show the MCP tool pill used and link citations into the evidence drawer (Policy p. 3, Policy p. 7, UB-04, TPA request). Free-typed questions route by intent. The drawer is read-only Q&A; it does not change packet state or figures.

### How It Works

The fifth nav destination covers the architecture: serverless BAA + ZDR OCR, Fireworks reasoning, authoritative verification sources, the human review gate, draft outputs, a locked-vs-cleared trust boundary, three rollout phases, and an FAQ.

---

## Repo layout

```
claimcatch/
├── claim_packet_9941/                     # local OCR packet (4 files, synthetic)
│   ├── 01_Meridian_StopLoss_Policy_MPM-SL-2026-0147.md
│   ├── 02_Hospital_UB04_CMS1450_Claim_9941.md
│   ├── 03_Clinical_UR_Case_Notes.md
│   └── 04_TPA_Aegle_Accel_Funding_Request.md
├── claimcatch_mcp.py                      # FastMCP stdio server, 6 tools
├── CLAIMCATCH_PARTNER_ASSOCIATE_PROMPT.md # LibreChat system prompt
├── demo_walkthrough.py                    # end-to-end walkthrough against the tools
├── tests/test_claimcatch.py               # tool-level tests, offline
├── web/                                   # static workbench (no backend)
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── diagrams/
│   │   └── claimcatch-flow.d2             # D2 source
│   ├── vendor/
│   │   └── pdfjs/
│   │       ├── pdf.min.js
│   │       ├── pdf.worker.min.js
│   │       └── LICENSE
│   └── assets/
│       ├── diagrams/
│       │   ├── claimcatch-flow-inline.svg # compiled inline diagram
│       │   └── claimcatch-flow.svg        # compiled full-size (modal)
│       ├── fonts/                         # Montserrat woff2 (4 weights)
│       └── logos/                         # vendor marks (8 svg)
├── .github/workflows/pages.yml            # Pages deploy from web/
├── requirements.txt
└── README.md
```

`03_Clinical_UR_Case_Notes.md` is the only packet document with clinical narrative. It stays local; nothing from it is quoted, summarized, or staged externally.

---

## Quickstart

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python demo_walkthrough.py
python -m http.server 3000 --bind 0.0.0.0 --directory web
```

The tests and demo run offline (`CLAIMCATCH_OFFLINE=1` semantics). Run them to see their status in your environment; this README makes no claim about their result.

Open `http://localhost:3000/` for the workbench. Any free port works. Binding `0.0.0.0` also exposes a Tailscale or LAN address when the firewall allows it; use `127.0.0.1` for loopback only.

### LibreChat setup

1. Paste the contents of `CLAIMCATCH_PARTNER_ASSOCIATE_PROMPT.md` as the agent's **system prompt**.
2. Register the MCP server over stdio:

   ```json
   {
     "claimcatch": {
       "command": "python",
       "args": ["/path/to/claimcatch_mcp.py"]
     }
   }
   ```

3. Ask for the claim 9941 readiness check.

HubSpot, Teams, and email writes are intentionally absent. Outbound artifacts are staged, read-only payloads awaiting human approval.

### Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `CLAIMCATCH_DB_PATH` | `./.claimcatch/claimcatch.sqlite3` | SQLite file for cache, audit log, and staging. Created on first run. |
| `CLAIMCATCH_OFFLINE` | unset | `1` disables the live CMS API and forces seed/local logic. Demo and tests use this. |
| `CLAIMCATCH_CMS_API_BASE` | `https://api.coverage.cms.gov/v1` | Base URL for best-effort live NCD 110.24 metadata lookups. |
| `CLAIMCATCH_HTTP_TIMEOUT` | `4` | Timeout in seconds for live CMS requests. |

---

## Architecture

| Stage | Component | Job |
|---|---|---|
| 01 Parse | Mistral OCR 4.1 via managed, serverless `/v1/ocr` under an executed Enterprise HIPAA BAA and ZDR | Turns PDFs, scanned UB-04s, and policy binders into page-anchored Markdown with `{page_no, bbox}`. |
| 02 Reason | Fireworks AI, US-resident `deepseek-v4p1-flash-1017-us`, `store:false` | Reasons over the parsed Markdown with zero prompt retention. |
| 03 Verify | FastMCP tools against [CMS NCD 110.24](https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=372), [openFDA](https://open.fda.gov/), [CourtListener](https://www.courtlistener.com/), [eCFR Title 29](https://www.ecfr.gov/current/title-29) | Deterministic coverage, label, case-law, and UB-04 FL47/FL48 cross-foot checks. |
| 04 Act | Zero-PHI sanitizer plus human review gate | Stages a de-identified `catastrophic_claim` record and drafts the finance memo and TPA cure notice. Nothing is sent or written without sign-off. |

---

## Benchmark

The How It Works page charts the [Artificial Analysis Legal Index](https://artificialanalysis.ai/indexes/legal), accessed 12 Nov 2026. Cost per legal task is AA's benchmark spend, not ClaimCatch per-claim economics.

| Model | Legal Index | Cost per legal task |
|---|---:|---:|
| DeepSeek V4.1 Flash (Fireworks) | 38 | $0.19 |
| Kimi K3.1 Pro (Fireworks) | 49 | $1.97 |
| Gemini 4 Carbon | 62 | $2.57 |
| Claude Fable 5.2 | 63 | $15.67 |

Callout: ~195 legal-index points per $1 for DeepSeek V4.1 Flash versus 4.0 for Claude Fable 5.2 — 81× the cost for 25.6 more points. The cheapest per point is not the most capable.

No other cost, speed, or accuracy table is claimed.

---

## Rollout

1. **Phase 1 — Self-Hosted LibreChat + Legal Verification Tools.** An internal, zero-PHI workspace wired to serverless OCR, Fireworks AI (BAA + ZDR), and the verification tools. Analysts inspect tool calls and citations during packet review.
2. **Phase 2 — Read-Only HubSpot CRM Integration.** Read-only CRM context under ZDR; no automated CRM write access.
3. **Phase 3 — ClaimCatch Intake & Triage Workbench.** This UI: multi-document triage, evidence review, and human-in-the-loop sign-off before staging records or drafting notices.

---

## Tools

All six tools are exposed by `claimcatch_mcp.py` over stdio.

| Tool | Signature | Purpose | Returns |
|---|---|---|---|
| `lookup_medical_code` | `lookup_medical_code(codes: list[str])` | Validate HCPCS/ICD-10 codes before they enter coverage logic. | Per-code validity, system, and description; invalid codes flagged. |
| `check_cms_coverage_and_fda` | `check_cms_coverage_and_fda(hcpcs_code: str, diagnosis_icd10: str)` | Apply seeded coverage logic under NCD 110.24, with a best-effort live metadata check. | Coverage indication, source (seed vs live), and a non-determinative status note. |
| `lookup_stoploss_case_law` | `lookup_stoploss_case_law(issue: str)` | Retrieve analogous stop-loss disputes by issue class (laser/amendment, 12/15 paid-basis/run-out, experimental/investigational). | Case names, issue summaries, relevance; reporter citations are not captured. |
| `reconcile_funding_tranche` | `reconcile_funding_tranche(billed: float, non_covered_fl48: float, lasered_deductible: float, signature_hold: float, requested_advance: float)` | **The only source of funding math.** Computes the waterfall, cross-foot, and gap attribution. | Waterfall lines, approved amount, total gap with components, and a cross-foot check. |
| `stage_zero_phi_hubspot_and_teams_handoff` | `stage_zero_phi_hubspot_and_teams_handoff(claim_id: str, partner_tpa: str, owner_name: str = "Patrick Feit")` | Build the read-only handoff payload from `claimant_key` and financial/contract fields, then run the PHI scan. | Payload with `dry: true`, `status: PENDING_APPROVAL`, HubSpot stage, and `phi_scan` results. |
| `generate_partner_resolution_pack` | `generate_partner_resolution_pack(partner_tpa: str, claim_id: str)` | Draft the TPA resolution pack: issues, root cause, cure steps, owner, due date, curability. | Structured issue set plus a zero-PHI TPA message body. |

Never compute a tranche by hand: call `reconcile_funding_tranche` and show its cross-foot.

---

## Funding waterfall (claim 9941)

| Line | Amount | Label |
|---|---:|---|
| Billed | $3,050,000 | Total billed charges |
| Less FL48 non-covered | −$350,000 | Services outside the covered benefit schedule |
| Less lasered deductible (Endorsement L-1) | −$750,000 | Separate specific deductible on `MPM-9941-07` |
| Less signature hold | −$250,000 | Tranche 2 held pending CFO and carrier signatures |
| **Draft Tranche 1** | **$1,700,000** | Draft for human sign-off |
| Requested advance | $2,800,000 | Amount requested by the partner |
| **Total gap** | **$1,100,000** | Requested minus draft |

Gap attribution: $500,000 laser gap ($750,000 vs $250,000 base) + $350,000 FL48 + $250,000 signature hold = $1,100,000. Laser and FL48 are non-curable; the hold cures on both signatures.

---

## Limitations

- Static demo: the workbench calls no backend and performs no network writes.
- PDF.js extracts embedded text only; scanned/image-only PDFs surface no text.
- No external HubSpot, Teams, or email writes; BAAs and ZDR are contractual.
- AA Legal Index figures are a 12 Nov 2026 snapshot and are not ClaimCatch claim economics.
- Crafted, synthetic packet and figures; the $250,000 signature hold is simulated.
- No live wire or release path exists in this repo.

---

## Deploy

Live: https://henrygetz.github.io/claimcatch/

GitHub Pages currently serves the static `web/` snapshot from the `gh-pages` branch (legacy builder). The repository also includes `.github/workflows/pages.yml` for Actions-based deployment; GitHub Actions is currently billing-locked on the account, so the workflow is not active. Once Actions billing is restored, switch the Pages source to GitHub Actions and pushes to `main` will deploy automatically. The published build is static: no server, no API keys, no writes.

---

ClaimCatch · Aegle Capital
