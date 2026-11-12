<div align="center">
  <h1>Aegle Aura — Partner Ops</h1>
  <p><strong>High-speed stop-loss claim triaging with humans in the loop.</strong></p>
  <p>
    <a href="#the-vision">The Vision</a> •
    <a href="#quickstart">Quickstart</a> •
    <a href="#how-it-works">How It Works</a> •
    <a href="#rollout-roadmap">Roadmap</a>
  </p>
</div>

---

## The Vision

Reviewing a 300-page catastrophic claim packet takes hours of manually cross-referencing hospital billing codes, stop-loss policy schedules, laser endorsements, and clinical utilization notes before a funding advance can be safely approved.

**Aegle Aura** is an interactive proof-of-concept exploring what the future of Partner & Funding Operations at Aegle Capital looks like when analysts have an AI triage copilot doing the heavy lifting.

* **Endgame Workbench (`web/`):** A visual, interactive frontend concept where analysts drop in a massive claim packet and get an instant, citation-backed pre-audit, interactive chat overrides to recalculate math on the fly, and drafted partner communications ready for human sign-off.
* **Day-1 Practical Starting Point (`claimcatch_mcp.py`):** A lightweight suite of specialized legal and clinical verification tools built to plug directly into a self-hosted **LibreChat** workspace—giving analysts an immediate internal copilot before Aegle ever builds a custom frontend.

> [!NOTE]
> **100% Synthetic Proof of Concept:** Everything in this repo (including example `Claim #9941`) is fabricated to demonstrate the workflow and UI vision. Real patient data (PHI) would only ever run inside Aegle's own HIPAA-governed infrastructure.

---

## Quickstart

Spin up the interactive workbench in one command:

```bash
python3 -m http.server 3000 --directory web

```

Open **`http://localhost:3000`** in your browser.

---

## How It Works

If brought into production inside Aegle's environment, the stack is designed around four practical pillars:

1. **Serverless HIPAA-Compliant Parsing** — Instead of paying for dedicated GPU clusters that sit idle 95% of the time, messy PDFs and UB-04 forms route through stateless, pay-per-token OCR endpoints under an Enterprise HIPAA BAA and Zero Data Retention (ZDR) to produce page-anchored Markdown.
2. **Zero-Data-Retention Legal Reasoning** — Top-scoring open-weight legal models (like DeepSeek V4.1 Flash and Kimi K3.1 Pro) run on **Fireworks AI** serverless endpoints (`store: false` + HIPAA BAA), delivering frontier legal intelligence at a fraction of proprietary model costs.
3. **Specialized Verification Tools** — The AI never guesses coverage rules or calculates funding tranches in its head. It verifies every code and clause against live, authoritative sources:
* [CMS Medicare Coverage Database (NCD 110.24)](https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=372)
* [openFDA Drug Labels](https://open.fda.gov/)
* [CourtListener ERISA & Stop-Loss Case Law](https://www.courtlistener.com/)
* [eCFR Title 29 Claims Regulations](https://www.ecfr.gov/current/title-29)


4. **Human-in-the-Loop & Zero-PHI Boundary** — AI never autonomously wires money or mutates CRM data. Analysts review every citation, challenge or adjust findings via chat, and sign off on drafts—keeping clinical data locked inside the HIPAA boundary while only de-identified keys and dollar math ever touch HubSpot or Teams.

---

## Rollout Roadmap

* **Phase 1: Self-Hosted LibreChat + Verification Tools** — Deploy an internal, zero-PHI LibreChat workspace wired to Fireworks AI (ZDR + BAA) and our verification tools (`claimcatch_mcp.py` + `CLAIMCATCH_PARTNER_ASSOCIATE_PROMPT.md`). Takes ~4 hours to set up and gives analysts an immediate chat copilot with full chain-of-thought and source citations.
* **Phase 2: Read-Only HubSpot Context** — Connect read-only CRM context from HubSpot into the workspace so analysts can cross-reference partner and policy metadata without granting AI write access to production records.
* **Phase 3: Dedicated Aegle Aura Workbench** — Graduate into the custom workbench UI (`web/`) for drag-and-drop multi-document triage, side-by-side PDF evidence inspection, and one-click human-in-the-loop staging.

```

```
