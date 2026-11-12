# ClaimCatch

ClaimCatch — partner-side stop-loss claim operations for Aegle Capital.

A six-tool MCP server plus a LibreChat system prompt that turn a local claim packet into a readiness check, an exact funding reconciliation, a zero-PHI CRM handoff, and a TPA resolution pack.

> **Synthetic data.** Claim `9941`, policy `MPM-SL-2026-0147`, and every figure in this repo are fabricated for demonstration. No real member, employer, TPA, carrier, or claim data is included. Nothing here is clinical, legal, or coverage advice.

---

## What this demo proves

- **1/1 laser detection.** Endorsement L-1 imposes a $750,000 separate specific deductible on `MPM-9941-07` against a $250,000 base — a $500,000 gap invisible on the policy summary.
- **Exact funding reconciliation.** One tool owns all funding arithmetic: $3,050,000 billed becomes $1,700,000 approved and $1,100,000 of fully attributed gap.
- **Zero-PHI human-in-the-loop staging.** HubSpot/Teams handoff is read-only, `dry: true`, `PENDING_APPROVAL`, and gated on `phi_scan.result == "PASS"`.
- **TPA resolution pack.** Issues are converted into root cause, cure steps, owner, and due date — with curability stated explicitly.
- **Cite-able OCR packet.** Every document claim resolves to a packet page and bounding box in `claim_packet_9941/`.
- **Auditable tools.** Every tool call writes an `audit_log` row; cache TTL is 24h; logging is stderr-only.
- **Interactive workbench.** One state model drives intake -> simulated agent trace -> source evidence -> cure -> HubSpot push, with confirmations, receipts, and timestamps.

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
├── CLAIMCATCH_PARTNER_ASSOCIATE_PROMPT.md      # LibreChat system prompt
├── demo_walkthrough.py                    # end-to-end walkthrough against the tools
├── tests/test_claimcatch.py               # tool-level tests, offline
├── web/                                   # workbench UI (no network writes)
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── diagrams/
│   │   └── claimcatch-flow.d2             # D2 source: full architecture flow
│   └── assets/
│       ├── diagrams/
│       │   ├── claimcatch-flow-inline.svg # compiled multi-node inline diagram
│       │   └── claimcatch-flow.svg        # compiled full-size (modal)
│       ├── fonts/                         # Montserrat 400/500/600/700 (woff2)
│       │   ├── montserrat-400.woff2
│       │   ├── montserrat-500.woff2
│       │   ├── montserrat-600.woff2
│       │   └── montserrat-700.woff2
│       └── logos/                         # mistral, fireworks, fastmcp, mcp,
│                                          # cmsgov, openfda, courtlistener, hubspot
├── requirements.txt
└── README.md
```

`03_Clinical_UR_Case_Notes.md` is the only packet document containing clinical narrative. It stays local; nothing from it is quoted, summarized, or staged for an external channel.

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

The test suite and demo run with `CLAIMCATCH_OFFLINE=1` semantics, so no network access is required. Run the tests to see their status in your environment; this README makes no claim about their result.

Then open `http://localhost:3000/` for the workbench. Any free port works. Binding `0.0.0.0` also makes the page reachable on a Tailscale or LAN IP when the host firewall allows it; use `127.0.0.1` if you only want loopback access.

### LibreChat setup

1. Paste the full contents of `CLAIMCATCH_PARTNER_ASSOCIATE_PROMPT.md` as the agent's **system prompt**.
2. Add the MCP server as a stdio MCP server:

   ```json
   {
     "claimcatch": {
       "command": "python",
       "args": ["/path/to/claimcatch_mcp.py"]
     }
   }
   ```

3. Start a conversation and ask for the claim 9941 readiness check.

Real HubSpot, Teams, and email writes are **intentionally absent**. The only outbound artifacts are staged, read-only payloads awaiting human approval.

---

## Interactive workbench (`web/`)

A brand-matched operator workbench for claim 9941. Montserrat (local woff2), navy `#192e58`, teal `#368caa`, 4px-radius uppercase buttons, 1200px layout, responsive to 390px. All assets are local — the logo, fonts, and vendor marks ship in `web/assets/` (marks under `web/assets/logos/`); no CDN at runtime. No build step, no dependencies. Deep links: `#intake`, `#workbench`, `#evidence`, `#resolution`, `#how-it-works`.

**Flow.**

