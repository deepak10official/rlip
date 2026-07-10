"""File-backed storage for completed audit results."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from backend.config import settings
from backend.schemas import AuditResultRecord, AuditWorkflowOutput, InvoiceFinding


_SAFE_ID_PATTERN = re.compile(r"^[a-z0-9_-]+$")


def save_audit_result(report: AuditWorkflowOutput) -> AuditResultRecord:
    """Persist an audit report as a JSON file and return its history record."""

    settings.results_root.mkdir(parents=True, exist_ok=True)
    completed_at = datetime.now().astimezone()
    audit_id = _unique_audit_id(report.billing_type, completed_at)
    result = report.model_copy(update={"audit_id": audit_id, "completed_at": completed_at.isoformat()})
    findings = result.validation_report.findings
    record = AuditResultRecord(
        id=audit_id,
        billing_type=result.billing_type,
        completed_at=completed_at.isoformat(),
        status=result.status,
        finding_count=len(findings),
        total_variance=_total_variance(findings),
        document_count=len(result.source_documents),
        result=result,
    )
    _record_path(audit_id).write_text(record.model_dump_json(indent=2))
    return record


def list_audit_results() -> list[AuditResultRecord]:
    """Return saved audit records newest first."""

    if not settings.results_root.exists():
        return []

    records: list[AuditResultRecord] = []
    for path in settings.results_root.glob("*.json"):
        try:
            records.append(AuditResultRecord.model_validate_json(path.read_text()))
        except Exception:
            continue

    return sorted(records, key=lambda record: record.completed_at, reverse=True)


def get_audit_result(audit_id: str) -> AuditResultRecord | None:
    """Load a single saved audit record by id."""

    if not _SAFE_ID_PATTERN.fullmatch(audit_id):
        return None

    path = _record_path(audit_id)
    if not path.exists():
        return None

    try:
        return AuditResultRecord.model_validate_json(path.read_text())
    except Exception:
        return None


def _unique_audit_id(billing_type: str, completed_at: datetime) -> str:
    base_id = f"{_sanitize_id_part(billing_type)}-{completed_at:%Y-%m-%d-%H-%M}"
    audit_id = base_id
    suffix = 2

    while _record_path(audit_id).exists():
        audit_id = f"{base_id}-{suffix}"
        suffix += 1

    return audit_id


def _sanitize_id_part(value: str) -> str:
    normalized = value.lower().replace(" ", "_")
    normalized = re.sub(r"[^a-z0-9_]+", "-", normalized)
    return normalized.strip("-") or "billing"


def _record_path(audit_id: str) -> Path:
    return settings.results_root / f"{audit_id}.json"


def _total_variance(findings: list[InvoiceFinding]) -> float:
    return sum(abs(finding.variance_amount or 0) for finding in findings)
