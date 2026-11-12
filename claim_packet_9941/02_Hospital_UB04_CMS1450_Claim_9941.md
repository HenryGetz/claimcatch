---
doc_id: DOC-NCH-UB04-9941
source_file: 02_Hospital_UB04_CMS1450_Claim_9941.pdf
pipeline: Mistral OCR 4.1 (mistral-ocr-4-1) · stateless /v1/ocr · ZDR
ocr_mode: sandbox-local OCR simulation
pages: 4
bbox_format: PDF points, top-left origin, 612 x 792 (US Letter)
language: en-US
produced: 2026-11-11T09:40:00Z
classification: CONFIDENTIAL - SYNTHETIC DEMO - CONTAINS PHI
sha256: synthetic-demo-not-a-real-hash
confidence: 0.96
---

# UB-04 / CMS-1450 Claim Extract — Claim #9941

> Extraction note: form is a machine-generated 837i print image; field grid lines recovered at 300 dpi. Field labels below use FL (form locator) numbering. Patient name fields are tokenized to Member ID only.

--- Page 1 of 4 ---

<!-- mistral-ocr:block id=ub-p1-h1 type=heading level=1 -->
**UB-04 / CMS-1450 — CLAIM SUMMARY**
<!-- /mistral-ocr:block -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 1, bbox (72, 72, 540, 108)]

<!-- mistral-ocr:table id=ub-p1-t1 -->
**Facility and Claim Header**

| FL | Field | Value |
|---|---|---|
| FL1 | Billing Provider | Northfield Children's Hospital |
| FL1 | Provider Address | [redacted for demo packet] |
| FL2 | Pay-to | Northfield Children's Hospital — Provider ID on file |
| FL4 | Type of Bill | 111 |
| FL5 | Federal Tax ID | XX-XXXXXXX (masked) |
| FL6 | Statement Covers Period | 15 Aug 2026 – 25 Sep 2026 |
| FL42 | Revenue Code (statement) | 0001 |
| FL47 | Total Charges | $3,050,000.00 |
| FL48 | Total Non-Covered Charges | $350,000.00 |
| FL60 | Insured's Unique ID / Member ID | MPM-9941-07 |
| FL67 | Principal Diagnosis (ICD-10-CM) | C91.02 |
| FL69 | Admitting Diagnosis | C91.02 |
| FL74 | Principal Procedure (ICD-10-PCS) | XW033J7 — 2 Sep 2026 |
| FL76 | Attending NPI | 1XXXXXXXXX (masked) |
<!-- /mistral-ocr:table -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 1, bbox (72, 120, 540, 470)]

Table extraction confidence: 0.99 — all 14 rows recovered, no merged cells.

<!-- mistral-ocr:table id=ub-p1-t2 -->
**FL58–FL61 Insured / Patient**

| FL | Field | Value |
|---|---|---|
| FL58 | Insured's Name | MIDWEST PRECISION MANUFACTURING LLC (group) |
| FL59 | Patient's Relationship to Insured | 01 — Self |
| FL60 | Patient ID | MPM-9941-07 |
| FL61 | Group Name / Number | MIDWEST PRECISION MFG / MPM-SL-2026-0147 |
| FL62 | Insurance Group No. | MPM-SL-2026-0147 |
| FL63 | Treatment Authorization Code | PA-9941-0926 |
| FL80 | Remarks | see page 4 |
<!-- /mistral-ocr:table -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 1, bbox (72, 482, 540, 700)]

Table extraction confidence: 0.97 — patient name field contains a member token, not a name; no name text present in the source image.

Page 1 of 4 | Mistral OCR 4.1 (ZDR) · page-anchored Markdown

--- Page 2 of 4 ---

<!-- mistral-ocr:block id=ub-p2-h1 type=heading level=2 -->
**DETAIL CHARGES (CONTINUED ON PAGE 3)**
<!-- /mistral-ocr:block -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 2, bbox (72, 72, 540, 104)]