1. **Claim intake.** Drag and drop a PDF/ZIP, or press **Simulate Upload: Claim #9941 Packet (4 PDFs · 312 Pages)**.
2. **Agent stream (~7.2s).** Four animated steps: OCR parse (`Mistral OCR 4.1`, `mistral-ocr-4-1`, 312 pages), CMS/FDA coverage check, laser check (Endorsement L-1, Policy p. 7), and funding reconciliation. This trace is simulated in the page.
3. **Workbench.** Three zones: the hero decision banner, the three-finding trap attribution ($500,000 laser gap, $350,000 FL48, $250,000 signature hold), and the resolution + HubSpot action panel.

FL48 detail on the page: $235,000 Rev 0256/J9999 CD22 protocol, $40,000 off-label HCPCS `J3490`, $25,000 private-room differential, and $50,000 convenience charges.

**Evidence drawer.** Policy, UB-04, and TPA pages render as formatted documents with the cited findings highlighted; a toggle switches to the extracted Markdown with page and bbox metadata. Keyboard-accessible with focus return and Escape to close.

**Cure checkboxes.** Employer CFO signature and carrier countersignature drive a single state model: approved advance $1,700,000 -> $1,950,000, curable hold $250,000 -> $0, Tranche 2 status `READY FOR DISBURSEMENT`. Unchecking either signature reverses every dependent value.

**Actions.** Send Cure Notice, Route to Lockton, and Approve & Push to HubSpot each open a confirmation dialog and then a terminal receipt with an audit timestamp; no control is disabled by state, and repeating an action returns the existing receipt. The HubSpot panel is a `catastrophic_claim` record with the Lockton growth signal, plus a raw JSON payload toggle.

**Boundary.** The workbench is hard-coded demo data with a simulated stream. It does not call the MCP server, reads no packet files or external APIs at runtime, and performs no network writes; receipts and timestamps are local UI state.

---

## HOW IT WORKS

The architecture page is the fifth nav destination: `INTAKE / WORKBENCH / EVIDENCE / RESOLUTION / HOW IT WORKS`, plus the `Ask Packet (Chat)` action in the topbar. The profile chip reads `Patrick Feit · VP, Client Partnerships`, and there is no sandbox badge.

**Architecture page.** Navy hero, then a four-stage pipeline:

| Stage | Component | Job |
|---|---|---|
| 01 Parse | **Private-VPC Structural Parsing** — Mistral OCR 4.1 (`mistral-ocr-4-1`) via stateless `/v1/ocr`, ZDR | PDFs, scanned UB-04s, and .docx binders become page-anchored Markdown with `{page_no, bbox}`. |
| 02 Reason | Fireworks AI, US-resident `deepseek-v4p1-flash-1017-us`, `store:false` | Reasoning over the parsed Markdown with zero prompt retention. |
| 03 Verify | FastMCP ground truth: CMS NCD 110.24, openFDA, CourtListener, eCFR | Deterministic coverage, label, case-law, and cross-foot checks. |
| 04 Act | Zero-PHI sanitizer, then HubSpot `catastrophic_claim` and Aegle Accel | De-identified staging, growth signal, and drafted cure notices. |

The full multi-node architecture is inline: `web/assets/diagrams/claimcatch-flow-inline.svg` renders in a horizontally scrollable frame with a mobile pan hint, and its arrow labels stay readable at that size. The optional full-size view opens from **Open full D2 diagram** in a modal and uses the static `web/assets/diagrams/claimcatch-flow.svg`, compiled from `web/diagrams/claimcatch-flow.d2`. There is no runtime diagram service. The page also carries a locked-vs-cleared trust-boundary comparison, a 30/60/90 rollout, and a FAQ.

**Ask Packet (Chat).** A topbar action opens a 440px slide-over (full-screen on mobile) that answers packet questions from three starter prompts, shows the MCP tool pill used for each answer, and links citations into the evidence drawer at Policy p. 3, Policy p. 7, UB-04, and the TPA request. Free-typed questions route by intent to the same answers. The bridge is read-only and zero-PHI.

**Benchmark section.**

- **Chart 1 — Domain Accuracy**, tagged `AEGLE 12-FIELD ADJUDICATION BENCHMARK`: 94% Frontier+MCP versus 82% human specialist. Evaluated across 12 stop-loss adjudication fields (Specific Deductible, Endorsement Lasers, UB-04 FL47/FL48 cross-footing, CMS NCD 110.24, and Section D signatures) with mandatory human sign-off.
- **Chart 2 — Cost vs Effective Adjudication Accuracy**: Fireworks AI + FastMCP sits top-left at 94% for $0.60 per task; unassisted models plot to the right at higher cost. Callout: `94% Effective Domain Accuracy · $0.60/task · ~40x lower cost than unassisted proprietary frontier models`. Cost per task comes from Artificial Analysis v5.0.1.

