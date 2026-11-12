"""ClaimCatch MCP server.

Production-shaped FastMCP demo for the Aegle Health Partners (d/b/a Aegle Capital)
Client Partner Associate workflow.  Synthetic claim #9941 / policy MPM-SL-2026-0147.

All tools are read-only with respect to external systems.  The HubSpot/Teams
handoff is staged locally and requires human approval; nothing is ever written to
HubSpot, Teams, or email by this server.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterator

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("claimcatch")

# ---------------------------------------------------------------------------
# Logging (stderr only; server mode must never print to stdout)
# ---------------------------------------------------------------------------

logger = logging.getLogger("claimcatch")
if not logger.handlers:
    _handler = logging.StreamHandler(stream=sys.stderr)
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

POLICY_NUMBER = "MPM-SL-2026-0147"
CARRIER = "Meridian Mutual Stop Loss"
PARTNER_TPA = "Prairie States Administrators"
EMPLOYER = "Midwest Precision Manufacturing LLC"
CLAIMANT_KEY = "MPM-9941-07"
OPEN_ISSUE_ROOT_CAUSE = "Unflagged Renewal Laser + Missing CFO Counter-Sign"

BASE_SPECIFIC_DEDUCTIBLE = Decimal("250000")
BILLED_AMOUNT = Decimal("3050000")
FL48_NON_COVERED = Decimal("350000")
LASERED_DEDUCTIBLE = Decimal("750000")
SIGNATURE_HOLD = Decimal("250000")
REQUESTED_ADVANCE = Decimal("2800000")
APPROVED_TRANCHE_1 = Decimal("1700000")

CITATION_STATUS = (
    "party/court/year from research packet; reporter citation not captured"
)

PRACTICE_NOTE = (
    "No verified precedent exists for a leukemia/CAR-T laser, or for denial based "
    "solely on a missing signature. A signature defect is an operational, curable "
    "hold, not a coverage determination. Experimental exclusion authority is "
    "plan-language dependent and plan-level (Parsons); none is CAR-T-specific."
)

NCD_110_24 = {
    "ncd_id": "110.24",
    "ncd_numeric_id": "374",
    "title": "Chimeric Antigen Receptor (CAR) T-Cell Therapy",
    "url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=110.24",
    "effective_date": "2019-08-07",
    "determination": (
        "Autologous CAR T-cell therapy is covered when furnished consistent with "
        "the FDA-approved label or a CMS-accepted compendium, with the patient "
        "enrolled in a registry when required."
    ),
}

FDA_KYMRIAH = {
    "product": "tisagenlecleucel (Kymriah)",
    "approval_date": "2017-08-30",
    "labeled_population": (
        "B-cell precursor acute lymphoblastic leukemia (B-ALL) in patients up to "
        "25 years of age that is refractory or in second or later relapse"
    ),
}

FDA_PEMBROLIZUMAB = {
    "product": "pembrolizumab (Keytruda)",
    "approval_date": "2014-09-04",
    "labeled_population": (
        "Select advanced solid tumors and lymphomas; no FDA-labeled indication for "
        "B-cell precursor acute lymphoblastic leukemia"
    ),
}

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

MEDICAL_CODE_SEED: list[dict[str, Any]] = [
    {
        "code": "C91.02",
        "system": "ICD-10-CM",
        "description": "Acute lymphoblastic leukemia, in relapse",
        "flags": ["malignancy", "car_t_labeled_indication"],
        "packet_role": "primary diagnosis (UB-04 FL67)",
    },
    {
        "code": "D89.83",
        "system": "ICD-10-CM",
        "description": "Cytokine release syndrome",
        "flags": ["car_t_complication"],
        "packet_role": "secondary diagnosis",
    },
    {
        "code": "D61.810",
        "system": "ICD-10-CM",
        "description": "Antineoplastic chemotherapy induced pancytopenia",
        "flags": ["treatment_complication"],
        "packet_role": "secondary diagnosis",
    },
    {
        "code": "D70.1",
        "system": "ICD-10-CM",
        "description": "Agranulocytosis secondary to cancer chemotherapy",
        "flags": ["treatment_complication"],
        "packet_role": "secondary diagnosis",
    },
    {
        "code": "N17.9",
        "system": "ICD-10-CM",
        "description": "Acute kidney failure, unspecified",
        "flags": ["organ_support"],
        "packet_role": "secondary diagnosis",
    },
    {
        "code": "J18.9",
        "system": "ICD-10-CM",
        "description": "Pneumonia, unspecified organism",
        "flags": ["infection"],
        "packet_role": "secondary diagnosis",
    },
    {
        "code": "Q2042",
        "system": "HCPCS",
        "description": "Tisagenlecleucel, per infusion",
        "flags": ["fda_labeled", "ncd_110.24"],
        "packet_role": "CAR-T product (Kymriah), labelled and payable",
    },
    {
        "code": "J9999",
        "system": "HCPCS",
        "description": "Not otherwise classified, antineoplastic drug",
        "flags": ["unclassified", "experimental_tell"],
        "packet_role": "unclassified drug line - experimental/investigational tell",
    },
    {
        "code": "J3490",
        "system": "HCPCS",
        "description": "Unclassified drugs",
        "flags": ["unclassified", "off_label_risk"],
        "packet_role": "unclassified drug line - off-label risk",
    },
    {
        "code": "J9039",
        "system": "HCPCS",
        "description": "Blinatumomab, 1 mcg",
        "flags": ["fda_labeled"],
        "packet_role": "supporting therapy",
    },
    {
        "code": "J9185",
        "system": "HCPCS",
        "description": "Fludarabine, 50 mg",
        "flags": ["lymphodepletion"],
        "packet_role": "lymphodepletion regimen",
    },
    {
        "code": "J9070",
        "system": "HCPCS",
        "description": "Cyclophosphamide, 100 mg",
        "flags": ["lymphodepletion"],
        "packet_role": "lymphodepletion regimen",
    },
    {
        "code": "0256",
        "system": "UB-04 revenue",
        "description": "Investigational drugs",
        "flags": ["investigational"],
        "packet_role": "experimental/investigational drug charges",
    },
    {
        "code": "0891",
        "system": "UB-04 revenue",
        "description": "Cell therapy",
        "flags": ["car_t"],
        "packet_role": "CAR-T infusion service",
    },
    {
        "code": "0110",
        "system": "UB-04 revenue",
        "description": "Private medical/surgical room",
        "flags": ["private_room_differential"],
        "packet_role": "private-room differential",
    },
    {
        "code": "0999",
        "system": "UB-04 revenue",
        "description": "Patient convenience/luxury items",
        "flags": ["non_covered_luxury"],
        "packet_role": "non-covered convenience/luxury charges",
    },
    {
        "code": "0001",
        "system": "UB-04 revenue",
        "description": "Total charges",
        "flags": ["form_total"],
        "packet_role": "UB-04 form total / cross-foot line",
    },
    {
        "code": "0636",
        "system": "UB-04 revenue",
        "description": "Drugs requiring detailed coding",
        "flags": ["drug_detail"],
        "packet_role": "itemized drug charges",
    },
    {
        "code": "0250",
        "system": "UB-04 revenue",
        "description": "Pharmacy",
        "flags": ["pharmacy"],
        "packet_role": "pharmacy charges",
    },
    {
        "code": "0200",
        "system": "UB-04 revenue",
        "description": "ICU",
        "flags": ["intensive_care"],
        "packet_role": "ICU days",
    },
    {
        "code": "0206",
        "system": "UB-04 revenue",
        "description": "Step-down",
        "flags": ["step_down"],
        "packet_role": "step-down days",
    },
    {
        "code": "0335",
        "system": "UB-04 revenue",
        "description": "Chemotherapy administration",
        "flags": ["chemotherapy_admin"],
        "packet_role": "chemotherapy administration",
    },
]

CASE_LAW_SEED: list[dict[str, Any]] = [
    {
        "case_name": "Trustmark Ins. Co. v. Citizens",
        "court": "D. Conn.",
        "year": 2004,
        "holding": (
            "A laser / separate specific deductible was enforced where a signed "
            "amendment created it; undisclosed expected claims supported the "
            "underwriting challenge and reached the jury."
        ),
        "issue_tags": ["laser", "amendment", "endorsement", "deductible", "underwriting"],
        "relevance": (
            "Closest authority for enforcing a signed laser endorsement and for "
            "treating undisclosed expected claims as an underwriting issue."
        ),
        "confidence": "high",
    },
    {
        "case_name": "Blue Cross of Idaho v. Scentsy",
        "court": "D. Idaho",
        "year": 2026,
        "holding": (
            "Strict compliance with the 12/15 paid-basis and run-out terms; a "
            "payment made after the run-out did not qualify for reimbursement."
        ),
        "issue_tags": [
            "paid_basis",
            "run_out",
            "runout",
            "12/15",
            "contract_basis",
            "late_payment",
        ],
        "relevance": (
            "Authoritative on paid-basis 12/15 mechanics and run-out deadlines; "
            "late payment after run-out forfeits reimbursement."
        ),
        "confidence": "high",
    },
    {
        "case_name": "BCBS NC v. Technibilt",
        "court": "W.D.N.C.",
        "year": 2020,
        "holding": (
            "Paid-only policy plus late TPA payment; motion to dismiss denied, so "
            "the dispute proceeded without a merits holding."
        ),
        "issue_tags": ["paid_basis", "runout", "tpa_payment", "late_payment"],
        "relevance": (
            "Shows a paid-only theory surviving dismissal where the TPA paid late; "
            "no merits ruling, so persuasive rather than binding."
        ),
        "confidence": "medium",
    },
    {
        "case_name": "Parsons",
        "court": "D. Mont.",
        "year": 2011,
        "holding": (
            "Enforceability of an experimental/investigational exclusion depends on "
            "the plan language; no CAR-T-specific holding."
        ),
        "issue_tags": ["experimental", "investigational", "car_t"],
        "relevance": (
            "The only identified experimental-exclusion authority; plan-level, not "
            "therapy-specific, and not CAR-T authority."
        ),
        "confidence": "medium",
    },
]

# ---------------------------------------------------------------------------
# PHI patterns
# ---------------------------------------------------------------------------

PHI_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("icd10", re.compile(r"\b[A-TV-Z]\d{2}(?:\.[0-9A-Z]{1,4})?\b", re.IGNORECASE)),
    ("icd10_compact", re.compile(r"\b[A-TV-Z]\d{3}[0-9A-Z]{0,2}\b", re.IGNORECASE)),
    ("date_iso", re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b")),
    ("date_us", re.compile(r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    (
        "patient_identifier",
        re.compile(r"\b(?:MRN|SSN|DOB|PATIENT|MEMBER\s*ID)\b\s*[:#]?\s*[A-Za-z0-9-]{3,}\b", re.IGNORECASE),
    ),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone", re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")),
]

PATTERNS_CHECKED = [name for name, _ in PHI_PATTERNS]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    tool TEXT NOT NULL,
    args_json TEXT NOT NULL,
    result_summary TEXT NOT NULL,
    ok INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_log_ts ON audit_log(ts);

CREATE TABLE IF NOT EXISTS api_cache (
    cache_key TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    ttl_seconds INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS staged_payloads (
    staged_payload_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    claim_id TEXT NOT NULL,
    partner_tpa TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS case_law (
    case_name TEXT PRIMARY KEY,
    court TEXT NOT NULL,
    year INTEGER NOT NULL,
    holding TEXT NOT NULL,
    issue_tags TEXT NOT NULL,
    relevance TEXT NOT NULL,
    confidence TEXT NOT NULL,
    citation_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medical_codes (
    code TEXT PRIMARY KEY,
    system TEXT NOT NULL,
    description TEXT NOT NULL,
    flags TEXT NOT NULL,
    packet_role TEXT NOT NULL
);
"""