<!-- mistral-ocr:table id=ub-p2-t1 -->
| Rev | Description | HCPCS | Date(s) | Units | Billed | FL48 Non-Covered |
|---|---|---|---|---|---|---|
| 0200 | ICU — medical/surgical | — | 15 Aug – 1 Sep 2026 | 18 days @ $25,000.00 | $450,000.00 | $0.00 |
| 0206 | Step-down unit | — | 2 Sep – 15 Sep 2026 | 14 days @ $13,000.00 | $182,000.00 | $0.00 |
| 0110 | Private room — medically necessary | — | 16 Sep – 25 Sep 2026 | 10 days @ $5,000.00 | $50,000.00 | $0.00 |
| 0110 | Private deluxe suite differential | — | 16 Sep – 25 Sep 2026 | 10 days @ $2,500.00 | $25,000.00 | $25,000.00 |
| 0250 | Pharmacy — general | — | 15 Aug – 25 Sep 2026 | — | $400,000.00 | $0.00 |
| 0335 | Chemotherapy administration | — | 15 Aug – 25 Sep 2026 | — | $120,000.00 | $0.00 |
| 0381 | Blood products | — | 15 Aug – 25 Sep 2026 | — | $180,000.00 | $0.00 |
| 0384 | Blood administration | — | 15 Aug – 25 Sep 2026 | — | $60,000.00 | $0.00 |
| 0300 | Laboratory — general | — | 15 Aug – 25 Sep 2026 | — | $188,000.00 | $0.00 |
| 0320 | Radiology — diagnostic | — | 15 Aug – 25 Sep 2026 | — | $90,000.00 | $0.00 |
<!-- /mistral-ocr:table -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 2, bbox (72, 116, 540, 560)]

Table extraction confidence: 0.95 — 10 rows; the two 0110 rows are consecutive and were correctly kept separate (currency column aligned at x = 470).

<!-- mistral-ocr:block id=ub-p2-b1 type=paragraph -->
Line 1–3 dates: ICU and step-down day counts reconcile to the 15 Aug 2026 admission and the 25 Sep 2026 discharge, 42 days total (18 + 14 + 10). The 10 private-room days and the 10 deluxe-suite differential days both run **16 Sep – 25 Sep 2026** and are concurrent; 15 Sep 2026 was billed at the step-down rate. The differential is a per-day upgrade charge, not an additional day of stay.
<!-- /mistral-ocr:block -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 2, bbox (72, 572, 540, 676)]

Page 2 of 4 | Mistral OCR 4.1 (ZDR) · page-anchored Markdown

--- Page 3 of 4 ---

<!-- mistral-ocr:block id=ub-p3-h1 type=heading level=2 -->
**DETAIL CHARGES (CONTINUED)**
<!-- /mistral-ocr:block -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 3, bbox (72, 72, 540, 104)]

<!-- mistral-ocr:table id=ub-p3-t1 -->
| Rev | Description | HCPCS | Date(s) | Units | Billed | FL48 Non-Covered |
|---|---|---|---|---|---|---|
| 0410 | Respiratory services | — | 15 Aug – 25 Sep 2026 | — | $80,000.00 | $0.00 |
| 0270 | Medical/surgical supplies | — | 15 Aug – 25 Sep 2026 | — | $250,000.00 | $0.00 |
| 0361 | Minor procedure | — | 4 Sep 2026 | 1 | $50,000.00 | $0.00 |
| 0260 | IV therapy | — | 15 Aug – 25 Sep 2026 | — | $25,000.00 | $0.00 |
| 0891 | Cell therapy administration — Kymriah (tisagenlecleucel) | Q2042 | 2 Sep 2026 | 1 | $475,000.00 | $0.00 |
| 0891 | Cell therapy administration — supportive | — | 2 Sep – 6 Sep 2026 | — | $100,000.00 | $0.00 |
| 0256 | Investigational CD22 CAR-T (protocol MPM-RES-2026-014) | J9999 | 10–12 Sep 2026 | — | $235,000.00 | $235,000.00 |
| 0636 | Off-label pembrolizumab | J3490 | 15 Sep and 22 Sep 2026 | 2 | $40,000.00 | $40,000.00 |
| 0999 | Patient convenience / luxury package | — | 15 Sep – 25 Sep 2026 | — | $50,000.00 | $50,000.00 |
| 0001 | **TOTAL CHARGES — summary row (FL47 / FL48)** | — | — | — | **$3,050,000.00** | **$350,000.00** |
<!-- /mistral-ocr:table -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 3, bbox (72, 116, 540, 596)]