Cost strip: OCR $4.00 per 1,000 pages + reasoning $1.47 base / $2.21 US-pinned = $5.47–$6.21 all-in per 1,000 pages. Based on 312-page TPA claim packet (~2,100 input / 700 output tokens per page) via Mistral OCR 4.1 + Fireworks AI US-Resident ZDR.

BAA line: Production deployment operates under executed Enterprise HIPAA BAA + enforced Zero Data Retention (ZDR) across all inference and OCR endpoints.

**Rollout.** Days 1–30 — Self-Hosted LibreChat + FastMCP (Shadow Mode): deploy an internal, zero-PHI LibreChat workspace wired to Mistral OCR 4.1, Fireworks AI ZDR, and our Python FastMCP tools in 48 hours—giving Partner Associates immediate ad-hoc packet interrogation during 1/1 and 7/1 readiness checks before graduating to this dedicated Workbench UI. Days 31–60 connect read-only FastMCP staging to the HubSpot `catastrophic_claim` pipeline with one-click Partner Associate sign-off; days 61–90 expose pre-flight packet readiness checks to TPAs and brokers.

**Resolution — Drafted Outbound Pack.** Below the cure checklist, the page drafts three zero-PHI artifacts: the TPA cure notice (Tranche 1 $1,700,000; Tranche 2 $250,000 held), the finance memo ($1,100,000 gap attribution), and the 1/1 playbook update. The FL48 detail names the off-label line as HCPCS `J3490`.

---

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `CLAIMCATCH_DB_PATH` | `./.claimcatch/claimcatch.sqlite3` | SQLite file for cache, audit log, and staging records. Created on first run. |
| `CLAIMCATCH_OFFLINE` | unset | `1` disables the live CMS API and forces seed/local logic. The demo and tests use this. |
| `CLAIMCATCH_CMS_API_BASE` | `https://api.coverage.cms.gov/v1` | Base URL for best-effort live NCD 110.24 metadata lookups. |
| `CLAIMCATCH_HTTP_TIMEOUT` | `4` | Timeout in seconds for live CMS requests. |

---

## Tools

All six tools are exposed by `claimcatch_mcp.py` over stdio.

| Tool | Signature | Purpose | Returns |
|---|---|---|---|
| `lookup_medical_code` | `lookup_medical_code(codes: list[str])` | Validate HCPCS/ICD-10 codes and normalize their descriptions before they enter coverage logic. | Per-code validity, system, and description; invalid codes flagged. |
| `check_cms_coverage_and_fda` | `check_cms_coverage_and_fda(hcpcs_code: str, diagnosis_icd10: str)` | Apply seeded coverage logic for a service/drug code against a principal diagnosis under NCD 110.24, with a best-effort live CMS call that only checks NCD 110.24 metadata. | Coverage indication, source (seed vs live), and a non-determinative status note. |
| `lookup_stoploss_case_law` | `lookup_stoploss_case_law(issue: str)` | Retrieve analogous stop-loss disputes by issue class (laser/amendment/endorsement, 12/15 paid-basis/run-out, experimental/investigational). | Case names, issue summaries, relevance; reporter citations are not captured. |
| `reconcile_funding_tranche` | `reconcile_funding_tranche(billed: float, non_covered_fl48: float, lasered_deductible: float, signature_hold: float, requested_advance: float)` | **The only source of funding math.** Computes the tranche waterfall, cross-foot, and gap attribution. | Waterfall lines, approved amount, total gap with components, and a cross-foot check. |
| `stage_zero_phi_hubspot_and_teams_handoff` | `stage_zero_phi_hubspot_and_teams_handoff(claim_id: str, partner_tpa: str, owner_name: str = "Patrick Feit")` | Build the read-only HubSpot + Teams handoff payload using only `claimant_key` and financial/contract codes, then run the PHI scan. | Payload with `dry: true`, `status: PENDING_APPROVAL`, HubSpot stage, and `phi_scan` (result, fields, findings). |
| `generate_partner_resolution_pack` | `generate_partner_resolution_pack(partner_tpa: str, claim_id: str)` | Draft the TPA-facing resolution pack: issues, root cause, cure steps, owners, due dates, curability. | Structured issue set plus a zero-PHI TPA message body. |

Never compute a tranche by hand: call `reconcile_funding_tranche` and show its cross-foot.

---

## Funding waterfall (claim 9941)