_WRITE_LOCK = threading.RLock()
_INIT_LOCK = threading.Lock()
_INITIALIZED: set[str] = set()


def _db_path() -> str:
    """Resolve the SQLite path from the environment on every call."""
    return os.environ.get("CLAIMCATCH_DB_PATH", os.path.join(".claimcatch", "claimcatch.sqlite3"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _new_audit_id() -> str:
    return f"aud_{uuid.uuid4().hex}"


def _offline() -> bool:
    value = os.environ.get("CLAIMCATCH_OFFLINE", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _ensure_db() -> str:
    """Create the parent directory, schema, and seed rows once per path."""
    path = os.path.abspath(_db_path())
    with _INIT_LOCK:
        if path in _INITIALIZED:
            return path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, timeout=10)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=10000")
            conn.executescript(SCHEMA)
            _seed(conn)
            conn.commit()
        finally:
            conn.close()
        _INITIALIZED.add(path)
    return path


def _seed(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO medical_codes (code, system, description, flags, packet_role) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (
                row["code"],
                row["system"],
                row["description"],
                json.dumps(row["flags"]),
                row["packet_role"],
            )
            for row in MEDICAL_CODE_SEED
        ],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO case_law "
        "(case_name, court, year, holding, issue_tags, relevance, confidence, citation_status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["case_name"],
                row["court"],
                row["year"],
                row["holding"],
                json.dumps(row["issue_tags"]),
                row["relevance"],
                row["confidence"],
                CITATION_STATUS,
            )
            for row in CASE_LAW_SEED
        ],
    )


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    path = _ensure_db()
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def _safe_json(value: Any, limit: int = 4000) -> str:
    try:
        text = json.dumps(value, default=str, ensure_ascii=False, sort_keys=True)
    except Exception:  # pragma: no cover - defensive
        text = json.dumps({"unserializable": type(value).__name__})
    return text[:limit]


def _write_audit(audit_id: str, tool: str, args: Any, result: dict[str, Any]) -> None:
    summary = {
        "ok": bool(result.get("ok")),
        "keys": sorted(result.keys())[:30],
    }
    if "error" in result:
        summary["error"] = str(result["error"])[:300]
    if "coverage_status" in result:
        summary["coverage_status"] = result["coverage_status"]
    if "matched_precedents" in result:
        summary["matched_cases"] = [
            item.get("case") for item in result.get("matched_precedents", [])
        ][:5]
    if "staged_payload_id" in result:
        summary["staged_payload_id"] = result["staged_payload_id"]
    if "approved_tranche_1" in result:
        summary["approved_tranche_1"] = result["approved_tranche_1"]

    try:
        with _WRITE_LOCK, _connect() as conn:
            conn.execute(
                "INSERT INTO audit_log (audit_id, ts, tool, args_json, result_summary, ok) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    audit_id,
                    _now_iso(),
                    tool,
                    _safe_json(args),
                    _safe_json(summary, limit=2000),
                    1 if result.get("ok") else 0,
                ),
            )
            conn.commit()
    except Exception as exc:  # pragma: no cover - audit must never crash a tool
        logger.error("audit write failed for %s: %s", audit_id, exc)