Table extraction confidence: 0.93 — dense 7-column table; the J9999 and J3490 HCPCS tokens are small-type and were confirmed twice at 400 dpi. Row 0001 is a form summary row printed by the billing system and is excluded from the line sum.

<!-- mistral-ocr:block id=ub-p3-b1 type=paragraph -->
Q2042 Kymriah is FDA-approved for B-cell precursor acute lymphoblastic leukemia in patients up to 25 years of age and is covered under CMS National Coverage Determination **NCD 110.24** (Chimeric Antigen Receptor T-Cell Therapy). One unit at $475,000.00, administered 2 Sep 2026, no FL48 amount applied.
<!-- /mistral-ocr:block -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 3, bbox (72, 608, 540, 700)]

Page 3 of 4 | Mistral OCR 4.1 (ZDR) · page-anchored Markdown

--- Page 4 of 4 ---

<!-- mistral-ocr:block id=ub-p4-h1 type=heading level=2 -->
**TOTALS, FL48 RECONCILIATION, AND REMARKS**
<!-- /mistral-ocr:block -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 4, bbox (72, 72, 540, 104)]

<!-- mistral-ocr:table id=ub-p4-t1 -->
**Charge Reconciliation**

| Item | Amount |
|---|---|
| Sum of itemized detail lines (rev 0200 through 0999) | $3,050,000.00 |
| FL47 Total Charges | $3,050,000.00 |
| Less FL48 Total Non-Covered Charges | ($350,000.00) |
| **Eligible charges (FL47 − FL48)** | **$2,700,000.00** |
<!-- /mistral-ocr:table -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 4, bbox (72, 116, 540, 268)]

Table extraction confidence: 0.98.

<!-- mistral-ocr:table id=ub-p4-t2 -->
**FL48 Non-Covered Line Detail**

| Rev | Description | Non-Covered | Reason |
|---|---|---|---|
| 0256 | Investigational CD22 CAR-T, J9999 | $235,000.00 | Experimental / investigational — protocol MPM-RES-2026-014, IRB #2026-114 |
| 0636 | Off-label pembrolizumab, J3490 | $40,000.00 | Off-label — not FDA-approved for C91.02 |
| 0110 | Private deluxe suite differential | $25,000.00 | Not medically necessary — convenience/upgrade |
| 0999 | Patient convenience / luxury package | $50,000.00 | Not medically necessary — convenience/luxury |
| | **Total FL48** | **$350,000.00** | |
<!-- /mistral-ocr:table -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 4, bbox (72, 280, 540, 470)]

Table extraction confidence: 0.96 — reason text reflowed from a 3-line-per-row layout.

<!-- mistral-ocr:block id=ub-p4-b1 type=paragraph -->
**FL80 Remarks.** Itemized bill attached; charges certified as accurate and submitted in accordance with the provider's chargemaster. Non-covered amounts are identified at the line level above and are excluded from the total in FL47.

**Authorization.** PA-9941-0926 was issued by Prairie States Administrators for **Q2042 Kymriah only**. The authorization does not extend to protocol MPM-RES-2026-014 (investigational CD22 CAR-T) or to the off-label pembrolizumab administrations.

**NCD reference.** Q2042 administered 2 Sep 2026 under CMS NCD 110.24; coverage criteria documented in the medical record (B-ALL, age ≤ 25, relapsed/refractory).

**Reason codes.** FL48 lines are coded as: 0256 — CARC 55 (experimental/investigational), RARC N425; 0636 — CARC 55 (off-label, no FDA approval for indication); 0110 differential — CARC 50 (not medically necessary); 0999 — CARC 50 (not medically necessary, convenience).
<!-- /mistral-ocr:block -->
[02_Hospital_UB04_CMS1450_Claim_9941.pdf, p. 4, bbox (72, 482, 540, 700)]

Page 4 of 4 | Mistral OCR 4.1 (ZDR) · page-anchored Markdown