| Line | Amount | Label |
|---|---:|---|
| Billed | $3,050,000 | Total billed charges for the admission |
| Less FL48 non-covered | −$350,000 | Services outside the covered benefit schedule |
| Less lasered deductible (Endorsement L-1) | −$750,000 | Separate specific deductible on `MPM-9941-07` |
| Less signature hold | −$250,000 | Tranche 2 held pending employer CFO and carrier subrogation signatures |
| **Approved Tranche 1** | **$1,700,000** | Approved for Finance/Accounting disbursement |
| Requested advance | $2,800,000 | Amount requested by the partner |
| **Total gap** | **$1,100,000** | Requested minus approved |

Gap attribution:

| Cause | Amount | Curable |
|---|---:|---|
| Laser gap ($750,000 laser − $250,000 base) | $500,000 | Not curable — contract term |
| FL48 non-covered services | $350,000 | Not curable — coverage |
| Signature hold | $250,000 | Curable — employer CFO signature + carrier subrogation countersignature |
| **Total** | **$1,100,000** | |

Cross-foot: $3,050,000 − $350,000 − $750,000 − $250,000 = $1,700,000; $2,800,000 − $1,700,000 = $1,100,000; $500,000 + $350,000 + $250,000 = $1,100,000.

---

## Zero-PHI handoff

`stage_zero_phi_hubspot_and_teams_handoff` produces a payload that is:

- **Read-only** — it records intent, never performs a write.
- **`dry: true`** and **`status: PENDING_APPROVAL`** — a human with approval authority completes the write.
- **HubSpot stage** `adjudication_hold_laser_flagged`.
- **No network writes** — no HubSpot, Teams, or email API call leaves the process.
- **Field-limited** — no member/patient names, DOB, dates of service, MRN, SSN, addresses, or clinical narrative. Allowed: `claimant_key`, claim/policy IDs, partner TPA, workforce owner name (e.g. `Patrick Feit`), financial amounts.
- **Gated** — the payload is only described as ready when `phi_scan.result == "PASS"`; any other result blocks the send. Report the full scan shape: `result`, `phi_detected` (output artifact after redaction), `input_redactions`, and `fields_stripped` (input scrubbing). A PASS with redactions is still zero-PHI output, but both fields are shown.

---

## Architecture

```mermaid
flowchart LR
    A[Local OCR packet<br/>claim_packet_9941/] --> B[MCP tools<br/>6 tools]
    B --> C[(SQLite<br/>cache · audit · staging)]
    C --> D{Human approval<br/>HITL review}
    D -->|approved| E[External executor (not in demo)<br/>approved writes only]
    D -->|held or rejected| F[Remains staged<br/>PENDING_APPROVAL]
```

---

## What is real vs simulated

| Element | Status |
|---|---|
| CMS NCD 110.24 coverage logic | Coverage mapping seeded locally. The optional live call is a best-effort NCD 110.24 metadata check only (when `CLAIMCATCH_OFFLINE` is not `1`); it does not return the full determination. |
| Mistral OCR 4.1 / Fireworks reasoning | Described architecture, not wired into this repo. The workbench neither calls nor requires either service; no API keys ship. |
| Case law names | Real case names; reporter citations are not captured in this demo. |
| HubSpot / Teams / email writes | Simulated. Staged payloads only; no outbound API calls. |
| Claim packet, policy, claim figures | Fully synthetic. |
| Funding math | Deterministic, computed by `reconcile_funding_tranche`. |

---

## Limitations and next steps

- No live HubSpot write path; a production version needs an approved, audited connector and a named approver role.
- CMS lookups degrade to seed logic when the API is unavailable or `CLAIMCATCH_OFFLINE=1`; results are labeled accordingly and are not a coverage determination.
- No PHI is processed by this demo; production keeps clinical data inside the Aegle VPC, and any future clinical workflow needs a separate, reviewed data-handling design.
- Demo only — figures, entities, and outcomes are fabricated.
- The $250,000 signature hold is a **simulated hold**, not an observed carrier action.
- Case-law lookup does not carry reporter citations; Legal must source authoritative text.

---

## Security and audit notes

- Every tool invocation writes a row to `audit_log` in SQLite: tool name, argument summary, timestamp, and result status.
- Cache entries expire after 24 hours.
- No stdout logging from the MCP server; diagnostics go to stderr only, keeping the stdio protocol clean.
- The packet directory is read locally; OCR text is never forwarded to an external channel.
- PHI scanning runs before any payload is described as sendable, and a non-`PASS` result blocks it.

---

ClaimCatch · Aegle Capital