def _finalize(
    audit_id: str,
    tool: str,
    args: Any,
    result: dict[str, Any],
    *,
    internal_error: BaseException | None = None,
) -> dict[str, Any]:
    if internal_error is not None:
        logger.error("%s failed: %s", tool, internal_error)
    if "ok" not in result:
        result["ok"] = False
    result["audit_id"] = audit_id
    _write_audit(audit_id, tool, args, result)
    return result


def _error(message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": False, "error": message}
    payload.update(extra)
    return payload


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _normalize(code: str) -> str:
    return re.sub(r"\s+", "", str(code)).upper()


def _canonical_icd(code: str) -> str:
    normalized = _normalize(code)
    if "." in normalized or len(normalized) <= 3:
        return normalized
    return f"{normalized[:3]}.{normalized[3:]}"


def _detect_system(code: str) -> str | None:
    if re.fullmatch(r"\d{4}", code):
        return "UB-04 revenue"
    if re.fullmatch(r"[A-Z]\d{4}", code):
        return "HCPCS"
    if re.fullmatch(r"[A-Z]\d{2}\.[0-9A-Z]{1,4}", code):
        return "ICD-10-CM"
    if re.fullmatch(r"[A-Z]\d{2}[0-9A-Z]{1,4}", code) and len(code) > 5:
        return "ICD-10-CM"
    return None


def _is_icd10(code: str) -> bool:
    return bool(
        re.fullmatch(r"[A-TV-Z]\d{2}(?:\.[0-9A-Z]{1,4}|[0-9A-Z]{1,4})", code)
    )


def _medical_index() -> dict[str, dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT code, system, description, flags, packet_role FROM medical_codes"
        ).fetchall()
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        index[row["code"].replace(".", "").upper()] = {
            "code": row["code"],
            "system": row["system"],
            "description": row["description"],
            "flags": json.loads(row["flags"]),
            "packet_role": row["packet_role"],
        }
    return index


def _medical_lookup(code: str) -> dict[str, Any] | None:
    return _medical_index().get(code.replace(".", "").upper())


def _fmt_money(value: Decimal | float | int) -> str:
    amount = Decimal(str(value))
    if amount == amount.to_integral_value():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"


def _money(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError(f"{field} must be a finite number")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a finite number") from None
    if not amount.is_finite():
        raise ValueError(f"{field} must be a finite number")
    if amount < 0:
        raise ValueError(f"{field} must be non-negative")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _sanitize_text(value: Any, field: str, max_len: int) -> tuple[str, list[str]]:
    """Flatten control characters, scrub PHI patterns, and bound the length."""
    if not isinstance(value, str):
        value = "" if value is None else str(value)
    clean = re.sub(r"[\r\n\t]+", " ", value)
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", clean)
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    stripped: list[str] = []
    for name, pattern in PHI_PATTERNS:
        if pattern.search(clean):
            clean = pattern.sub("[REDACTED]", clean)
            stripped.append(f"{field}:{name}")
    clean = re.sub(r"\s{2,}", " ", clean).strip()[:max_len]
    return clean, stripped


def _scan_texts(texts: dict[str, str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field, text in texts.items():
        for name, pattern in PHI_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    {"field": field, "pattern": name, "match": match.group(0)}
                )
    return findings


def _scan_value(value: Any, path: str, findings: list[dict[str, str]]) -> None:
    if isinstance(value, str):
        for name, pattern in PHI_PATTERNS:
            for match in pattern.finditer(value):
                findings.append(
                    {"field": path, "pattern": name, "match": match.group(0)}
                )
    elif isinstance(value, dict):
        for key, item in value.items():
            _scan_value(item, f"{path}.{key}" if path else str(key), findings)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _scan_value(item, f"{path}[{index}]", findings)


def _scan_payload(payload: Any) -> list[dict[str, str]]:
    """Recursively scan every string in a nested payload for PHI patterns."""
    findings: list[dict[str, str]] = []
    _scan_value(payload, "", findings)
    return findings


def _idempotency_key(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"idem_{digest[:32]}"


# ---------------------------------------------------------------------------
# Tool 1 - medical code lookup
# ---------------------------------------------------------------------------


@mcp.tool()
def lookup_medical_code(codes: list[str]) -> dict:
    """Validate ICD-10-CM, HCPCS Level II, and UB-04 revenue codes against the seeded code set.

    Returns per-code validity, description, system, flags, and packet role, plus
    unknown_codes / requested_count / recognized_count. Unknown codes do not fail
    the whole call; malformed input does.
    """
    audit_id = _new_audit_id()
    args = {"codes": codes}
    try:
        if not isinstance(codes, list) or not codes:
            return _finalize(
                audit_id,
                "lookup_medical_code",
                args,
                _error("codes must be a non-empty list of strings"),
            )
        if any(not isinstance(code, str) for code in codes):
            return _finalize(
                audit_id,
                "lookup_medical_code",
                args,
                _error("every entry in codes must be a string"),
            )

        index = _medical_index()
        results: list[dict[str, Any]] = []
        unknown: list[str] = []
        recognized = 0

        for raw in codes:
            normalized = _normalize(raw)
            system = _detect_system(normalized)
            if system is None:
                results.append(
                    {
                        "input": raw,
                        "code": normalized,
                        "valid": False,
                        "system": None,
                        "description": None,
                        "flags": [],
                        "packet_role": None,
                        "reason": "unrecognized_format",
                    }
                )
                unknown.append(raw)
                continue

            row = index.get(normalized.replace(".", ""))
            if row is None:
                results.append(
                    {
                        "input": raw,
                        "code": normalized,
                        "valid": False,
                        "system": system,
                        "description": None,
                        "flags": [],
                        "packet_role": None,
                        "reason": "not_in_seeded_code_set",
                    }
                )
                unknown.append(raw)
                continue

            recognized += 1
            results.append(
                {
                    "input": raw,
                    "code": row["code"],
                    "valid": True,
                    "system": row["system"],
                    "description": row["description"],
                    "flags": row["flags"],
                    "packet_role": row["packet_role"],
                }
            )

        return _finalize(
            audit_id,
            "lookup_medical_code",
            args,
            {
                "ok": True,
                "requested_count": len(codes),
                "recognized_count": recognized,
                "unknown_codes": unknown,
                "results": results,
                "codes": results,
            },
        )
    except Exception as exc:
        return _finalize(
            audit_id,
            "lookup_medical_code",
            args,
            _error(f"internal_error: {type(exc).__name__}"),
            internal_error=exc,
        )


# ---------------------------------------------------------------------------
# Tool 2 - CMS coverage / FDA label check
# ---------------------------------------------------------------------------


def _ncd_record() -> dict[str, Any]:
    return {
        "ncd_id": NCD_110_24["ncd_id"],
        "title": NCD_110_24["title"],
        "url": NCD_110_24["url"],
        "effective_date": NCD_110_24["effective_date"],
        "determination": NCD_110_24["determination"],
    }


def _determination(hcpcs: str, diagnosis: str) -> dict[str, Any]:
    row = _medical_lookup(hcpcs)
    if row is None:
        return {
            "ok": False,
            "coverage_status": "unknown_code",
            "indication_match": False,
            "determination": (
                f"{hcpcs} is not present in the seeded code set; coverage cannot be "
                "determined from local ground truth."
            ),
            "reasons": [
                f"{hcpcs} is not in the seeded medical code table.",
                "No live or local NCD determination is asserted for an unknown code.",
            ],
            "fda": None,
            "diagnosis_recognized": _medical_lookup(diagnosis) is not None,
        }

    if hcpcs == "0256":
        return {
            "ok": True,
            "coverage_status": "non_covered",
            "indication_match": False,
            "determination": (
                "Revenue code 0256 designates investigational drugs; the NCD does "
                "not cover investigational products outside an approved trial."
            ),
            "reasons": [
                "0256 = investigational drugs.",
                "Investigational billing is excluded as experimental/investigational.",
                "A 0256 line is a packet red flag even when a CAR-T product code appears nearby.",
            ],
            "fda": None,
            "diagnosis_recognized": _medical_lookup(diagnosis) is not None,
            "packet_role": row["packet_role"],
        }

    if hcpcs == "J9999":
        return {
            "ok": True,
            "coverage_status": "non_covered",
            "indication_match": False,
            "determination": (
                "J9999 is an unclassified antineoplastic code; an unclassified line "
                "is treated as experimental/investigational and is not covered."
            ),
            "reasons": [
                "J9999 = not otherwise classified, antineoplastic drug.",
                "Unclassified coding is an experimental/investigational tell.",
                "NCD 110.24 covers labeled or compendium-supported CAR-T products, not unclassified lines.",
            ],
            "fda": None,
            "diagnosis_recognized": _medical_lookup(diagnosis) is not None,
            "packet_role": row["packet_role"],
        }

    if hcpcs == "J3490":
        off_label = diagnosis == "C91.02"
        return {
            "ok": True,
            "coverage_status": "non_covered",
            "indication_match": False,
            "determination": (
                "J3490 is an unclassified drug code. With C91.02 this is off-label "
                "pembrolizumab, which is not an FDA-labeled B-ALL indication and is "
                "non-covered."
                if off_label
                else "J3490 is an unclassified drug code with off-label risk and is "
                "non-covered absent a specific covered indication."
            ),
            "reasons": [
                "J3490 = unclassified drugs; no product-specific NDC or label.",
                "Off-label use without compendium support is excluded.",
                "NCD 110.24 does not extend to unclassified off-label drug lines.",
            ],
            "fda": {
                **FDA_PEMBROLIZUMAB,
                "indication_match": False,
                "note": "Off-label pembrolizumab use; no B-ALL labeling.",
            },
            "diagnosis_recognized": _medical_lookup(diagnosis) is not None,
            "packet_role": row["packet_role"],
        }

    if hcpcs == "Q2042":
        labeled = {"C91.02", "C91.00", "C91.01"}
        if diagnosis in labeled:
            return {
                "ok": True,
                "coverage_status": "covered",
                "indication_match": True,
                "determination": (
                    "Q2042 (tisagenlecleucel) is covered under NCD 110.24 for the "
                    "FDA-labeled B-ALL population; C91.02 matches the label."
                ),
                "reasons": [
                    "Q2042 = tisagenlecleucel, per infusion (Kymriah).",
                    "FDA approval 2017-08-30 for B-ALL up to age 25, refractory or >=2nd relapse.",
                    "Diagnosis C91.02 (B-ALL, in relapse) matches the labeled population.",
                    "NCD 110.24 covers autologous CAR T-cell therapy consistent with the label.",
                ],
                "fda": {**FDA_KYMRIAH, "indication_match": True},
                "diagnosis_recognized": _medical_lookup(diagnosis) is not None,
                "packet_role": row["packet_role"],
            }
        return {
            "ok": True,
            "coverage_status": "not_covered_outside_label",
            "indication_match": False,
            "determination": (
                "Q2042 is FDA-labeled for B-ALL up to age 25; the supplied diagnosis "
                "falls outside that labeled population and is not covered on this record."
            ),
            "reasons": [
                "Q2042 is a labeled CAR-T product, but the diagnosis is outside the label.",
                f"{diagnosis} is not in the labeled B-ALL population.",
                "NCD 110.24 covers labeled or compendium-supported use only.",
            ],
            "fda": {**FDA_KYMRIAH, "indication_match": False},
            "diagnosis_recognized": _medical_lookup(diagnosis) is not None,
            "packet_role": row["packet_role"],
        }

    return {
        "ok": True,
        "coverage_status": "no_ncd_found",
        "indication_match": False,
        "determination": (
            "No code-specific NCD determination is seeded for this code; the CAR-T "
            "NCD does not resolve it."
        ),
        "reasons": [
            f"{hcpcs} is recognized ({row['description']}).",
            "No seeded NCD 110.24 rule maps this code to a coverage outcome.",
        ],
        "fda": None,
        "diagnosis_recognized": _medical_lookup(diagnosis) is not None,
        "packet_role": row["packet_role"],
    }


def _cache_get(key: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload_json, fetched_at, ttl_seconds FROM api_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
    if row is None:
        return None
    try:
        fetched_at = datetime.fromisoformat(row["fetched_at"].replace("Z", "+00:00"))
    except ValueError:
        return None
    if datetime.now(timezone.utc) - fetched_at > timedelta(seconds=row["ttl_seconds"]):
        return None
    try:
        return json.loads(row["payload_json"])
    except json.JSONDecodeError:
        return None


def _cache_put(key: str, payload: dict[str, Any], ttl_seconds: int = 86400) -> None:
    try:
        with _WRITE_LOCK, _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO api_cache (cache_key, payload_json, fetched_at, ttl_seconds) "
                "VALUES (?, ?, ?, ?)",
                (key, json.dumps(payload), _now_iso(), ttl_seconds),
            )
            conn.commit()
    except Exception as exc:  # pragma: no cover - cache is best effort
        logger.warning("cache write failed: %s", exc)


def _live_ncd_lookup(url: str) -> dict[str, Any]:
    timeout_raw = os.environ.get("CLAIMCATCH_HTTP_TIMEOUT", "4")
    try:
        timeout = float(timeout_raw)
    except (TypeError, ValueError):
        timeout = 4.0
    try:
        import httpx

        with httpx.Client(timeout=timeout) as client:
            response = client.get(
                url,
                params={"ncdid": NCD_110_24["ncd_id"]},
                headers={"Accept": "application/json"},
            )
        status = response.status_code
        if status >= 400:
            return {
                "ok": False,
                "http_status": status,
                "error": f"CMS API returned HTTP {status}",
            }
        data = response.json()
        blob = json.dumps(data)[:200000]
        if (
            NCD_110_24["ncd_id"] not in blob
            and f'"{NCD_110_24["ncd_numeric_id"]}"' not in blob
        ):
            return {
                "ok": False,
                "http_status": status,
                "error": "CMS response did not contain NCD 110.24",
            }
        return {"ok": True, "http_status": status, "error": None, "record": _ncd_record()}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": None,
            "error": f"{type(exc).__name__}: {str(exc)[:240]}",
        }


@mcp.tool()
def check_cms_coverage_and_fda(hcpcs_code: str, diagnosis_icd10: str) -> dict:
    """Check CMS NCD 110.24 coverage and the FDA label for a HCPCS/revenue code plus ICD-10-CM diagnosis.

    Attempts the live CMS Coverage API (short timeout) unless CLAIMCATCH_OFFLINE=1,
    caches successful responses for 24 hours, and otherwise falls back to a local
    seeded NCD record.  The response states exactly which source was used; it never
    claims live verification when the API was not reached.
    """
    audit_id = _new_audit_id()
    args = {"hcpcs_code": hcpcs_code, "diagnosis_icd10": diagnosis_icd10}
    try:
        if not isinstance(hcpcs_code, str) or not isinstance(diagnosis_icd10, str):
            return _finalize(
                audit_id,
                "check_cms_coverage_and_fda",
                args,
                _error("hcpcs_code and diagnosis_icd10 must both be strings"),
            )
        code = _normalize(hcpcs_code)
        diagnosis = _canonical_icd(diagnosis_icd10)
        if not _is_icd10(_normalize(diagnosis_icd10)):
            return _finalize(
                audit_id,
                "check_cms_coverage_and_fda",
                args,
                _error(
                    "diagnosis_icd10 is not a well-formed ICD-10-CM code",
                    query={"hcpcs_code": code, "diagnosis_icd10": diagnosis},
                ),
            )
        if _detect_system(code) is None:
            return _finalize(
                audit_id,
                "check_cms_coverage_and_fda",
                args,
                _error(
                    "hcpcs_code is not a well-formed HCPCS Level II or UB-04 revenue code",
                    query={"hcpcs_code": code, "diagnosis_icd10": diagnosis},
                ),
            )

        determination = _determination(code, diagnosis)
        ncd = _ncd_record()
        ncd["determination"] = determination["determination"]

        base_url = os.environ.get(
            "CLAIMCATCH_CMS_API_BASE", "https://api.coverage.cms.gov/v1"
        ).rstrip("/")
        live_url = f"{base_url}/reports/national-coverage-ncd/"
        cache_key = f"cms_ncd:{NCD_110_24['ncd_id']}:{code}:{diagnosis}"

        live_attempted = False
        live_error: str | None = None
        http_status: int | None = None
        cache_hit = False
        source = "local_ncd_seed"
        verified_at: str | None = None

        if not determination["ok"]:
            live_error = None
        elif _offline():
            live_error = "offline_mode (CLAIMCATCH_OFFLINE=1); no live CMS call attempted"
        else:
            cached = _cache_get(cache_key)
            if cached is not None:
                cache_hit = True
                source = "cms_api_cache"
                http_status = cached.get("http_status")
                verified_at = cached.get("fetched_at")
            else:
                live_attempted = True
                result = _live_ncd_lookup(live_url)
                http_status = result.get("http_status")
                if result["ok"]:
                    source = "cms_api_live"
                    verified_at = _now_iso()
                    _cache_put(
                        cache_key,
                        {
                            "ncd": _ncd_record(),
                            "http_status": http_status,
                            "fetched_at": verified_at,
                        },
                    )
                else:
                    live_error = result.get("error") or "live CMS lookup failed"

        response: dict[str, Any] = {
            "ok": determination["ok"],
            "query": {"hcpcs_code": code, "diagnosis_icd10": diagnosis},
            "coverage_status": determination["coverage_status"],
            "indication_match": determination["indication_match"],
            "determination": ncd["determination"],
            "reasons": determination["reasons"],
            "ncd": ncd,
            "fda": determination.get("fda"),
            "diagnosis_recognized": determination.get("diagnosis_recognized"),
            "source": source,
            "determination_source": "local_ncd_seed",
            "live_api_scope": (
                "NCD metadata/ID presence only; coverage logic is seeded locally"
                if source in {"cms_api_live", "cms_api_cache"}
                else None
            ),
            "live_api_attempted": live_attempted,
            "live_api_error": live_error,
            "live_api_url": live_url,
            "live_api_http_status": http_status,
            "live_api_verified_at": verified_at,
            "cache_hit": cache_hit,
            "checked_at": _now_iso(),
        }
        if "packet_role" in determination:
            response["packet_role"] = determination["packet_role"]
        if not determination["ok"]:
            response["error"] = determination["reasons"][0]

        return _finalize(audit_id, "check_cms_coverage_and_fda", args, response)
    except Exception as exc:
        return _finalize(
            audit_id,
            "check_cms_coverage_and_fda",
            args,
            _error(f"internal_error: {type(exc).__name__}"),
            internal_error=exc,
        )


# ---------------------------------------------------------------------------
# Tool 3 - stop-loss case law
# ---------------------------------------------------------------------------


def _normalized_terms(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


@mcp.tool()
def lookup_stoploss_case_law(issue: str) -> dict:
    """Search seeded stop-loss precedents by issue tags (case-insensitive keyword match).

    Returns matched precedents with holding, citation status, and confidence, plus a
    practice note that distinguishes plan-level authority from CAR-T-specific
    authority.  No match returns an empty list with suggested query terms.
    """
    audit_id = _new_audit_id()
    args = {"issue": issue}
    try:
        if not isinstance(issue, str) or not issue.strip():
            return _finalize(
                audit_id,
                "lookup_stoploss_case_law",
                args,
                _error("issue must be a non-empty string"),
            )

        issue_norm = _normalized_terms(issue)
        with _connect() as conn:
            rows = conn.execute(
                "SELECT case_name, court, year, holding, issue_tags, relevance, "
                "confidence, citation_status FROM case_law"
            ).fetchall()

        matches: list[dict[str, Any]] = []
        for row in rows:
            tags = json.loads(row["issue_tags"])
            matched_tags = [
                tag
                for tag in tags
                if _normalized_terms(tag)
                and _normalized_terms(tag) in issue_norm
            ]
            if matched_tags:
                matches.append(
                    {
                        "case": row["case_name"],
                        "court": row["court"],
                        "year": row["year"],
                        "holding": row["holding"],
                        "relevance": (
                            f"{row['relevance']} Matched issue tags: "
                            f"{', '.join(matched_tags)}."
                        ),
                        "citation_status": CITATION_STATUS,
                        "confidence": row["confidence"],
                        "matched_tags": matched_tags,
                        "issue_tags": tags,
                    }
                )

        matches.sort(key=lambda item: (len(item["matched_tags"]), item["year"]), reverse=True)

        response: dict[str, Any] = {
            "ok": True,
            "issue": issue,
            "match_count": len(matches),
            "matched_precedents": matches,
            "practice_note": PRACTICE_NOTE,
            "coverage_gap": (
                "No seeded precedent decides a leukemia/CAR-T laser or a denial "
                "based solely on a missing signature."
            ),
        }
        if not matches:
            response["suggested_query_terms"] = [
                "laser",
                "specific deductible",
                "endorsement",
                "paid basis",
                "12/15",
                "run-out",
                "experimental",
                "CAR-T",
            ]
        return _finalize(audit_id, "lookup_stoploss_case_law", args, response)
    except Exception as exc:
        return _finalize(
            audit_id,
            "lookup_stoploss_case_law",
            args,
            _error(f"internal_error: {type(exc).__name__}"),
            internal_error=exc,
        )


# ---------------------------------------------------------------------------
# Tool 4 - funding tranche reconciliation
# ---------------------------------------------------------------------------


@mcp.tool()
def reconcile_funding_tranche(
    billed: float,
    non_covered_fl48: float,
    lasered_deductible: float,
    signature_hold: float,
    requested_advance: float,
) -> dict:
    """Reconcile a stop-loss advance request into approved Tranche 1 and the trap gap.

    Uses Decimal money math rounded to cents.  Returns the approved tranche, total
    gap, laser gap, trap breakdown, cross-foot checks, and a narrative.  Negative or
    non-finite inputs are rejected; a laser below the base deductible is recorded as
    a check failure but is not a hard error.
    """
    audit_id = _new_audit_id()
    args = {
        "billed": billed,
        "non_covered_fl48": non_covered_fl48,
        "lasered_deductible": lasered_deductible,
        "signature_hold": signature_hold,
        "requested_advance": requested_advance,
    }
    try:
        errors: list[str] = []
        values: dict[str, Decimal] = {}
        for field, raw in args.items():
            try:
                values[field] = _money(raw, field)
            except ValueError as exc:
                errors.append(str(exc))
        if errors:
            return _finalize(
                audit_id,
                "reconcile_funding_tranche",
                args,
                _error("invalid monetary input", validation_errors=errors),
            )

        billed_d = values["billed"]
        fl48_d = values["non_covered_fl48"]
        laser_d = values["lasered_deductible"]
        hold_d = values["signature_hold"]
        requested_d = values["requested_advance"]

        eligible_billed = billed_d - fl48_d
        reimbursable_before_hold = eligible_billed - laser_d
        approved = reimbursable_before_hold - hold_d
        total_gap = requested_d - approved
        laser_gap = max(laser_d - BASE_SPECIFIC_DEDUCTIBLE, Decimal("0.00"))
        trap_total = laser_gap + fl48_d + hold_d
        unrecovered = max(total_gap, Decimal("0.00"))

        checks = {
            "equation_balances": (
                reimbursable_before_hold - hold_d == approved
                and requested_d - approved == total_gap
            ),
            "gap_equals_traps": total_gap == trap_total,
            "approved_not_above_eligible": approved <= eligible_billed,
            "all_inputs_non_negative": True,
            "lasered_deductible_at_or_above_base": laser_d >= BASE_SPECIFIC_DEDUCTIBLE,
        }
        deductible_check = {
            "base_specific_deductible": float(BASE_SPECIFIC_DEDUCTIBLE),
            "lasered_deductible": float(laser_d),
            "meets_base": laser_d >= BASE_SPECIFIC_DEDUCTIBLE,
            "delta": float(laser_d - BASE_SPECIFIC_DEDUCTIBLE),
            "note": (
                "Laser exceeds the base specific deductible."
                if laser_d >= BASE_SPECIFIC_DEDUCTIBLE
                else "Laser is below the base specific deductible; recorded, not hard-failed."
            ),
        }

        narrative = [
            f"Billed {_fmt_money(billed_d)} less FL48 non-covered "
            f"{_fmt_money(fl48_d)} = eligible billed {_fmt_money(eligible_billed)}.",
            f"Eligible {_fmt_money(eligible_billed)} less lasered deductible "
            f"{_fmt_money(laser_d)} = reimbursable before hold "
            f"{_fmt_money(reimbursable_before_hold)}.",
            f"Reimbursable {_fmt_money(reimbursable_before_hold)} less signature hold "
            f"{_fmt_money(hold_d)} = approved Tranche 1 {_fmt_money(approved)}.",
            f"Requested advance {_fmt_money(requested_d)} less approved "
            f"{_fmt_money(approved)} = total gap {_fmt_money(total_gap)}.",
            f"Cross-foot: laser gap {_fmt_money(laser_gap)} + FL48 "
            f"{_fmt_money(fl48_d)} + signature hold {_fmt_money(hold_d)} = "
            f"{_fmt_money(trap_total)}.",
        ]
        assertions = [
            {
                "assertion": "Approved Tranche 1 equals eligible billed less laser deductible and signature hold",
                "passed": checks["equation_balances"],
            },
            {
                "assertion": "Total gap equals the sum of the three traps",
                "passed": checks["gap_equals_traps"],
                "detail": (
                    f"{_fmt_money(laser_gap)} + {_fmt_money(fl48_d)} + "
                    f"{_fmt_money(hold_d)} = {_fmt_money(trap_total)}"
                ),
            },
            {
                "assertion": "Approved Tranche 1 does not exceed eligible billed",
                "passed": checks["approved_not_above_eligible"],
            },
        ]

        response: dict[str, Any] = {
            "ok": True,
            "billed": float(billed_d),
            "non_covered_fl48": float(fl48_d),
            "eligible_billed": float(eligible_billed),
            "lasered_deductible": float(laser_d),
            "reimbursable_before_hold": float(reimbursable_before_hold),
            "signature_hold": float(hold_d),
            "approved_tranche_1": float(approved),
            "requested_advance": float(requested_d),
            "total_gap": float(total_gap),
            "laser_gap": float(laser_gap),
            "trap_breakdown": {
                "laser_gap": float(laser_gap),
                "non_covered_fl48": float(fl48_d),
                "signature_hold": float(hold_d),
                "total": float(trap_total),
            },
            "unrecovered_receivable_loss_prevented": float(unrecovered),
            "tranche_2_hold_amount": float(hold_d),
            "base_specific_deductible": float(BASE_SPECIFIC_DEDUCTIBLE),
            "checks": checks,
            "deductible_check": deductible_check,
            "assertions": assertions,
            "narrative": narrative,
            "formatted": {
                "billed": _fmt_money(billed_d),
                "eligible_billed": _fmt_money(eligible_billed),
                "reimbursable_before_hold": _fmt_money(reimbursable_before_hold),
                "approved_tranche_1": _fmt_money(approved),
                "requested_advance": _fmt_money(requested_d),
                "total_gap": _fmt_money(total_gap),
                "laser_gap": _fmt_money(laser_gap),
            },
        }
        return _finalize(audit_id, "reconcile_funding_tranche", args, response)
    except Exception as exc:
        return _finalize(
            audit_id,
            "reconcile_funding_tranche",
            args,
            _error(f"internal_error: {type(exc).__name__}"),
            internal_error=exc,
        )


# ---------------------------------------------------------------------------
# Tool 5 - zero-PHI HubSpot / Teams staging handoff
# ---------------------------------------------------------------------------


@mcp.tool()
def stage_zero_phi_hubspot_and_teams_handoff(
    claim_id: str,
    partner_tpa: str,
    owner_name: str = "Patrick Feit",
) -> dict:
    """Stage a zero-PHI HubSpot/Teams handoff envelope for human approval.

    Enforces the Aegle Protected-Data Rule: only an allowlisted, de-identified
    payload is built.  No diagnosis, patient identity, DOB, SSN, MRN, service dates,
    address, phone, email, or clinical free text can enter the payload.  The result
    is a dry, read-only PENDING_APPROVAL envelope persisted locally; no HubSpot,
    Teams, or email network writes occur.
    """
    audit_id = _new_audit_id()
    args = {"claim_id": claim_id, "partner_tpa": partner_tpa, "owner_name": owner_name}
    try:
        if not isinstance(claim_id, str) or not isinstance(partner_tpa, str) or not isinstance(owner_name, str):
            return _finalize(
                audit_id,
                "stage_zero_phi_hubspot_and_teams_handoff",
                args,
                _error("claim_id, partner_tpa, and owner_name must be strings"),
            )

        fields_stripped: list[str] = []
        clean_claim, claim_stripped = _sanitize_text(claim_id, "claim_id", 64)
        fields_stripped.extend(claim_stripped)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", clean_claim):
            return _finalize(
                audit_id,
                "stage_zero_phi_hubspot_and_teams_handoff",
                args,
                _error(
                    "claim_id must match [A-Za-z0-9_-]{1,64} after PHI sanitation",
                    fields_stripped=fields_stripped,
                    phi_scan={
                        "phi_detected": bool(fields_stripped),
                        "phi_field_count": len(fields_stripped),
                        "fields_stripped": fields_stripped,
                        "patterns_checked": PATTERNS_CHECKED,
                        "result": "BLOCKED",
                    },
                ),
            )

        clean_tpa, tpa_stripped = _sanitize_text(partner_tpa, "partner_tpa", 120)
        clean_owner, owner_stripped = _sanitize_text(owner_name, "owner_name", 80)
        fields_stripped.extend(tpa_stripped)
        fields_stripped.extend(owner_stripped)
        if not clean_tpa:
            return _finalize(
                audit_id,
                "stage_zero_phi_hubspot_and_teams_handoff",
                args,
                _error("partner_tpa is empty after sanitation", fields_stripped=fields_stripped),
            )
        if not clean_owner:
            clean_owner = "Patrick Feit"

        payload = {
            "claim_id": clean_claim,
            "claimant_key": CLAIMANT_KEY,
            "partner_tpa": clean_tpa,
            "owner_name": clean_owner,
            "policy_number": POLICY_NUMBER,
            "carrier": CARRIER,
            "billed_amount": float(BILLED_AMOUNT),
            "fl48_non_covered_amount": float(FL48_NON_COVERED),
            "lasered_deductible": float(LASERED_DEDUCTIBLE),
            "approved_tranche_1": float(APPROVED_TRANCHE_1),
            "tranche_2_hold_amount": float(SIGNATURE_HOLD),
            "requested_advance": float(REQUESTED_ADVANCE),
            "hs_pipeline_stage": "adjudication_hold_laser_flagged",
            "laser_flag": "flagged",
            "missing_signature_employer": True,
            "missing_signature_tpa": False,
            "missing_signature_carrier": True,
            "open_issue_root_cause": OPEN_ISSUE_ROOT_CAUSE,
            "next_action": (
                "Obtain the Employer CFO counter-signature and carrier countersignature, "
                "then release the $250,000 Tranche 2 hold after verification."
            ),
        }

        partner_health = {
            "partner_tpa": clean_tpa,
            "funding_turnaround_hours": 24,
            "open_issue_root_cause": OPEN_ISSUE_ROOT_CAUSE,
            "mbr_status": "AT_RISK",
        }

        payload_findings = _scan_payload(
            {
                "payload": payload,
                "partner_health": partner_health,
            }
        )
        if payload_findings:
            return _finalize(
                audit_id,
                "stage_zero_phi_hubspot_and_teams_handoff",
                args,
                _error(
                    "payload failed the zero-PHI scan; staging blocked",
                    payload_findings=payload_findings,
                    phi_scan={
                        "phi_detected": True,
                        "phi_field_count": len(payload_findings),
                        "fields_stripped": fields_stripped,
                        "input_redactions": list(fields_stripped),
                        "redaction_count": len(fields_stripped),
                        "patterns_checked": PATTERNS_CHECKED,
                        "result": "BLOCKED",
                    },
                ),
            )

        staged_id = f"stg_{uuid.uuid4().hex[:16]}"
        idem_key = _idempotency_key(payload)
        created_at = _now_iso()

        with _WRITE_LOCK, _connect() as conn:
            conn.execute(
                "INSERT INTO staged_payloads "
                "(staged_payload_id, created_at, claim_id, partner_tpa, payload_json, status, idempotency_key) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    staged_id,
                    created_at,
                    clean_claim,
                    clean_tpa,
                    json.dumps(payload, sort_keys=True),
                    "PENDING_APPROVAL",
                    idem_key,
                ),
            )
            conn.commit()

        phi_scan = {
            "phi_detected": False,
            "phi_field_count": 0,
            "fields_stripped": fields_stripped,
            "input_redactions": list(fields_stripped),
            "redaction_count": len(fields_stripped),
            "patterns_checked": PATTERNS_CHECKED,
            "payload_findings": [],
            "result": "PASS",
        }

        response = {
            "ok": True,
            "dry": True,
            "read_only": True,
            "status": "PENDING_APPROVAL",
            "target": "/crm/v3/objects/catastrophic_claim",
            "staged_payload_id": staged_id,
            "idempotency_key": idem_key,
            "created_at": created_at,
            "approval": {
                "required": True,
                "role": "VP, Client Partnerships",
                "owner_name": clean_owner,
                "action": "single_click",
            },
            "payload": payload,
            "partner_health": partner_health,
            "phi_scan": phi_scan,
            "persistence": {
                "table": "staged_payloads",
                "staged_payload_id": staged_id,
                "status": "PENDING_APPROVAL",
            },
            "network_writes": 0,
        }
        return _finalize(
            audit_id, "stage_zero_phi_hubspot_and_teams_handoff", args, response
        )
    except Exception as exc:
        return _finalize(
            audit_id,
            "stage_zero_phi_hubspot_and_teams_handoff",
            args,
            _error(f"internal_error: {type(exc).__name__}"),
            internal_error=exc,
        )


# ---------------------------------------------------------------------------
# Tool 6 - partner resolution pack
# ---------------------------------------------------------------------------


def _tpa_message(claim: str, tpa: str, owner: str) -> str:
    return f"""# TPA Message - Claim #{claim}

**To:** {tpa} - Account Management
**From:** Aegle Health Partners - Client Partnerships
**Subject:** Claim #{claim}: Tranche 1 of $1,700,000 approved; $250,000 held pending a curable signature fix

Dear Account Management Team,

Thank you for the advance request for claim #{claim} under policy {POLICY_NUMBER}. We have completed the first-pass adjudication review and want to share the position clearly.

**Approved now - Tranche 1: $1,700,000.** This amount is approved for the next Finance/Accounting disbursement run, subject to release by Finance.

**Held - Tranche 2: $250,000 (curable).** The employer CFO signature line on the advance request is blank and the carrier countersignature is missing. This is a documentation defect, not a coverage denial, and it can be cured.

**Unsupported balance: $850,000**, made up of $350,000 in non-covered FL48 charges and a $500,000 laser deductible gap. Line-item detail is available on the schedule; no clinical records are included here.

**Cure checklist - three steps:**
1. Obtain the Employer CFO signature on the advance request certification.
2. Obtain the carrier countersignature on the same instrument.
3. Return the fully executed request to Aegle Client Partnerships for same-day release of the $250,000 hold.

**Target:** all three steps within 5 business days of this message. We are glad to walk through the line-item detail on a call - please propose two windows that work for your team.

Regards,
{owner}
VP, Client Partnerships
Aegle Health Partners (d/b/a Aegle Capital)
"""


def _finance_memo(claim: str, tpa: str, owner: str) -> str:
    return f"""# Finance Memo - Claim #{claim} Tranche Release

**To:** Finance & Accounting
**From:** Client Partnerships - {owner}
**Re:** Claim #{claim} - approved disbursement, signature hold, and prevented gap
**Policy:** {POLICY_NUMBER} - {CARRIER} (TPA: {tpa})

## Position

| Line | Amount |
|---|---|
| Tranche 1 - approved, pending Finance release | $1,700,000 |
| Tranche 2 - held pending signature cure | $250,000 |
| Requested advance | $2,800,000 |
| Total gap prevented (not payable) | $1,100,000 |

## Composition of the $1,100,000 gap

- $500,000 laser deductible gap ($750,000 separate specific deductible less the $250,000 base specific deductible)
- $350,000 non-covered FL48 charges (experimental/investigational, private-room differential, off-label drug, and convenience items)
- $250,000 signature-held Tranche 2

## Controls

- Double approval: Client Partnerships and Finance must both approve before any release.
- Signature verification: the Employer CFO signature and carrier countersignature must both be present before the $250,000 hold is released.
- No PHI: this memo uses de-identified claim references only; no diagnosis, member identity, or service dates are included.

## Action

Approve and release $1,700,000 on the next payment run. Keep $250,000 in the Tranche 2 suspense position until the executed request is returned.

This pack is a draft, not an authorization; Finance retains release authority.
"""


def _playbook_update(claim: str, tpa: str, owner: str) -> str:
    return f"""# Playbook Update - 1/1 Readiness Check (Stop-Loss Laser & Signature Controls)

**Owner:** {owner}
**Due:** 20 November 2026 - before the policy renewal on 1 January 2027
**Scope:** every renewing self-funded group with a specific stop-loss deductible
**Trigger:** claim #{claim} with {tpa}

## Why this check exists

Claim #{claim} exposed three preventable traps: an unflagged renewal laser, a lasered deductible applied above the base deductible, and a missing Employer CFO signature plus carrier countersignature at onboarding.

## Three checks

1. **Endorsements after Schedule A.** Confirm every laser / separate-specific-deductible endorsement is dated, signed, and issued after Schedule A. Flag any laser that appears only on a summary page.
2. **Base vs separate specific deductible.** Reconcile the base specific deductible against each lasered separate specific deductible. Record the delta and require underwriting sign-off where the laser exceeds the base.
3. **Employer CFO + carrier countersignature at onboarding.** Verify both signatures on the advance request and policy amendment at onboarding, not at claim time.

## Acceptance criteria

- All three checks completed and evidenced for every renewing group before 1 December 2026.
- Zero policies with an unsigned laser endorsement or a missing countersignature at renewal.
- Every laser above the base deductible documented with underwriting rationale and communicated to the TPA.
"""


@mcp.tool()
def generate_partner_resolution_pack(partner_tpa: str, claim_id: str) -> dict:
    """Generate a zero-PHI partner resolution pack: TPA message, finance memo, and playbook update.

    All three Markdown drafts are scanned for PHI before return.  The pack reports
    zero_phi and a PASS phi_scan, uses exact approved/hold/gap amounts, and contains
    no diagnosis codes, claimant identity, or dates of service.
    """
    audit_id = _new_audit_id()
    args = {"partner_tpa": partner_tpa, "claim_id": claim_id}
    try:
        if not isinstance(partner_tpa, str) or not isinstance(claim_id, str):
            return _finalize(
                audit_id,
                "generate_partner_resolution_pack",
                args,
                _error("partner_tpa and claim_id must be strings"),
            )

        fields_stripped: list[str] = []
        clean_claim, claim_stripped = _sanitize_text(claim_id, "claim_id", 64)
        clean_tpa, tpa_stripped = _sanitize_text(partner_tpa, "partner_tpa", 120)
        fields_stripped.extend(claim_stripped)
        fields_stripped.extend(tpa_stripped)

        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", clean_claim):
            return _finalize(
                audit_id,
                "generate_partner_resolution_pack",
                args,
                _error(
                    "claim_id must match [A-Za-z0-9_-]{1,64} after PHI sanitation",
                    fields_stripped=fields_stripped,
                ),
            )
        if not clean_tpa:
            return _finalize(
                audit_id,
                "generate_partner_resolution_pack",
                args,
                _error("partner_tpa is empty after sanitation"),
            )

        owner = "Patrick Feit"
        drafts = {
            "tpa_message": _tpa_message(clean_claim, clean_tpa, owner),
            "finance_memo": _finance_memo(clean_claim, clean_tpa, owner),
            "playbook_update": _playbook_update(clean_claim, clean_tpa, owner),
        }
        findings = _scan_texts(drafts)
        if findings:
            return _finalize(
                audit_id,
                "generate_partner_resolution_pack",
                args,
                _error(
                    "resolution pack failed the zero-PHI scan",
                    zero_phi=False,
                    phi_scan={
                        "phi_detected": True,
                        "phi_field_count": len(findings),
                        "fields_stripped": fields_stripped,
                        "input_redactions": list(fields_stripped),
                        "redaction_count": len(fields_stripped),
                        "patterns_checked": PATTERNS_CHECKED,
                        "findings": findings,
                        "result": "FAIL",
                    },
                ),
            )

        response = {
            "ok": True,
            "zero_phi": True,
            "claim": {
                "claim_id": clean_claim,
                "partner_tpa": clean_tpa,
                "carrier": CARRIER,
                "policy_number": POLICY_NUMBER,
                "employer": EMPLOYER,
            },
            "amounts": {
                "approved_tranche_1": float(APPROVED_TRANCHE_1),
                "tranche_2_hold": float(SIGNATURE_HOLD),
                "requested_advance": float(REQUESTED_ADVANCE),
                "total_gap": float(REQUESTED_ADVANCE - APPROVED_TRANCHE_1),
                "non_covered_fl48": float(FL48_NON_COVERED),
                "laser_gap": float(LASERED_DEDUCTIBLE - BASE_SPECIFIC_DEDUCTIBLE),
                "unsupported_balance": float(FL48_NON_COVERED + LASERED_DEDUCTIBLE - BASE_SPECIFIC_DEDUCTIBLE),
            },
            "tpa_message": drafts["tpa_message"],
            "finance_memo": drafts["finance_memo"],
            "playbook_update": drafts["playbook_update"],
            "phi_scan": {
                "phi_detected": False,
                "phi_field_count": 0,
                "fields_stripped": fields_stripped,
                "input_redactions": list(fields_stripped),
                "redaction_count": len(fields_stripped),
                "patterns_checked": PATTERNS_CHECKED,
                "result": "PASS",
            },
            "generated_at": _now_iso(),
        }
        return _finalize(audit_id, "generate_partner_resolution_pack", args, response)
    except Exception as exc:
        return _finalize(
            audit_id,
            "generate_partner_resolution_pack",
            args,
            _error(f"internal_error: {type(exc).__name__}"),
            internal_error=exc,
        )


if __name__ == "__main__":
    mcp.run()
