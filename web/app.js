/* ==========================================================================
   ClaimCatch — Claim #9941 workbench
   No network calls, no external writes.
   ========================================================================== */
"use strict";

(function () {
  if (window.pdfjsLib && window.pdfjsLib.GlobalWorkerOptions) {
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = "vendor/pdfjs/pdf.worker.min.js";
  }

  /* ------------------------------------------------------------------ */
  /* Data                                                                */
  /* ------------------------------------------------------------------ */

  const AMOUNTS = {
    billed: 3050000,
    eligible: 2700000,
    requested: 2800000,
    laserDeductible: 750000,
    baseDeductible: 250000,
    laserGap: 500000,
    fl48: 350000,
    tranche1: 1700000,
    curedApproved: 1950000,
    hold: 250000,
    hardExclusions: 850000,
    reimbursable: 1950000
  };

  const LEGAL_BENCHMARK = {
    title: "Artificial Analysis Legal Index",
    url: "https://artificialanalysis.ai/indexes/legal",
    callout:
      "DeepSeek V4.1 Flash: ~195 legal-index points per $1. Claude Fable 5.2: 4.0 — 81× the cost for 25.6 more points. The cheapest per point is not the most capable: 38 vs 63.",
    source:
      "Source: Artificial Analysis Legal Index, accessed 12 Nov 2026. Cost per legal task is AA's benchmark spend, not Aegle's per-claim economics.",
    points: [
      { label: "DeepSeek V4.1 Flash", provider: "Fireworks", score: 38, cost: 0.19, tone: "#2B7A8B", highlight: true },
      { label: "Kimi K3.1 Pro", provider: "Fireworks", score: 49, cost: 1.97, tone: "#192E58" },
      { label: "Gemini 4 Carbon", score: 62, cost: 2.57, tone: "#6B7F8C" },
      { label: "Claude Fable 5.2", score: 63, cost: 15.67, tone: "#192E58" }
    ]
  };

  const DEMO_STATS = { pages: 312, files: 4, real: false };

  function pdfLabel(count) {
    return count + " PDF" + (count === 1 ? "" : "s");
  }

  function pageLabel(count) {
    return count + " page" + (count === 1 ? "" : "s");
  }

  function buildStreamSteps(pages, files) {
    return [
      {
        id: "ocr",
        num: "01",
        at: 0,
        doneAt: 1400,
        title:
          "Mistral OCR 4.1 (ZDR Stateless /v1/ocr) — " +
          pages +
          " pages across " +
          files +
          " " +
          (files === 1 ? "PDF" : "PDFs") +
          " converted to page-anchored Markdown",
        detail: "",
        doneDetail: ""
      },
      {
        id: "cms",
        num: "02",
        at: 2800,
        title: "Verification: CMS & FDA",
        detail:
          "Q2042 Kymriah <b>$475,000</b> covered under CMS NCD 110.24; Rev 0256 / J9999 <b>$235,000</b> experimental CD22 trial; <b>$115,000</b> off-label/luxury lines flagged."
      },
      {
        id: "laser",
        num: "03",
        at: 4200,
        title: "Verification: policy laser",
        detail:
          '<span class="alert-word">ALERT</span> Endorsement L-1 on Page 7; <b>$750,000</b> separate specific deductible; <b>$500,000</b> non-curable gap.'
      },
      {
        id: "funding",
        num: "04",
        at: 5600,
        title: "Verification: funding math",
        detail:
          "Safe Tranche 1 <b>$1,700,000</b>; <b>$250,000</b> held for missing CFO + carrier signatures."
      }
    ];
  }

  const STREAM_DURATION = 7200;

  const DOCS = {
    policy: {
      label: "Policy evidence",
      title: "Endorsement L-1",
      sub: "Meridian Mutual Stop Loss · Policy MPM-SL-2026-0147",
      page: "Policy p. 7",
      bbox: "document: 01_Meridian_StopLoss_Policy_MPM-SL-2026-0147.md\npage: 7\nbbox: (72, 236, 540, 512)\nextraction: Mistral OCR 4.1 (ZDR) · page-anchored Markdown",
      citation:
        "<b>Cited authority · Trustmark Ins. Co. v. Citizens (D. Conn. 2004).</b> A separately negotiated specific deductible controls over the base schedule when the endorsement is executed in the policy.",
      formatted: `
        <div class="doc-page">
          <div class="doc-banner"><h3>Endorsement L-1</h3><span>MPM-SL-2026-0147</span></div>
          <p class="doc-sub">Meridian Mutual Stop Loss · Policy MPM-SL-2026-0147 · Effective 01 Jan 2026</p>
          <div class="doc-rule"></div>
          <div class="doc-row"><span class="k">Issued</span><span class="v">18 Dec 2025</span><span>p. 7</span></div>
          <div class="doc-row"><span class="k">Applies to</span><span class="v">Member ID MPM-9941-07</span><span>De-identified</span></div>
          <div class="doc-row"><span class="k">Diagnosis</span><span class="v">C91.02</span><span>p. 7</span></div>
          <div class="doc-rule"></div>
          <div class="doc-body">
            <p>The Separate Specific Deductible of $750,000 replaces, and does not add to, the $250,000 Specific Deductible shown on Schedule A for Member MPM-9941-07 and diagnosis C91.02.</p>
            <div class="doc-clause"><span class="clause-tag">Endorsement L-1 · cited clause</span>“The Separate Specific Deductible of $750,000.00 … replaces, and does not add to, the $250,000.00 Specific Deductible shown on Schedule A for Member ID MPM-9941-07 and diagnosis C91.02.”</div>
          </div>
          <div class="doc-rule"></div>
          <div class="doc-row hl-line"><span class="k">Separate Specific Deductible</span><span class="v">$750,000</span><span>p. 7</span></div>
          <div class="doc-row"><span class="k">Base Specific Deductible (Schedule A)</span><span class="v">$250,000</span><span>Schedule A · p. 2</span></div>
          <div class="doc-row"><span class="k">Contract basis</span><span class="v">12/15 · paid through 31 Mar 2027</span><span></span></div>
          <p class="doc-note">Amounts applied to the Separate Specific Deductible do not accumulate toward the Aggregate Attachment Point. No No-New-Laser endorsement is included in the executed extract. Endorsement appears at page 7, after Schedule A.</p>
        </div>`,
      markdown: `
<div class="md-page">
  <span class="page-tag">p. 7</span>
  <pre># ENDORSEMENT L-1 · POLICY MPM-SL-2026-0147

Issued ............ 18 Dec 2025
Applies to ........ Member ID MPM-9941-07
Diagnosis ......... C91.02

The Separate Specific Deductible of $750,000 replaces, and does not
add to, the $250,000 Specific Deductible shown on Schedule A for
Member MPM-9941-07 and diagnosis C91.02.

&gt; "The Separate Specific Deductible of $750,000.00 … replaces, and
&gt; does not add to, the $250,000.00 Specific Deductible shown on
&gt; Schedule A for Member ID MPM-9941-07 and diagnosis C91.02."

Separate Specific Deductible ........ $750,000
Base Specific Deductible ............ $250,000
Contract basis ...................... 12/15 · paid through 31 Mar 2027

Amounts applied to the Separate Specific Deductible do not accumulate
toward the Aggregate Attachment Point. No No-New-Laser endorsement is
included in the executed extract.</pre>
</div>`
    },

    policyAssignment: {
      label: "Policy evidence",
      title: "Policy §7.4 — Anti-assignment",
      sub: "Meridian Mutual Stop Loss · Policy MPM-SL-2026-0147",
      page: "Policy p. 3",
      bbox: "document: 01_Meridian_StopLoss_Policy_MPM-SL-2026-0147.md\npage: 3\nbbox: (72, 368, 540, 452)\nextraction: Mistral OCR 4.1 (ZDR) · page-anchored Markdown",
      citation:
        "<b>Policy §7.4 · Anti-assignment.</b> Executed policy language prohibits assignment of reimbursement and requires the carrier to disregard any purported assignment.",
      formatted: `
        <div class="doc-page">
          <div class="doc-banner"><h3>Policy §7.4</h3><span>MPM-SL-2026-0147</span></div>
          <p class="doc-sub">Meridian Mutual Stop Loss · Policy MPM-SL-2026-0147 · Page 3</p>
          <div class="doc-rule"></div>
          <div class="doc-row"><span class="k">Section</span><span class="v">§7.4 — Assignment</span><span>p. 3</span></div>
          <div class="doc-row"><span class="k">Effective</span><span class="v">01 Jan 2026</span><span></span></div>
          <div class="doc-row"><span class="k">Applies to</span><span class="v">Policy MPM-SL-2026-0147</span><span></span></div>
          <div class="doc-rule"></div>
          <div class="doc-body">
            <p><strong>7.4 ASSIGNMENT.</strong> No assignment of reimbursement under this policy is recognized by the carrier.</p>
            <div class="doc-clause"><span class="clause-tag">§7.4 · cited clause</span>“YOU may not assign reimbursement under this POLICY, and WE shall not recognize any such assignment.”</div>
            <p>Any purported assignment is void against the carrier. Payment direction changes require a separate executed carrier endorsement.</p>
          </div>
          <p class="doc-note">Executed policy extract. No assignment endorsement is included. Claimant key MPM-9941-07.</p>
        </div>`,
      markdown: `
<div class="md-page">
  <span class="page-tag">p. 3</span>
  <pre># POLICY MPM-SL-2026-0147 · §7.4 ASSIGNMENT

Effective .......... 01 Jan 2026
Applies to ......... Policy MPM-SL-2026-0147

## 7.4 ASSIGNMENT
No assignment of reimbursement under this policy is recognized
by the carrier.

&gt; "YOU may not assign reimbursement under this POLICY, and WE
&gt; shall not recognize any such assignment."

Any purported assignment is void against the carrier. Payment
direction changes require a separate executed carrier endorsement.

Executed policy extract. No assignment endorsement is included.</pre>
</div>`
    },

    ub04: {
      label: "Facility claim",
      title: "UB-04 / CMS-1450 claim summary",
      sub: "Prairie States Administrators · Provider statement 08 Oct 2026",
      page: "UB-04 p. 2 / p. 4",
      bbox: "document: 02_Hospital_UB04_CMS1450_Claim_9941.md\npage: 2\nbbox: (72, 116, 540, 560)\nextraction: Mistral OCR 4.1 (ZDR) · page-anchored Markdown",
      citation:
        "<b>Coverage reference · CMS NCD 110.24.</b> Q2042 Kymriah at $475,000 is covered and paid; the FL48 exclusion applies to the investigational protocol, off-label drug, private-room differential, and convenience charges only.",
      formatted: `
        <div class="doc-page">
          <div class="doc-banner"><h3>UB-04 / CMS-1450</h3><span>CLAIM 9941</span></div>
          <p class="doc-sub">Prairie States Administrators · Provider statement 08 Oct 2026 · Type of bill 111</p>
          <div class="doc-rule"></div>
          <div class="ub04-sheet">
            <div class="ub04-grid-2">
              <div class="ub04-cell"><span class="lbl">FL47 · Total charges</span><span class="val">$3,050,000</span></div>
              <div class="ub04-cell hl"><span class="lbl">FL48 · Non-covered charges</span><span class="val">$350,000</span></div>
            </div>
            <div class="ub04-grid-3">
              <div class="ub04-cell"><span class="lbl">Statement period</span><span class="val">15 Aug – 25 Sep 2026</span></div>
              <div class="ub04-cell"><span class="lbl">Member ID</span><span class="val">MPM-9941-07</span></div>
              <div class="ub04-cell"><span class="lbl">Eligible charges</span><span class="val">$2,700,000</span></div>
            </div>
          </div>
          <p class="ub04-section-label">FL48 line items · page 4</p>
          <table class="ub04-lines">
            <thead><tr><th>Revenue / code</th><th>Description</th><th>Charges</th><th>FL48</th></tr></thead>
            <tbody>
              <tr class="is-excluded"><td class="code">0256 / J9999</td><td>CD22 protocol · MPM-RES-2026-014</td><td class="num">$235,000</td><td>Non-covered</td></tr>
              <tr class="is-excluded"><td class="code">0636 / J3490</td><td>Off-label pembrolizumab</td><td class="num">$40,000</td><td>Non-covered</td></tr>
              <tr class="is-excluded"><td class="code">0110</td><td>Private deluxe room differential</td><td class="num">$25,000</td><td>Non-covered</td></tr>
              <tr class="is-excluded"><td class="code">0999</td><td>Convenience / luxury charges</td><td class="num">$50,000</td><td>Non-covered</td></tr>
              <tr class="is-covered"><td class="code">Q2042</td><td>Kymriah, 2 Sep 2026 <span class="covered-chip">Covered</span></td><td class="num">$475,000</td><td>—</td></tr>
            </tbody>
          </table>
          <p class="doc-note">FL48 composition: $235,000 experimental protocol, $40,000 off-label drug, $25,000 private-room differential, $50,000 convenience. Q2042 Kymriah $475,000 is covered under CMS NCD 110.24 and is not a trap. FL67 C91.02 · FL74 XW033J7 · FL63 PA-9941-0926.</p>
        </div>`,
      markdown: `
<div class="md-page">
  <span class="page-tag">p. 2</span>
  <pre># UB-04 / CMS-1450 · CLAIM 9941

FL47  Total charges ............... $3,050,000
FL48  Non-covered charges ......... $350,000
      Eligible charges ............ $2,700,000
FL67  Principal diagnosis ......... C91.02
FL74  Principal procedure ......... XW033J7
FL63  Authorization ............... PA-9941-0926

## FL48 line items
0256 / J9999  CD22 protocol ........ $235,000  non-covered
0636 / J3490  Off-label drug ........ $40,000  non-covered
0110          Private-room diff ..... $25,000  non-covered
0999          Convenience ........... $50,000  non-covered

Q2042  Kymriah, 2 Sep 2026 ......... $475,000  covered · NCD 110.24

## Note
Kymriah Q2042 $475,000 is covered and is not a trap.
The investigational protocol MPM-RES-2026-014 is outside
authorization PA-9941-0926.</pre>
</div>`
    },

    tpa: {
      label: "Funding request",
      title: "Aegle Accel — Section D signatures",
      sub: "Prairie States Administrators · Request 9941-A · 6 October 2026",
      page: "TPA request p. 3",
      bbox: "document: 04_TPA_Aegle_Accel_Funding_Request.md\npage: 3\nbbox: (72, 504, 540, 632)\nextraction: Mistral OCR 4.1 (ZDR) · page-anchored Markdown",
      citation:
        "<b>Contract reference · Request 9941-A § D.</b> The blank Employer CFO line and the absent Meridian countersignature both gate the same $250,000 Tranche 2 and cure on valid signature.",
      formatted: `
        <div class="doc-page">
          <div class="doc-banner"><h3>Advance Request</h3><span>9941-A</span></div>
          <p class="doc-sub">Prairie States Administrators · Request 9941-A · 6 October 2026</p>
          <div class="doc-row"><span class="k">Employer / policyholder</span><span class="v">Midwest Precision Manufacturing LLC</span><span></span></div>
          <div class="doc-row"><span class="k">Policy</span><span class="v">MPM-SL-2026-0147</span><span></span></div>
          <div class="doc-row"><span class="k">Advance requested</span><span class="v">$2,800,000</span><span></span></div>
          <div class="doc-row"><span class="k">Tranche 1</span><span class="v">$1,700,000</span><span>Draft advance</span></div>
          <div class="doc-row"><span class="k">Tranche 2</span><span class="v">$250,000</span><span>Held</span></div>
          <div class="doc-rule"></div>
          <p class="doc-sub">SECTION D — CERTIFICATIONS AND SIGNATURES</p>
          <div class="sig-block">
            <div class="sig-field"><div class="sig-line"></div><span class="sig-label">TPA officer</span><span class="sig-name"><em>/s/ Dana Whitfield</em><br>6 Oct 2026</span></div>
            <div class="sig-field"><div class="sig-line"></div><span class="sig-label">Employer CFO</span><span class="sig-blank">[signature field blank — no ink detected]</span></div>
            <div class="sig-field"><div class="sig-line"></div><span class="sig-label">Date</span><span class="sig-blank">______</span></div>
          </div>
          <div class="sig-block">
            <div class="sig-field"><div class="sig-line"></div><span class="sig-label">Carrier subrogation countersignature</span><span class="sig-blank">[field absent from submitted packet]</span></div>
            <div class="sig-field"><div class="sig-line"></div><span class="sig-label">Meridian Mutual Stop Loss</span><span class="sig-blank">______</span></div>
            <div class="sig-field"><div class="sig-line"></div><span class="sig-label">Date</span><span class="sig-blank">______</span></div>
          </div>
          <p class="doc-note">TPA assertion: eligible paid claims $2,800,000; ineligible $0. Aegle reconciliation determines actual eligibility. Both Section D defects gate the same $250,000 Tranche 2.</p>
        </div>`,
      markdown: `
<div class="md-page">
  <span class="page-tag">p. 3</span>
  <pre># AEGLE ACCEL · 24-HOUR ADVANCE REQUEST 9941-A

Employer / policyholder ... Midwest Precision Manufacturing LLC
Policy .................... MPM-SL-2026-0147
Advance requested ......... $2,800,000
Tranche 1 ................. $1,700,000  draft advance
Tranche 2 ................. $250,000    held

## SECTION D — CERTIFICATIONS AND SIGNATURES

TPA officer ................ /s/ Dana Whitfield   6 Oct 2026
Employer CFO ............... [signature field blank - no ink detected]
Date ....................... ______

Carrier countersignature ... [field absent from submitted packet]
Meridian Mutual Stop Loss .. ______
Date ....................... ______

## Note
Both Section D defects gate the same $250,000 Tranche 2.</pre>
</div>`
    }
  };

  /* ------------------------------------------------------------------ */
  /* Elements & state                                                    */
  /* ------------------------------------------------------------------ */

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.prototype.slice.call((root || document).querySelectorAll(sel));

  const els = {
    intake: $("#intake"),
    stream: $("#stream"),
    workbench: $("#workbench"),
    howItWorks: $("#how-it-works"),
    simulate: $("#simulateBtn"),
    dropzone: $("#dropzone"),
    fileInput: $("#fileInput"),
    fileLine: $("#fileLine"),
    fileMeta: $("#fileMeta"),
    fileName: $("#fileName"),
    parseLine: $("#parseLine"),
    pdfState: $("#pdfState"),
    pdfChip: $("#pdfChip"),
    pdfPreview: $("#pdfPreview"),
    pdfPreviewText: $("#pdfPreviewText"),
    pdfPageTags: $("#pdfPageTags"),
    workbenchUploadMarker: $("#workbenchUploadMarker"),
    workbenchUploadMeta: $("#workbenchUploadMeta"),
    skipWorkbench: $("#skipWorkbench"),
    skipStream: $("#skipStream"),
    streamLog: $("#streamLog"),
    streamFill: $("#streamFill"),
    streamPct: $("#streamPct"),
    streamBar: $("#streamBar"),
    streamFile: $("#streamFile"),
    streamTitle: $("#stream-title"),
    newClaim: $("#newClaimBtn"),
    rerun: $("#rerunBtn"),
    heroAmount: $("#heroAmount"),
    heroApproved: $("#heroApproved"),
    heroHold: $("#heroHold"),
    heroStatusEyebrow: $("#heroStatusEyebrow"),
    timelineCure: $("#timelineCure"),
    equation: $("#equation"),
    reviewTraps: $("#reviewTraps"),
    segApproved: $("#segApproved"),
    segApprovedLabel: $("#segApprovedLabel"),
    segHold: $("#segHold"),
    segHoldLabel: $("#segHoldLabel"),
    legendApproved: $("#legendApproved"),
    legendHold: $("#legendHold"),
    stackBar: $("#stackBar"),
    trap3Tag: $("#trap3Tag"),
    trap3Sub: $("#trap3Sub"),
    trapsTitle: $("#trapsTitle"),
    resolutionTitle: $("#resolution-title"),
    resolutionDesc: $("#resolutionDesc"),
    approvedOut: $("#approvedOut"),
    holdOut: $("#holdOut"),
    t2Status: $("#t2Status"),
    progressPill: $("#progressPill"),
    cureBar: $("#cureBar"),
    cfo: $("#cfoCheck"),
    carrier: $("#carrierCheck"),
    sendCure: $("#sendCure"),
    push: $("#pushHubspot"),
    hsStageHuman: $("#hsStageHuman"),
    hsStageCode: $("#hsStageCode"),
    hsHealth: $("#hsHealth"),
    rawToggle: $("#rawToggle"),
    rawPayload: $("#rawPayload"),
    rawCode: $("#rawCode"),
    auditList: $("#auditList"),
    drawer: $("#drawer"),
    drawerBackdrop: $("#drawerBackdrop"),
    drawerBody: $("#drawerBody"),
    drawerType: $("#drawerType"),
    drawerTitle: $("#drawerTitle"),
    drawerSub: $("#drawerSub"),
    drawerPage: $("#drawerPage"),
    drawerClose: $("#drawerClose"),
    viewFormatted: $("#viewFormatted"),
    viewMarkdown: $("#viewMarkdown"),
    dialog: $("#dialog"),
    dialogBackdrop: $("#dialogBackdrop"),
    dialogKicker: $("#dialogKicker"),
    dialogTitle: $("#dialogTitle"),
    dialogBody: $("#dialogBody"),
    dialogPrimary: $("#dialogPrimary"),
    dialogSecondary: $("#dialogSecondary"),
    dialogClose: $("#dialogClose"),
    mediaModal: $("#mediaModal"),
    mediaBackdrop: $("#mediaBackdrop"),
    mediaTitle: $("#mediaTitle"),
    mediaScroll: $("#mediaScroll"),
    mediaClose: $("#mediaClose"),
    expandDiagram: $("#expandDiagram"),
    askPacket: $("#askPacket"),
    chatDrawer: $("#chatDrawer"),
    chatBackdrop: $("#chatBackdrop"),
    chatClose: $("#chatClose"),
    chatThread: $("#chatThread"),
    chatStarters: $("#chatStarters"),
    chatForm: $("#chatForm"),
    chatInput: $("#chatInput"),
    chatSend: $("#chatSend"),
    outboundPack: $("#outboundPack"),
    packStamp: $("#packStamp"),
    copyDraft: $("#copyDraft"),
    toastStack: $("#toastStack")
  };

  const state = {
    streamTimers: [],
    streamTicker: null,
    streamStart: 0,
    drawerDoc: null,
    drawerView: "formatted",
    drawerOpener: null,
    drawerOpen: false,
    dialogOpen: false,
    dialogOpener: null,
    mediaOpen: false,
    mediaOpener: null,
    chatOpen: false,
    chatBusy: false,
    chatOpener: null,
    cured: false,
    cureSentAt: null,
    cureSentSignatures: null,
    pushedStage: null,
    pushedAt: null,
    pushedStageCode: null,
    pushedApproved: null,
    pushCount: 0,
    rawOpen: false,
    parsing: false,
    parseToken: 0,
    parseHold: null,
    upload: null
  };

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ------------------------------------------------------------------ */
  /* Utilities                                                           */
  /* ------------------------------------------------------------------ */

  function money(value) {
    return "$" + Math.round(value).toLocaleString("en-US");
  }

  function timeStamp() {
    return new Date().toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    });
  }

  function logAction(action, detail) {
    const empty = $(".audit-empty", els.auditList);
    if (empty) empty.remove();

    const li = document.createElement("li");
    li.className = "is-new";
    const time = document.createElement("span");
    time.className = "audit-time";
    time.textContent = timeStamp();
    const text = document.createElement("span");
    text.textContent = action;
    if (detail) {
      const extra = document.createElement("span");
      extra.className = "audit-detail";
      extra.textContent = " — " + detail;
      text.appendChild(extra);
    }
    li.appendChild(time);
    li.appendChild(text);
    els.auditList.appendChild(li);
    els.auditList.scrollTop = els.auditList.scrollHeight;
    // Keep the animation from replaying on subsequent repaints.
    window.setTimeout(function () {
      li.classList.remove("is-new");
    }, 1500);
  }

  function toast(heading, message) {
    const box = document.createElement("div");
    box.className = "toast";
    const dot = document.createElement("span");
    dot.className = "toast-dot";
    dot.setAttribute("aria-hidden", "true");
    const body = document.createElement("div");
    const head = document.createElement("b");
    head.textContent = heading;
    body.appendChild(head);
    body.appendChild(document.createTextNode(message));
    box.appendChild(dot);
    box.appendChild(body);
    while (els.toastStack.children.length >= 2) {
      els.toastStack.firstElementChild.remove();
    }
    els.toastStack.appendChild(box);
    window.setTimeout(function () {
      box.classList.add("is-out");
      window.setTimeout(function () {
        box.remove();
      }, 300);
    }, 4200);
  }

  function animateMoney(el, to) {
    const from = Number(el.textContent.replace(/[^0-9]/g, "")) || 0;
    if (reducedMotion) {
      el.textContent = money(to);
      return;
    }
    if (el._raf) cancelAnimationFrame(el._raf);
    const start = performance.now();
    const duration = 620;
    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = money(from + (to - from) * eased);
      if (t < 1) {
        el._raf = requestAnimationFrame(frame);
      } else {
        el.textContent = money(to);
        el._raf = null;
      }
    }
    el._raf = requestAnimationFrame(frame);
  }

  /* ------------------------------------------------------------------ */
  /* Live state                                                          */
  /* ------------------------------------------------------------------ */

  function computeState() {
    const cured = state.cured;
    const signatures =
      (els.cfo.checked ? 1 : 0) + (els.carrier.checked ? 1 : 0);
    return {
      cured: cured,
      signatures: signatures,
      approved: cured ? AMOUNTS.curedApproved : AMOUNTS.tranche1,
      hold: cured ? 0 : AMOUNTS.hold,
      gap: AMOUNTS.requested - (cured ? AMOUNTS.curedApproved : AMOUNTS.tranche1),
      stage: cured ? "ready_for_human_signoff" : "adjudication_hold_laser_flagged",
      stageHuman: cured
        ? "Ready for human sign-off"
        : "Adjudication hold — laser flagged",
      mbrStatus: cured ? "ON_TRACK" : "AT_RISK",
      healthHuman: cured ? "On track" : "At risk",
      missingEmployer: !cured,
      missingCarrier: !cured,
      status: cured ? "READY_FOR_HUMAN_SIGNOFF" : "PENDING_APPROVAL"
    };
  }

  function buildPayload(cs) {
    cs = cs || computeState();
    const target = cs.cured ? "approved" : "hold";
    const currentPushed = state.pushedStage === target;
    return {
      object: "catastrophic_claim",
      claim_id: "9941",
      claimant_key: "MPM-9941-07",
      partner_tpa: "Prairie States Administrators",
      employer: "Midwest Precision Manufacturing LLC",
      carrier: "Meridian Mutual Stop Loss",
      policy_number: "MPM-SL-2026-0147",
      billed_amount: AMOUNTS.billed,
      fl48_non_covered_amount: AMOUNTS.fl48,
      lasered_deductible: AMOUNTS.laserDeductible,
      base_specific_deductible: AMOUNTS.baseDeductible,
      eligible_amount: AMOUNTS.eligible,
      reimbursable_amount: AMOUNTS.reimbursable,
      requested_advance: AMOUNTS.requested,
      approved_tranche_1: AMOUNTS.tranche1,
      approved_total: cs.approved,
      tranche_2_hold_amount: cs.hold,
      hs_pipeline_stage: cs.stage,
      laser_flag: "flagged",
      missing_signature_employer: cs.missingEmployer,
      missing_signature_tpa: false,
      missing_signature_carrier: cs.missingCarrier,
      open_issue_root_cause: cs.cured
        ? "Unflagged Renewal Laser — signatures cured"
        : "Unflagged Renewal Laser + Missing CFO Counter-Sign",
      partner_health: {
        funding_turnaround_hours: 24,
        mbr_status: cs.mbrStatus
      },
      phi_scan: {
        result: "PASS",
        phi_detected: false,
        phi_field_count: 0
      },
      dry: !currentPushed,
      status: currentPushed ? "PUSHED" : cs.status,
      pushed_at: currentPushed ? state.pushedAt : null
    };
  }

  function barPct(amount) {
    return (amount / AMOUNTS.billed) * 100;
  }

  function setMoney(el, value, animate) {
    if (animate) {
      animateMoney(el, value);
    } else {
      el.textContent = money(value);
    }
  }

  function pushLabelFor(cs) {
    const target = cs.cured ? "approved" : "hold";
    if (state.pushCount >= 2) return "Pushed · " + state.pushedAt;
    if (state.pushedStage === target) return "Pushed · " + state.pushedAt;
    if (target === "hold") return "Push Hold Record";
    return state.pushedStage ? "Push Updated Record" : "Approve & Push to HubSpot";
  }

  function updateActionLabels(cs) {
    if (state.cureSentAt) {
      els.sendCure.textContent = "Cure Notice Sent · " + state.cureSentAt;
    } else {
      els.sendCure.textContent = "Send Cure Notice to TPA";
    }
    els.sendCure.classList.toggle("btn-primary", !cs.cured);
    els.sendCure.classList.toggle("btn-ghost-dark", cs.cured);

    els.push.textContent = pushLabelFor(cs);
    els.push.classList.toggle("btn-primary", cs.cured);
    els.push.classList.toggle("btn-ghost-dark", !cs.cured);

    if (!cs.cured) {
      els.reviewTraps.textContent = "Review traps & cure hold";
      els.reviewTraps.setAttribute("href", "#evidence");
    } else if (state.pushCount >= 2 || state.pushedStage === "approved") {
      els.reviewTraps.textContent = "View HubSpot record";
      els.reviewTraps.setAttribute("href", "#resolution");
    } else {
      els.reviewTraps.textContent = "Confirm & push to HubSpot";
      els.reviewTraps.setAttribute("href", "#resolution");
    }
  }

  function updateUI(options) {
    const animate = Boolean(options && options.animate);
    const cs = computeState();

    setMoney(els.heroAmount, cs.approved, animate);
    setMoney(els.heroApproved, cs.approved, animate);
    setMoney(els.heroHold, cs.hold, animate);
    els.heroStatusEyebrow.textContent = "Claim #9941 · " + cs.stageHuman;

    els.timelineCure.textContent = cs.cured ? "Cure ready" : "Cure pending";
    els.timelineCure.classList.toggle("timeline-pending", !cs.cured);
    els.timelineCure.classList.toggle("timeline-ready", cs.cured);

    els.trapsTitle.textContent = cs.cured
      ? "Two hard exclusions explain $850,000; $250,000 ready for sign-off."
      : "Three findings explain the $1,100,000 gap.";

    els.equation.textContent = cs.cured
      ? "Billed " + money(AMOUNTS.billed) + " − FL48 " + money(AMOUNTS.fl48) +
        " = eligible " + money(AMOUNTS.eligible) + "; less L-1 " +
        money(AMOUNTS.laserDeductible) + " = " + money(AMOUNTS.reimbursable) +
        " reimbursable; hold cleared = " + money(cs.approved) + " draft advance."
      : "Billed " + money(AMOUNTS.billed) + " − FL48 " + money(AMOUNTS.fl48) +
        " = eligible " + money(AMOUNTS.eligible) + "; less L-1 " +
        money(AMOUNTS.laserDeductible) + " = " + money(AMOUNTS.reimbursable) +
        " reimbursable; less hold " + money(AMOUNTS.hold) + " = " +
        money(cs.approved) + " draft advance.";

    els.segApproved.style.width = barPct(cs.approved).toFixed(2) + "%";
    els.segHold.style.width = barPct(cs.hold).toFixed(2) + "%";
    els.segApprovedLabel.textContent =
      "$" + (cs.approved / 1000000).toFixed(2) + "M draft";
    els.segHoldLabel.textContent = cs.hold ? "$250k" : "$0";
    els.legendApproved.textContent = money(cs.approved);
    els.legendHold.textContent = money(cs.hold);
    els.stackBar.setAttribute(
      "aria-label",
      "Attribution of $3,050,000 billed: " + money(cs.approved) +
        " draft, " + money(cs.hold) + " signature hold, " +
        "$500,000 laser gap, $350,000 FL48 excluded, $250,000 base deductible."
    );

    els.trap3Tag.textContent = cs.cured ? "Cured" : "Curable";
    els.trap3Tag.classList.toggle("tag-cure", !cs.cured);
    els.trap3Tag.classList.toggle("tag-cured", cs.cured);
    els.trap3Sub.textContent = cs.cured
      ? "$250,000 included in draft advance; signatures on file"
      : "Tranche 2 clears for human sign-off when both Section D defects cure";

    setMoney(els.approvedOut, cs.approved, animate);
    setMoney(els.holdOut, cs.hold, animate);
    els.holdOut.style.color = cs.cured ? "var(--teal)" : "";
    els.t2Status.textContent = cs.cured ? "READY FOR HUMAN SIGN-OFF" : "HELD";
    els.t2Status.classList.toggle("chip-ready", cs.cured);
    els.t2Status.classList.toggle("chip-held", !cs.cured);
    els.progressPill.textContent = cs.signatures + "/2";
    els.cureBar.style.width =
      cs.signatures === 2 ? "100%" : cs.signatures === 1 ? "50%" : "0%";

    els.hsStageHuman.textContent = cs.stageHuman;
    els.hsStageCode.textContent = cs.stage;
    els.hsHealth.textContent = cs.healthHuman;
    els.hsHealth.classList.toggle("is-ok", cs.cured);

    els.resolutionTitle.textContent = cs.cured
      ? "Hold resolved. Ready for human sign-off."
      : "Resolve the hold. Prepare the sign-off.";
    els.resolutionDesc.textContent = cs.cured
      ? "Draft advance is $1,950,000; both signatures are on file, pending human sign-off."
      : "Tranche 2 is held pending two signatures. Draft advance is $1,700,000.";

    els.rawCode.textContent = JSON.stringify(buildPayload(cs), null, 2);
    updateActionLabels(cs);
  }

  function renderLegalIndex(data) {
    const W = 900;
    const H = 360;
    const left = 64;
    const right = 30;
    const top = 30;
    const bottom = 62;
    const plotW = W - left - right;
    const plotH = H - top - bottom;
    const family = 'Montserrat, Arial, sans-serif';
    const logMin = Math.log10(0.1);
    const logMax = Math.log10(20);
    const x = function (cost) {
      return left + ((Math.log10(cost) - logMin) / (logMax - logMin)) * plotW;
    };
    const y = function (score) {
      return top + ((70 - score) / 40) * plotH;
    };
    let out = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false">';

    [30, 40, 50, 60, 70].forEach(function (tick) {
      const py = y(tick);
      out += '<line x1="' + left + '" y1="' + py + '" x2="' + (W - right) + '" y2="' + py + '" stroke="#E3E7EC"></line>';
      out += '<text x="' + (left - 9) + '" y="' + (py + 4) + '" text-anchor="end" fill="#6F7680" font-family="' + family + '" font-size="11">' + tick + '</text>';
    });

    [0.1, 0.3, 1, 3, 10, 20].forEach(function (tick) {
      const px = x(tick);
      const label = tick < 1 ? "$" + tick.toFixed(2) : "$" + tick;
      out += '<line x1="' + px + '" y1="' + top + '" x2="' + px + '" y2="' + (top + plotH) + '" stroke="#E3E7EC"></line>';
      out += '<text x="' + px + '" y="' + (top + plotH + 17) + '" text-anchor="middle" fill="#6F7680" font-family="' + family + '" font-size="11">' + label + '</text>';
    });

    out += '<line x1="' + left + '" y1="' + (top + plotH) + '" x2="' + (W - right) + '" y2="' + (top + plotH) + '" stroke="#C9CED6"></line>';
    out += '<text x="' + (left + plotW / 2) + '" y="' + (H - 8) + '" text-anchor="middle" fill="#6F7680" font-family="' + family + '" font-size="11">AA Legal Cost per Task (log)</text>';
    out += '<text x="17" y="' + (top + plotH / 2) + '" transform="rotate(-90 17 ' + (top + plotH / 2) + ')" text-anchor="middle" fill="#6F7680" font-family="' + family + '" font-size="11">AA Legal Index Score</text>';

    // Pareto line: DeepSeek -> Kimi -> Gemini -> Claude.
    const pareto = data.points.slice().sort(function (a, b) { return a.cost - b.cost; });
    const points = pareto.map(function (point) {
      return x(point.cost).toFixed(1) + ',' + y(point.score).toFixed(1);
    }).join(' ');
    out += '<polyline points="' + points + '" fill="none" stroke="#2B7A8B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.8"></polyline>';

    data.points.forEach(function (point) {
      const px = x(point.cost);
      const py = y(point.score);
      if (point.highlight) {
        out += '<circle cx="' + px + '" cy="' + py + '" r="13" fill="#2B7A8B" opacity="0.16"></circle>';
      }
      out += '<circle cx="' + px + '" cy="' + py + '" r="' + (point.highlight ? 7 : 5.5) + '" fill="' + point.tone + '" stroke="#F8F7F4" stroke-width="2"></circle>';
    });

    out += '</svg>';
    return out;
  }

  function renderBenchmarks() {
    const data = LEGAL_BENCHMARK;
    const chart = document.getElementById("benchLegalChart");
    const legend = document.getElementById("benchLegalLegend");
    const source = document.getElementById("benchSource");
    const callout = document.getElementById("benchCallout");
    if (chart) chart.innerHTML = renderLegalIndex(data);
    if (legend) {
      legend.innerHTML = data.points.map(function (point) {
        return '<li><span class="bench-dot" style="background:' + point.tone + '"></span><span class="bench-model">' + point.label + '</span><span class="bench-value">' + point.score + ' · $' + point.cost.toFixed(2) + (point.provider ? ' · ' + point.provider : '') + '</span></li>';
      }).join("");
    }
    if (source) source.textContent = data.source;
    if (callout) callout.textContent = data.callout;
  }

  /* ------------------------------------------------------------------ */
  /* Intake + stream                                                     */
  /* ------------------------------------------------------------------ */

  function resetStreamUI() {
    els.streamLog.innerHTML = "";
    els.streamLog.setAttribute("aria-busy", "false");
    setProgress(0);
    els.streamFile.hidden = true;
    els.streamFile.textContent = "";
  }

  function setProgress(pct) {
    els.streamFill.style.width = pct + "%";
    els.streamPct.textContent = Math.round(pct) + "%";
    els.streamBar.setAttribute("aria-valuenow", String(Math.round(pct)));
  }

  function stopStream() {
    state.streamTimers.forEach(function (id) {
      window.clearTimeout(id);
    });
    state.streamTimers = [];
    if (state.streamTicker) {
      window.clearInterval(state.streamTicker);
      state.streamTicker = null;
    }
  }

  function renderStreamSteps(steps) {
    els.streamLog.innerHTML = "";
    els.streamLog.setAttribute("aria-busy", "true");
    steps.forEach(function (step) {
      const li = document.createElement("li");
      li.className = "stream-step is-pending";
      li.setAttribute("data-step", step.id);
      li.innerHTML =
        '<span class="step-index">' + step.num + "</span>" +
        '<div class="step-body">' +
        '<p class="step-title">' + step.title + "</p>" +
        '<p class="step-detail" hidden></p>' +
        '<p class="step-state">Queued</p>' +
        "</div>" +
        '<span class="step-marker" aria-hidden="true"></span>';
      els.streamLog.appendChild(li);
    });
  }

  function stepElement(id) {
    return els.streamLog.querySelector('.stream-step[data-step="' + id + '"]');
  }

  function completeStreamStep(id, doneDetail) {
    const li = stepElement(id);
    if (!li) return;
    li.classList.remove("is-active");
    li.classList.add("is-done");
    li.removeAttribute("aria-current");
    const stateEl = $(".step-state", li);
    if (stateEl) stateEl.hidden = true;
    const detail = $(".step-detail", li);
    if (detail && doneDetail) {
      detail.hidden = false;
      detail.innerHTML = doneDetail;
    }
  }

  function activateStreamStep(id, detail) {
    $$(".stream-step.is-active", els.streamLog).forEach(function (active) {
      const activeId = active.getAttribute("data-step");
      if (activeId !== id) completeStreamStep(activeId);
    });
    const li = stepElement(id);
    if (!li) return;
    li.classList.remove("is-pending", "is-done");
    li.classList.add("is-active");
    li.setAttribute("aria-current", "step");
    const stateEl = $(".step-state", li);
    if (stateEl) stateEl.hidden = true;
    const detailEl = $(".step-detail", li);
    if (detailEl) {
      detailEl.hidden = false;
      detailEl.innerHTML = detail;
    }
  }

  function demoStats() {
    return { pages: DEMO_STATS.pages, files: DEMO_STATS.files, real: false };
  }

  function uploadedStats() {
    if (!state.upload) return null;
    return { pages: state.upload.pages, files: state.upload.files, real: true };
  }

  function clearParseHold() {
    if (state.parseHold) {
      window.clearTimeout(state.parseHold);
      state.parseHold = null;
    }
  }

  function updateWorkbenchMarker(stats) {
    if (!els.workbenchUploadMarker || !els.workbenchUploadMeta) return;
    const real = !!(stats && stats.real);
    els.workbenchUploadMarker.hidden = !real;
    els.workbenchUploadMarker.title = real
      ? "PDF files were parsed locally; adjudication figures remain the synthetic Claim #9941 demo."
      : "";
    els.workbenchUploadMeta.textContent = real
      ? "LOCAL PDF · " + pageLabel(stats.pages).toUpperCase() + " · " + (stats.files + " FILE" + (stats.files === 1 ? "" : "S"))
      : "";
  }

  function startStream(fileName, stats) {
    clearParseHold();
    stats = stats || demoStats();
    stopStream();
    resetStreamUI();
    els.intake.hidden = true;
    els.stream.hidden = false;
    els.workbench.hidden = true;
    window.scrollTo(0, 0);
    if (els.streamTitle) {
      els.streamTitle.textContent = stats.real ? "Reading local PDF packet" : "Reading Claim #9941";
    }
    updateWorkbenchMarker(stats);

    if (fileName) {
      els.streamFile.hidden = false;
      els.streamFile.textContent = "Packet: " + fileName;
    }

    const steps = buildStreamSteps(stats.pages, stats.files);
    renderStreamSteps(steps);
    state.streamStart = performance.now();

    steps.forEach(function (step) {
      state.streamTimers.push(
        window.setTimeout(function () {
          activateStreamStep(step.id, step.detail);
        }, step.at)
      );
      if (step.doneAt) {
        state.streamTimers.push(
          window.setTimeout(function () {
            completeStreamStep(step.id, step.doneDetail);
          }, step.doneAt)
        );
      }
    });

    state.streamTicker = window.setInterval(function () {
      const elapsed = performance.now() - state.streamStart;
      const pct = Math.min(100, (elapsed / STREAM_DURATION) * 100);
      setProgress(pct);
    }, 80);

    state.streamTimers.push(
      window.setTimeout(function () {
        completeStreamStep("funding");
        revealWorkbench();
      }, STREAM_DURATION)
    );
  }

  function showWorkbench(scrollToTop) {
    els.intake.hidden = true;
    els.stream.hidden = true;
    els.howItWorks.hidden = true;
    const wasHidden = els.workbench.hidden;
    els.workbench.hidden = false;
    if (wasHidden) {
      els.workbench.classList.remove("workbench-in");
      void els.workbench.offsetWidth;
      els.workbench.classList.add("workbench-in");
    }
    if (scrollToTop !== false) window.scrollTo(0, 0);
  }

  function revealWorkbench() {
    stopStream();
    setProgress(100);
    els.streamLog.setAttribute("aria-busy", "false");
    showWorkbench();
    if (!location.hash || location.hash === "#intake") {
      history.pushState(null, "", "#workbench");
    }
    updateNavActive("workbench");
  }

  function skipToWorkbench() {
    clearParseHold();
    stopStream();
    els.streamLog.setAttribute("aria-busy", "false");
    showWorkbench();
    if (location.hash !== "#workbench") {
      history.pushState(null, "", "#workbench");
    }
    updateNavActive("workbench");
  }

  function formatMegabytes(bytes) {
    const mb = bytes / (1024 * 1024);
    return (mb >= 1 ? mb.toFixed(1) : mb.toFixed(3)) + " MB";
  }

  function hasPdfMagic(bytes) {
    return (
      bytes.length >= 5 &&
      bytes[0] === 0x25 &&
      bytes[1] === 0x50 &&
      bytes[2] === 0x44 &&
      bytes[3] === 0x46 &&
      bytes[4] === 0x2d
    );
  }

  function resetUploadState() {
    state.parseToken += 1;
    state.parsing = false;
    clearParseHold();
    state.upload = null;
    els.fileLine.hidden = true;
    els.fileMeta.textContent = "";
    els.fileName.textContent = "";
    els.fileInput.value = "";
    els.parseLine.hidden = true;
    els.parseLine.textContent = "";
    els.pdfState.hidden = true;
    els.pdfPreview.open = false;
    els.pdfPreviewText.textContent = "";
    els.pdfPageTags.innerHTML = "";
    els.dropzone.removeAttribute("aria-busy");
    updateWorkbenchMarker(null);
  }

  function setParsingStatus(fileCount, pages) {
    els.parseLine.hidden = false;
    els.parseLine.textContent =
      "Parsing " + pdfLabel(fileCount) + "…" + (pages ? " " + pageLabel(pages) : "");
  }

  async function sha256Preview(bytes) {
    if (typeof bytes === "undefined") return null;
    try {
      if (!(window.crypto && window.crypto.subtle && window.crypto.subtle.digest)) return null;
      const digest = await window.crypto.subtle.digest("SHA-256", bytes);
      return Array.prototype.slice
        .call(new Uint8Array(digest), 0, 6)
        .map(function (byte) {
          return byte.toString(16).padStart(2, "0");
        })
        .join("");
    } catch (error) {
      return null;
    }
  }

  async function parsePdfFiles(files) {
    if (state.parsing) {
      toast("Parsing already in progress", "Wait for the current PDF parse to finish.");
      return;
    }
    if (!window.pdfjsLib) {
      toast("PDF parser unavailable", "The local PDF.js runtime did not load. Reload and try again.");
      return;
    }

    resetUploadState();
    const token = state.parseToken;
    state.parsing = true;
    els.dropzone.setAttribute("aria-busy", "true");
    setParsingStatus(files.length, 0);

    try {
      const entries = [];
      let totalBytes = 0;
      for (let index = 0; index < files.length; index += 1) {
        const file = files[index];
        if (!/\.pdf$/i.test(file.name) && file.type !== "application/pdf") {
          throw new Error(file.name + " is not a PDF file.");
        }
        const bytes = new Uint8Array(await file.arrayBuffer());
        if (!hasPdfMagic(bytes)) {
          throw new Error(file.name + " is not a valid PDF (missing %PDF- header).");
        }
        entries.push({ file: file, bytes: bytes });
        totalBytes += bytes.byteLength;
      }

      if (token !== state.parseToken) return;

      const combined = new Uint8Array(totalBytes);
      let offset = 0;
      entries.forEach(function (entry) {
        combined.set(entry.bytes, offset);
        offset += entry.bytes.byteLength;
      });
      const hash = await sha256Preview(combined);
      if (token !== state.parseToken) return;

      const pages = [];
      const firstPageTexts = [];
      let totalPages = 0;

      for (let entryIndex = 0; entryIndex < entries.length; entryIndex += 1) {
        const entry = entries[entryIndex];
        const loadingTask = window.pdfjsLib.getDocument({
          data: entry.bytes.slice(),
          isEvalSupported: false
        });
        const pdf = await loadingTask.promise;
        try {
          for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
            if (token !== state.parseToken) return;
            const page = await pdf.getPage(pageNumber);
            const textContent = await page.getTextContent();
            let text = "";
            textContent.items.forEach(function (item) {
              if (typeof item.str === "string") {
                text += item.str;
                text += item.hasEOL ? "\n" : " ";
              }
            });
            text = text.replace(/[ \t]+/g, " ").replace(/\s*\n\s*/g, "\n").trim();
            if (entryIndex === 0 && pageNumber === 1) firstPageTexts.push(text);
            totalPages += 1;
            pages.push({
              file: entry.file.name,
              filePage: pageNumber,
              page: totalPages
            });
            setParsingStatus(files.length, totalPages);
            page.cleanup();
          }
        } finally {
          try {
            await pdf.destroy();
          } catch (error) {
            /* Ignore teardown errors after a successful extraction. */
          }
        }
      }

      if (token !== state.parseToken) return;

      const hashLabel = hash ? "SHA-256 " + hash + "…" : "hash unavailable";
      const summary =
        pdfLabel(entries.length) +
        " · " +
        pageLabel(totalPages) +
        " · " +
        formatMegabytes(totalBytes) +
        " · " +
        hashLabel;
      const fileNames = entries.map(function (entry) {
        return entry.file.name;
      }).join(" · ");
      const firstPage = firstPageTexts[0] || "No selectable text found on page 1.";

      state.upload = {
        files: entries.length,
        pages: totalPages
      };

      els.fileMeta.textContent = summary;
      els.fileName.textContent = fileNames;
      els.fileLine.hidden = false;
      els.pdfChip.textContent = "PDF verified · local parse";
      els.pdfPreviewText.textContent = firstPage.slice(0, 1200);
      els.pdfPageTags.innerHTML = "";
      pages.forEach(function (page) {
        const tag = document.createElement("span");
        tag.className = "pdf-page-tag";
        tag.textContent = "p. " + page.page;
        tag.title = page.file + " · page " + page.filePage;
        els.pdfPageTags.appendChild(tag);
      });
      els.pdfPreview.open = false;
      els.pdfState.hidden = false;
      els.parseLine.hidden = true;
      els.parseLine.textContent = "";
      els.dropzone.removeAttribute("aria-busy");
      state.parsing = false;

      state.parseHold = window.setTimeout(function () {
        if (token !== state.parseToken) return;
        startStream(pdfLabel(entries.length) + " · " + pageLabel(totalPages), {
          pages: totalPages,
          files: entries.length,
          real: true
        });
      }, 2400);
    } catch (error) {
      if (token !== state.parseToken) return;
      state.parsing = false;
      els.dropzone.removeAttribute("aria-busy");
      els.parseLine.hidden = true;
      els.parseLine.textContent = "";
      els.fileInput.value = "";
      toast("PDF parse failed", (error && error.message) || "The selected PDF could not be parsed.");
    }
  }

  function handleFiles(files) {
    if (!files || !files.length) {
      toast("No PDF selected", "Choose one or more PDF files to parse locally.");
      return;
    }
    if (state.parsing) {
      toast("Parsing already in progress", "Wait for the current PDF parse to finish.");
      return;
    }
    parsePdfFiles(Array.prototype.slice.call(files));
  }

  els.simulate.addEventListener("click", function () {
    if (state.parsing) {
      toast("Parsing already in progress", "Wait for the current PDF parse to finish.");
      return;
    }
    startStream("Claim #9941 · 4 PDFs · 312 pages", demoStats());
  });

  els.skipWorkbench.addEventListener("click", skipToWorkbench);
  els.skipStream.addEventListener("click", revealWorkbench);

  els.dropzone.addEventListener("click", function () {
    els.fileInput.click();
  });

  els.dropzone.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      els.fileInput.click();
    }
  });

  els.fileInput.addEventListener("change", function () {
    const files = Array.prototype.slice.call(els.fileInput.files || []);
    els.fileInput.value = "";
    handleFiles(files);
  });

  ["dragenter", "dragover"].forEach(function (name) {
    els.dropzone.addEventListener(name, function (event) {
      event.preventDefault();
      els.dropzone.classList.add("is-over");
    });
  });

  ["dragleave", "dragend"].forEach(function (name) {
    els.dropzone.addEventListener(name, function () {
      els.dropzone.classList.remove("is-over");
    });
  });

  els.dropzone.addEventListener("drop", function (event) {
    event.preventDefault();
    els.dropzone.classList.remove("is-over");
    const files = event.dataTransfer && event.dataTransfer.files
      ? Array.prototype.slice.call(event.dataTransfer.files)
      : [];
    handleFiles(files);
  });

  els.rerun.addEventListener("click", function () {
    const stats = uploadedStats();
    if (stats) {
      startStream(pdfLabel(stats.files) + " · " + pageLabel(stats.pages), stats);
      logAction("Agent stream re-run", "Local PDF packet · " + pageLabel(stats.pages));
    } else {
      startStream("Claim #9941 · 4 PDFs · 312 pages", demoStats());
      logAction("Agent stream re-run", "Claim #9941 packet");
    }
  });

  function showIntake() {
    stopStream();
    els.stream.hidden = true;
    els.workbench.hidden = true;
    els.howItWorks.hidden = true;
    els.intake.hidden = false;
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }

  function showHowItWorks() {
    stopStream();
    els.stream.hidden = true;
    els.workbench.hidden = true;
    els.intake.hidden = true;
    els.howItWorks.hidden = false;
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
    window.setTimeout(function () {
      window.scrollTo({ top: 0, left: 0, behavior: "instant" });
    }, 80);
  }

  els.newClaim.addEventListener("click", function () {
    resetStreamUI();
    resetClaimState();
    showIntake();
    if (location.hash !== "#intake") {
      history.pushState(null, "", "#intake");
    }
    updateNavActive("intake");
  });

  function resetClaimState() {
    els.cfo.checked = false;
    els.carrier.checked = false;
    state.cured = false;
    state.cureSentAt = null;
    state.cureSentSignatures = null;
    state.pushedStage = null;
    state.pushedAt = null;
    state.pushedStageCode = null;
    state.pushedApproved = null;
    state.pushCount = 0;
    state.rawOpen = false;
    els.rawPayload.hidden = true;
    els.rawToggle.setAttribute("aria-expanded", "false");
    els.auditList.innerHTML = '<li class="audit-empty">No actions recorded yet.</li>';
    const announce = document.getElementById("cureAnnounce");
    if (announce) announce.textContent = "";
    resetUploadState();
    if (els.outboundPack) {
      els.outboundPack.classList.remove("is-sent");
      els.packStamp.hidden = true;
      els.packStamp.textContent = "SENT";
    }
    selectPackTab("packTabTpa");
    updateUI(false);
  }

  /* ------------------------------------------------------------------ */
  /* Trap expansion                                                      */
  /* ------------------------------------------------------------------ */

  $$(".trap-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const trap = btn.closest(".trap");
      const panel = document.getElementById(btn.getAttribute("data-controls") || btn.getAttribute("aria-controls"));
      const open = !trap.classList.contains("is-open");
      trap.classList.toggle("is-open", open);
      btn.setAttribute("aria-expanded", String(open));
      if (panel) {
        panel.inert = !open;
        panel.setAttribute("aria-hidden", String(!open));
      }
      logAction(
        (open ? "Rationale expanded" : "Rationale collapsed"),
        trap.getAttribute("data-trap") === "laser"
          ? "Endorsement L-1"
          : trap.getAttribute("data-trap") === "fl48"
          ? "FL48"
          : "Signature hold"
      );
    });
  });

  /* ------------------------------------------------------------------ */
  /* Evidence drawer                                                     */
  /* ------------------------------------------------------------------ */

  const FOCUSABLE =
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex="-1"])';

  function renderDrawer(doc) {
    const data = DOCS[doc];
    if (!data) return;
    els.drawerType.textContent = data.label;
    els.drawerTitle.textContent = data.title;
    els.drawerSub.textContent = data.sub;
    els.drawerPage.textContent = data.page;
    els.drawerBody.innerHTML =
      (state.drawerView === "formatted" ? data.formatted : data.markdown) +
      '<div class="tech-cite"><details><summary>Technical citation</summary><pre>' +
      data.bbox +
      "</pre></details></div>" +
      '<div class="drawer-citation">' +
      data.citation +
      "</div>";
  }

  function setDrawerView(view) {
    state.drawerView = view;
    const formatted = view === "formatted";
    els.viewFormatted.classList.toggle("is-active", formatted);
    els.viewMarkdown.classList.toggle("is-active", !formatted);
    els.viewFormatted.setAttribute("aria-pressed", String(formatted));
    els.viewMarkdown.setAttribute("aria-pressed", String(!formatted));
    renderDrawer(state.drawerDoc);
    els.drawerBody.scrollTop = 0;
  }

  els.viewFormatted.addEventListener("click", function () {
    if (state.drawerView === "formatted") return;
    setDrawerView("formatted");
    logAction("Evidence view switched", "Formatted PDF View");
  });

  els.viewMarkdown.addEventListener("click", function () {
    if (state.drawerView === "markdown") return;
    setDrawerView("markdown");
    logAction("Evidence view switched", "Extracted Markdown");
  });

  function openDrawer(doc, opener) {
    const data = DOCS[doc];
    if (!data) return;

    state.drawerDoc = doc;
    state.drawerOpener = opener || document.activeElement;
    state.drawerOpen = true;
    document.body.style.overflow = "hidden";

    setDrawerView("formatted");

    els.drawer.hidden = false;
    els.drawerBackdrop.hidden = false;
    // Two frames so the enter transition always plays.
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        els.drawer.classList.add("is-open");
        els.drawerBackdrop.classList.add("is-open");
      });
    });

    els.drawerClose.focus();
    logAction("Evidence opened", data.title + " · " + data.page);
  }

  function closeDrawer() {
    if (!state.drawerOpen) return;
    state.drawerOpen = false;
    els.drawer.classList.remove("is-open");
    els.drawerBackdrop.classList.remove("is-open");
    document.body.style.overflow = "";

    const restore = state.drawerOpener;
    window.setTimeout(function () {
      if (!state.drawerOpen) {
        els.drawer.hidden = true;
        els.drawerBackdrop.hidden = true;
      }
    }, 350);

    if (restore && typeof restore.focus === "function" && document.contains(restore)) {
      restore.focus();
    }
  }

  $$("[data-doc]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      openDrawer(btn.getAttribute("data-doc"), btn);
    });
  });

  els.drawerClose.addEventListener("click", closeDrawer);
  els.drawerBackdrop.addEventListener("click", closeDrawer);

  function trapTab(container, event) {
    const focusable = $$(FOCUSABLE, container).filter(function (el) {
      return el.offsetWidth > 0 || el.offsetHeight > 0 || el === document.activeElement;
    });
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  document.addEventListener("keydown", function (event) {
    if (state.mediaOpen) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMedia();
        return;
      }
      if (event.key === "Tab") trapTab(els.mediaModal, event);
      return;
    }

    if (state.chatOpen) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeChat();
        return;
      }
      if (event.key === "Tab") trapTab(els.chatDrawer, event);
      return;
    }

    if (state.dialogOpen) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeDialog();
        return;
      }
      if (event.key === "Tab") trapTab(els.dialog, event);
      return;
    }

    if (!state.drawerOpen) return;

    if (event.key === "Escape") {
      event.preventDefault();
      closeDrawer();
      return;
    }

    if (event.key === "Tab") trapTab(els.drawer, event);
  });

  /* ------------------------------------------------------------------ */
  /* Confirmation / receipt dialog                                       */
  /* ------------------------------------------------------------------ */

  function facts(rows) {
    return (
      '<dl class="dialog-facts">' +
      rows
        .map(function (row) {
          return "<div><dt>" + row[0] + "</dt><dd>" + row[1] + "</dd></div>";
        })
        .join("") +
      "</dl>"
    );
  }

  function openDialog(options) {
    if (state.dialogOpen) return;
    state.dialogOpen = true;
    state.dialogOpener = document.activeElement;
    state.dialogPrimaryAction = options.onPrimary || null;
    state.dialogSecondaryAction = options.onSecondary || null;

    els.dialogKicker.textContent = options.kicker || "Confirm";
    els.dialogTitle.textContent = options.title || "Confirm action";
    els.dialogBody.innerHTML = options.body || "";
    els.dialogPrimary.textContent = options.primaryLabel || "Confirm";
    if (options.secondaryLabel) {
      els.dialogSecondary.hidden = false;
      els.dialogSecondary.textContent = options.secondaryLabel;
    } else {
      els.dialogSecondary.hidden = true;
    }

    document.body.style.overflow = "hidden";
    els.dialog.hidden = false;
    els.dialogBackdrop.hidden = false;
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        els.dialog.classList.add("is-open");
        els.dialogBackdrop.classList.add("is-open");
      });
    });
    els.dialogPrimary.focus();
  }

  function closeDialog() {
    if (!state.dialogOpen) return;
    state.dialogOpen = false;
    els.dialog.classList.remove("is-open");
    els.dialogBackdrop.classList.remove("is-open");
    document.body.style.overflow = state.drawerOpen ? "hidden" : "";

    const restore = state.dialogOpener;
    window.setTimeout(function () {
      if (!state.dialogOpen) {
        els.dialog.hidden = true;
        els.dialogBackdrop.hidden = true;
        els.dialogBody.innerHTML = "";
      }
    }, 250);

    if (restore && typeof restore.focus === "function" && document.contains(restore)) {
      restore.focus();
    }
  }

  function runDialogAction(which) {
    const action = which === "primary" ? state.dialogPrimaryAction : state.dialogSecondaryAction;
    closeDialog();
    if (action) action();
  }

  els.dialogClose.addEventListener("click", closeDialog);
  els.dialogBackdrop.addEventListener("click", closeDialog);
  els.dialogPrimary.addEventListener("click", function () {
    runDialogAction("primary");
  });
  els.dialogSecondary.addEventListener("click", function () {
    runDialogAction("secondary");
  });

  function openMedia(title, contentHtml) {
    if (state.mediaOpen) return;
    state.mediaOpen = true;
    state.mediaOpener = document.activeElement;
    els.mediaTitle.textContent = title;
    els.mediaScroll.innerHTML = contentHtml;
    els.mediaScroll.scrollTop = 0;
    els.mediaScroll.scrollLeft = 0;
    document.body.style.overflow = "hidden";
    els.mediaModal.hidden = false;
    els.mediaBackdrop.hidden = false;
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        els.mediaModal.classList.add("is-open");
        els.mediaBackdrop.classList.add("is-open");
      });
    });
    els.mediaClose.focus();
  }

  function closeMedia() {
    if (!state.mediaOpen) return;
    state.mediaOpen = false;
    els.mediaModal.classList.remove("is-open");
    els.mediaBackdrop.classList.remove("is-open");
    document.body.style.overflow = "";
    const restore = state.mediaOpener;
    window.setTimeout(function () {
      if (!state.mediaOpen) {
        els.mediaModal.hidden = true;
        els.mediaBackdrop.hidden = true;
        els.mediaScroll.innerHTML = "";
      }
    }, 250);
    if (restore && typeof restore.focus === "function" && document.contains(restore)) {
      restore.focus();
    }
  }

  els.mediaClose.addEventListener("click", closeMedia);
  els.mediaBackdrop.addEventListener("click", closeMedia);

  if (els.expandDiagram) {
    els.expandDiagram.addEventListener("click", function () {
      openMedia(
        "Architecture flow",
        '<object class="media-diagram" type="image/svg+xml" data="assets/diagrams/claimcatch-flow.svg" aria-label="Expanded ClaimCatch architecture: TPA claim packet, Mistral OCR, Fireworks AI, ground-truth verification, zero-PHI sanitizer, human analyst review and sign-off, and draft HubSpot, finance, and TPA outputs."><p class="media-diagram-fallback">Expand the architecture diagram in a browser that supports SVG objects.</p></object>'
      );
    });
  }

  /* ------------------------------------------------------------------ */
  /* Ask Packet chat                                                     */
  /* ------------------------------------------------------------------ */

  const CHAT_TEAMS_UPDATE =
    "Teams update — Claim #9941\n" +
    "• Tranche 1: $1,700,000 approved for Finance/Accounting disbursement.\n" +
    "• Tranche 2: $250,000 held pending Employer CFO + carrier countersignatures; curable.\n" +
    "• L-1: $500,000 laser gap (non-curable); FL48 $350,000 excluded.\n" +
    "No clinical data. Claimant key only: MPM-9941-07.";

  function chatScroll() {
    requestAnimationFrame(function () {
      els.chatThread.scrollTop = els.chatThread.scrollHeight;
    });
  }

  function chatUserMessage(text) {
    const empty = $("#chatEmpty");
    if (empty) empty.remove();
    const msg = document.createElement("div");
    msg.className = "chat-msg user";
    msg.textContent = text;
    els.chatThread.appendChild(msg);
    els.chatDrawer.classList.add("has-thread");
    chatScroll();
  }

  function chatToolPill(text) {
    const pill = document.createElement("div");
    pill.className = "chat-tool";
    pill.textContent = text;
    els.chatThread.appendChild(pill);
    chatScroll();
  }

  function chatTyping() {
    const typing = document.createElement("div");
    typing.className = "chat-typing";
    typing.innerHTML = "<span></span><span></span><span></span>";
    els.chatThread.appendChild(typing);
    chatScroll();
    return typing;
  }

  function chatAnswer(html) {
    const msg = document.createElement("div");
    msg.className = "chat-msg agent";
    msg.innerHTML = html;
    els.chatThread.appendChild(msg);
    chatScroll();
  }

  const CHAT_ANSWERS = {
    1:
      "<p>No No-New-Laser endorsement is in the executed packet. The anti-assignment clause is Policy §7.4 (p. 3): “YOU may not assign reimbursement under this POLICY, and WE shall not recognize any such assignment.” Endorsement L-1 (p. 7) is the only laser: $750,000 separate specific deductible on MPM-9941-07 — $500,000 above the $250,000 Schedule A base.</p>" +
      '<div class="chat-cites"><button type="button" class="chat-cite" data-chat-doc="policy">[Policy p. 7]</button><button type="button" class="chat-cite" data-chat-doc="policyAssignment">[Policy p. 3]</button></div>',
    2:
      "<p>Q2042 Kymriah is covered because it matches the FDA label (B-ALL, age ≤25) and CMS NCD 110.24; the $475,000 line carries no FL48. The CD22 CAR-T is Rev 0256/J9999 under protocol MPM-RES-2026-014 — investigational, no FDA approval or NCD coverage — billed FL48 $235,000. The other $115,000 FL48 is off-label pembrolizumab ($40k), deluxe differential ($25k), and convenience ($50k).</p>" +
      '<div class="chat-cites"><button type="button" class="chat-cite" data-chat-doc="ub04">[UB-04 p. 2]</button><button type="button" class="chat-cite" data-chat-doc="ub04">[UB-04 p. 4]</button><a class="chat-cite" href="https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=110.24" target="_blank" rel="noopener">CMS NCD 110.24</a></div>',
    3:
      "<p>Teams update — Claim #9941<br>• Tranche 1: $1,700,000 approved for Finance/Accounting disbursement.<br>• Tranche 2: $250,000 held pending Employer CFO + carrier countersignatures; curable.<br>• L-1: $500,000 laser gap (non-curable); FL48 $350,000 excluded.<br>No clinical data. Claimant key only: MPM-9941-07.</p>" +
      '<div class="chat-cites"><button type="button" class="chat-cite" data-chat-doc="tpa">[TPA request p. 3]</button><button type="button" class="chat-cite" data-chat-doc="policy">[Policy p. 7]</button></div>' +
      '<button type="button" class="chat-copy" data-chat-copy="teams">Copy update</button>',
    0:
      "<p>I can answer from the indexed packet: policy lasers, coverage, funding math, or a zero-PHI Teams update.</p>"
  };

  const CHAT_TOOLS = {
    1: "[MCP: check_policy_lasers]",
    2: "[MCP: check_cms_coverage_and_fda]",
    3: "[MCP: stage_zero_phi_hubspot_and_teams_handoff]"
  };

  function classifyChat(text) {
    const lower = text.toLowerCase();
    if (/no-new-laser|anti-assignment|assign|policy|laser|endorsement/.test(lower)) return 1;
    if (/kymriah|car-t|cd22|coverage|ncd|fda|fl48/.test(lower)) return 2;
    if (/teams|hold|signature|tranche|cure|update/.test(lower)) return 3;
    return 0;
  }

  function askChat(text, forcedId) {
    if (state.chatBusy) {
      toast("Packet Agent", "Still reading the packet. One question at a time.");
      return;
    }
    const id = typeof forcedId === "number" ? forcedId : classifyChat(text);
    state.chatBusy = true;
    chatUserMessage(text);
    if (id) chatToolPill(CHAT_TOOLS[id]);
    const typing = chatTyping();
    window.setTimeout(function () {
      typing.remove();
      chatAnswer(CHAT_ANSWERS[id] || CHAT_ANSWERS[0]);
      state.chatBusy = false;
    }, 800);
  }

  function openChat() {
    if (state.chatOpen) return;
    state.chatOpen = true;
    state.chatOpener = document.activeElement;
    document.body.style.overflow = "hidden";
    els.chatDrawer.hidden = false;
    els.chatBackdrop.hidden = false;
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        els.chatDrawer.classList.add("is-open");
        els.chatBackdrop.classList.add("is-open");
      });
    });
    els.chatInput.focus();
  }

  function closeChat(restoreFocus) {
    if (!state.chatOpen) return;
    state.chatOpen = false;
    els.chatDrawer.classList.remove("is-open");
    els.chatBackdrop.classList.remove("is-open");
    document.body.style.overflow = "";
    const restore = state.chatOpener;
    window.setTimeout(function () {
      if (!state.chatOpen) {
        els.chatDrawer.hidden = true;
        els.chatBackdrop.hidden = true;
      }
    }, 300);
    if (restoreFocus !== false && restore && typeof restore.focus === "function" && document.contains(restore)) {
      restore.focus();
    }
  }

  els.askPacket.addEventListener("click", openChat);
  els.chatClose.addEventListener("click", function () {
    closeChat();
  });
  els.chatBackdrop.addEventListener("click", function () {
    closeChat();
  });

  $$("[data-open-chat]").forEach(function (button) {
    button.addEventListener("click", openChat);
  });

  $$(".chat-starter").forEach(function (button) {
    button.addEventListener("click", function () {
      if (state.chatBusy) {
        toast("Packet Agent", "Still reading the packet. One question at a time.");
        return;
      }
      askChat(button.textContent.trim(), Number(button.getAttribute("data-chat-prompt")));
    });
  });

  els.chatForm.addEventListener("submit", function (event) {
    event.preventDefault();
    if (state.chatBusy) {
      toast("Packet Agent", "Still reading the packet. One question at a time.");
      return;
    }
    const text = els.chatInput.value.trim();
    if (!text) {
      els.chatInput.focus();
      return;
    }
    els.chatInput.value = "";
    askChat(text);
  });

  els.chatInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      els.chatForm.requestSubmit();
    }
  });

  els.chatThread.addEventListener("click", function (event) {
    const cite = event.target.closest("[data-chat-doc]");
    if (cite) {
      const doc = cite.getAttribute("data-chat-doc");
      closeChat(false);
      window.setTimeout(function () {
        openDrawer(doc, els.askPacket);
      }, 300);
      return;
    }
    const copy = event.target.closest("[data-chat-copy]");
    if (copy) {
      copyDraftText(CHAT_TEAMS_UPDATE, "Teams update");
    }
  });

  /* ------------------------------------------------------------------ */
  /* Resolution                                                          */
  /* ------------------------------------------------------------------ */

  function onCureChange(which) {
    const wasCured = state.cured;
    const signatures =
      (els.cfo.checked ? 1 : 0) + (els.carrier.checked ? 1 : 0);
    const cured = signatures === 2;
    const label = which === "cfo" ? "Employer CFO signature" : "Carrier countersignature";
    const checked = which === "cfo" ? els.cfo.checked : els.carrier.checked;

    state.cured = cured;
    logAction((checked ? "Confirmed" : "Unchecked") + " — " + label, signatures + "/2 signatures");

    const cs = computeState();
    const live = document.getElementById("cureAnnounce");
    if (live) {
      live.textContent = cured
        ? "Signatures complete. Draft advance " + money(cs.approved) + ". Tranche 2 ready for human sign-off."
        : "Cure incomplete. Draft advance " + money(cs.approved) + ". Tranche 2 held.";
    }

    if (cured && !wasCured) {
      logAction(
        "Signatures complete — Tranche 2 ready for human sign-off",
        "Draft advance " + money(cs.approved) + " · stage " + cs.stage
      );
    } else if (!cured && wasCured) {
      logAction(
        "Signatures reverted — Tranche 2 held",
        "Draft advance " + money(cs.approved) + " · stage " + cs.stage
      );
    }

    updateUI({ animate: true });
  }

  els.cfo.addEventListener("change", function () {
    onCureChange("cfo");
  });
  els.carrier.addEventListener("change", function () {
    onCureChange("carrier");
  });

  function showCureReceipt() {
    const cs = computeState();
    openDialog({
      kicker: "Receipt",
      title: "Cure notice already sent",
      body:
        "<p><b>Already sent " + state.cureSentAt + " · " + state.cureSentSignatures +
        "/2 signatures · no additional write.</b></p>" +
        facts([
          ["Recipient", "Prairie States Administrators"],
          ["Request", "9941-A"],
          ["Draft advance", money(cs.approved)]
        ]),
      primaryLabel: "Close"
    });
  }

  function performCureSend() {
    if (state.cureSentAt) return;
    state.cureSentAt = timeStamp();
    const cs = computeState();
    state.cureSentSignatures = cs.signatures;
    logAction(
      "Cure notice sent to TPA",
      "Request 9941-A · Prairie States Administrators · " + cs.signatures + "/2 signatures"
    );
    toast("Cure notice sent", "Prairie States Administrators · " + state.cureSentAt);
    updateUI(false);
    markPackSent(state.cureSentAt);
  }

  function requestCureSend() {
    if (state.cureSentAt) {
      showCureReceipt();
      return;
    }
    const cs = computeState();
    openDialog({
      kicker: "Confirm",
      title: cs.cured
        ? "Send executed cure pack for records?"
        : "Send cure notice to Prairie States Administrators?",
      body: cs.cured
        ? "<p>Both signatures are on file. Send the executed cure pack to Prairie State for records?</p>" +
          facts([
            ["Draft advance", money(cs.approved)],
            ["Tranche 2 hold", money(cs.hold)],
            ["Signatures on file", cs.signatures + "/2"]
          ])
        : "<p>Request 9941-A will be sent for the Employer CFO signature and Meridian countersignature.</p>" +
          facts([
            ["Draft advance", money(cs.approved)],
            ["Curable hold", money(cs.hold)],
            ["Signatures on file", cs.signatures + "/2"]
          ]),
      primaryLabel: cs.cured ? "Send cure pack" : "Send Cure Notice",
      secondaryLabel: "Cancel",
      onPrimary: performCureSend
    });
  }

  els.sendCure.addEventListener("click", requestCureSend);

  /* Drafted outbound pack */
  function selectPackTab(tabId) {
    const tabs = $$(".outbound-tab");
    if (!tabs.length) return;
    let selected = tabs.find(function (tab) {
      return tab.id === tabId;
    });
    if (!selected) selected = tabs[0];
    tabs.forEach(function (tab) {
      const active = tab === selected;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      const panel = document.getElementById(tab.getAttribute("aria-controls"));
      if (panel) panel.hidden = !active;
    });
  }

  function markPackSent(time) {
    if (!els.outboundPack) return;
    els.outboundPack.classList.add("is-sent");
    els.packStamp.hidden = false;
    els.packStamp.textContent = "SENT · " + time;
    selectPackTab("packTabTpa");
  }

  function copyDraftText(text, label) {
    let copied = false;
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    area.style.top = "0";
    document.body.appendChild(area);
    area.select();
    try {
      copied = document.execCommand("copy");
    } catch (e) {
      copied = false;
    }
    area.remove();

    if (copied) {
      toast("Draft copied", label);
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () {
          toast("Draft copied", label);
        },
        function () {
          toast("Draft ready", label + " · select and copy");
        }
      );
      return;
    }
    toast("Draft ready", label + " · select and copy");
  }

  $$(".outbound-tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      selectPackTab(tab.id);
    });
    tab.addEventListener("keydown", function (event) {
      const tabs = $$(".outbound-tab");
      const index = tabs.indexOf(tab);
      let next = null;
      if (event.key === "ArrowRight") next = tabs[(index + 1) % tabs.length];
      else if (event.key === "ArrowLeft") next = tabs[(index - 1 + tabs.length) % tabs.length];
      else if (event.key === "Home") next = tabs[0];
      else if (event.key === "End") next = tabs[tabs.length - 1];
      if (!next) return;
      event.preventDefault();
      selectPackTab(next.id);
      next.focus();
    });
  });

  els.copyDraft.addEventListener("click", function () {
    const activeTab = $(".outbound-tab.is-active");
    if (!activeTab) return;
    const panel = document.getElementById(activeTab.getAttribute("aria-controls"));
    if (!panel) return;
    copyDraftText(panel.innerText.trim(), activeTab.textContent.trim());
  });

  /* ------------------------------------------------------------------ */
  /* HubSpot                                                             */
  /* ------------------------------------------------------------------ */

  function targetPushStage(cs) {
    return cs.cured ? "approved" : "hold";
  }

  function showPushReceipt() {
    openDialog({
      kicker: "Receipt",
      title: "HubSpot record already pushed",
      body:
        "<p><b>Already pushed " + state.pushedAt + " · " + state.pushedStageCode +
        " · no additional write.</b></p>" +
        facts([
          ["Draft total", money(state.pushedApproved)],
          ["PHI scan", "PASS · 0 fields"]
        ]),
      primaryLabel: "Close"
    });
  }

  function performPush(stage) {
    if (state.pushedStage === stage) return;
    const cs = computeState();
    if (stage !== targetPushStage(cs)) return;

    state.pushedStage = stage;
    state.pushedAt = timeStamp();
    state.pushedStageCode = cs.stage;
    state.pushedApproved = cs.approved;
    state.pushCount += 1;

    logAction(
      stage === "approved"
        ? "Staged sign-off-ready record in HubSpot"
        : "Staged hold record in HubSpot",
      "stage " + cs.stage + " · draft advance " + money(cs.approved) + " · zero PHI"
    );
    toast(
      "HubSpot record staged",
      (stage === "approved" ? "Sign-off-ready draft" : "Hold stage") + " · " + money(cs.approved)
    );
    updateUI(false);
  }

  function requestPush() {
    const cs = computeState();
    const target = targetPushStage(cs);

    if (state.pushedStage === target || state.pushCount >= 2) {
      showPushReceipt();
      return;
    }

    const isUpdate = Boolean(state.pushedStage);

    if (target === "hold") {
      openDialog({
        kicker: "Confirm",
        title: isUpdate ? "Push the current hold record?" : "Push the hold-stage record?",
        body:
          "<p>Tranche 2 is still held. Push the hold-stage record now, or cure the two signatures first?</p>" +
          facts([
            ["Draft total", money(cs.approved)],
            ["Tranche 2 hold", money(cs.hold)],
            ["Employer CFO", "Missing"],
            ["Carrier countersignature", "Missing"]
          ]),
        primaryLabel: "Push hold record",
        secondaryLabel: "Return to cure",
        onPrimary: function () {
          performPush("hold");
        },
        onSecondary: function () {
          els.cfo.focus();
          const card = els.cfo.closest(".check");
          if (card) card.scrollIntoView({ block: "center", behavior: reducedMotion ? "auto" : "smooth" });
        }
      });
      return;
    }

    openDialog({
      kicker: "Confirm",
      title: isUpdate ? "Push the updated sign-off-ready draft?" : "Approve and push the sign-off-ready draft?",
      body:
        "<p>Draft advance <b>" + money(cs.approved) + "</b>. Both signatures are on file; human sign-off is the next gate.</p>" +
        facts([
          ["Employer CFO", "Signed"],
          ["Carrier", "Countersigned"],
          ["Tranche 2 hold", money(cs.hold)],
          ["Stage", cs.stage]
        ]),
      primaryLabel: isUpdate ? "Push updated record" : "Approve & Push",
      secondaryLabel: "Cancel",
      onPrimary: function () {
        performPush("approved");
      }
    });
  }

  els.push.addEventListener("click", requestPush);

  els.rawToggle.addEventListener("click", function () {
    state.rawOpen = !state.rawOpen;
    els.rawToggle.setAttribute("aria-expanded", String(state.rawOpen));
    els.rawPayload.hidden = !state.rawOpen;
    if (state.rawOpen) {
      els.rawCode.textContent = JSON.stringify(buildPayload(), null, 2);
    }
    logAction(
      state.rawOpen ? "Raw JSON payload viewed" : "Raw JSON payload hidden",
      "catastrophic_claim 9941"
    );
  });

  /* ------------------------------------------------------------------ */
  /* Hash routing                                                        */
  /* ------------------------------------------------------------------ */

  function updateNavActive(name) {
    let activeLink = null;
    $$(".nav-links a").forEach(function (link) {
      const href = (link.getAttribute("href") || "").replace("#", "");
      const active = href === name;
      link.classList.toggle("is-active", active);
      if (active) {
        link.setAttribute("aria-current", "page");
        activeLink = link;
      } else {
        link.removeAttribute("aria-current");
      }
    });

    const nav = $(".nav-links");
    function alignActive() {
      if (!activeLink || !nav || nav.scrollWidth <= nav.clientWidth + 1) return;
      const navRect = nav.getBoundingClientRect();
      const linkRect = activeLink.getBoundingClientRect();
      const leftOffset = linkRect.left - navRect.left + nav.scrollLeft;
      const rightOffset = leftOffset + linkRect.width;
      if (leftOffset < nav.scrollLeft + 12) {
        nav.scrollLeft = Math.max(0, leftOffset - 12);
      } else if (rightOffset > nav.scrollLeft + nav.clientWidth - 24) {
        nav.scrollLeft = rightOffset - nav.clientWidth + 24;
      }
    }
    alignActive();
    requestAnimationFrame(alignActive);
    window.setTimeout(alignActive, 120);
  }

  function scrollToSection(id) {
    const target = document.getElementById(id);
    if (!target) return;
    target.scrollIntoView({
      behavior: reducedMotion ? "auto" : "smooth",
      block: "start"
    });
  }

  function route() {
    if (state.mediaOpen) closeMedia();
    if (state.chatOpen) closeChat(false);
    if (state.dialogOpen) closeDialog();
    const name = (location.hash || "").replace(/^#/, "");

    if (!name || name === "intake") {
      showIntake();
      updateNavActive("intake");
      return;
    }

    if (name === "how-it-works") {
      showHowItWorks();
      updateNavActive("how-it-works");
      return;
    }

    els.howItWorks.hidden = true;
    if (els.workbench.hidden) {
      showWorkbench(false);
    } else {
      els.intake.hidden = true;
      els.stream.hidden = true;
    }

    if (name === "resolution" || name === "evidence") {
      requestAnimationFrame(function () {
        window.setTimeout(function () {
          scrollToSection(name);
        }, 40);
      });
    } else {
      window.scrollTo({ top: 0, left: 0, behavior: "instant" });
      window.setTimeout(function () {
        window.scrollTo({ top: 0, left: 0, behavior: "instant" });
      }, 80);
    }
    updateNavActive(name);
  }

  function navigate(hash) {
    if (location.hash === hash) {
      route();
      return;
    }
    history.pushState(null, "", hash);
    route();
  }

  window.addEventListener("hashchange", route);
  window.addEventListener("popstate", route);

  $$("a[data-nav]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      navigate(link.getAttribute("href"));
    });
  });

  els.reviewTraps.addEventListener("click", function (event) {
    event.preventDefault();
    const cs = computeState();
    if (!cs.cured) {
      navigate("#evidence");
      return;
    }
    if (state.pushCount >= 2 || state.pushedStage === "approved") {
      navigate("#resolution");
      window.setTimeout(function () {
        const panel = $(".hubspot-panel");
        if (panel) {
          panel.scrollIntoView({
            block: "center",
            behavior: reducedMotion ? "auto" : "smooth"
          });
        }
        els.push.focus();
      }, 320);
      return;
    }
    requestPush();
  });

  /* Initialize ambient values */
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () {
      updateNavActive((location.hash || "").replace(/^#/, "") || "intake");
    });
  }
  window.addEventListener("resize", function () {
    updateNavActive((location.hash || "").replace(/^#/, "") || "intake");
  });
  selectPackTab("packTabTpa");
  renderBenchmarks();
  updateUI(false);
  route();
})();
