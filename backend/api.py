"""FastAPI backend for the billing agents workflow."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.billing_rules import get_billing_rules
from backend.config import settings
from backend.document_loader import load_packet_from_corpus
from backend.orchestration.workflow import run_corpus_audit_async, run_uploaded_audit_async
from backend.schemas import AuditWorkflowOutput, SUPPORTED_BILLING_TYPES


app = FastAPI(
    title="Billing Agents API",
    description="FastAPI layer for OpenAI Agents SDK invoice validation.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CorpusAuditRequest(BaseModel):
    billing_type: str
    session_id: str | None = None


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "api_key_present": settings.api_key_present,
        "model": settings.model,
        "vision_model": settings.vision_model,
        "fast_model": settings.fast_model,
    }


@app.get("/billing-types")
def billing_types() -> dict:
    return {"billing_types": list(SUPPORTED_BILLING_TYPES)}


@app.get("/billing-types/{billing_type}/rules")
def billing_type_rules(billing_type: str) -> dict:
    _validate_billing_type(billing_type)
    return get_billing_rules(billing_type).model_dump()


@app.get("/billing-types/{billing_type}/documents")
def corpus_documents(billing_type: str) -> dict:
    _validate_billing_type(billing_type)
    packet = load_packet_from_corpus(billing_type)
    return {
        "billing_type": packet.billing_type,
        "service_agreements": [asset.model_dump() for asset in packet.service_agreements],
        "invoices": [asset.model_dump() for asset in packet.invoices],
        "billing_evidence": [asset.model_dump() for asset in packet.billing_evidence],
        "payment_records": [asset.model_dump() for asset in packet.payment_records],
    }


@app.post("/audit/corpus", response_model=AuditWorkflowOutput)
async def audit_corpus(request: CorpusAuditRequest) -> AuditWorkflowOutput:
    _validate_billing_type(request.billing_type)
    try:
        return await run_corpus_audit_async(request.billing_type, session_id=request.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/audit/upload", response_model=AuditWorkflowOutput)
async def audit_upload(
    billing_type: Annotated[str, Form()],
    session_id: Annotated[str | None, Form()] = None,
    service_agreements: Annotated[list[UploadFile], File()] = [],
    invoices: Annotated[list[UploadFile], File()] = [],
    billing_evidence: Annotated[list[UploadFile], File()] = [],
    payment_records: Annotated[list[UploadFile], File()] = [],
) -> AuditWorkflowOutput:
    _validate_billing_type(billing_type)
    _require_files("service_agreements", service_agreements)
    _require_files("invoices", invoices)
    _require_files("billing_evidence", billing_evidence)
    _require_files("payment_records", payment_records)

    with TemporaryDirectory(prefix="billing-agent-api-") as temp_dir:
        root = Path(temp_dir)
        agreement_paths = await _save_uploads(service_agreements, root / "service_agreements")
        invoice_paths = await _save_uploads(invoices, root / "invoices")
        evidence_paths = await _save_uploads(billing_evidence, root / "billing_evidence")
        payment_paths = await _save_uploads(payment_records, root / "payment_records")
        try:
            return await run_uploaded_audit_async(
                billing_type=billing_type,
                service_agreements=agreement_paths,
                invoices=invoice_paths,
                billing_evidence=evidence_paths,
                payment_records=payment_paths,
                session_id=session_id,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc


def _validate_billing_type(billing_type: str) -> None:
    if billing_type not in SUPPORTED_BILLING_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported billing type: {billing_type}")


def _require_files(field_name: str, files: list[UploadFile]) -> None:
    if not files:
        raise HTTPException(status_code=400, detail=f"At least one file is required for {field_name}.")


async def _save_uploads(files: list[UploadFile], target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for upload in files:
        file_name = Path(upload.filename or "uploaded_file").name
        path = target_dir / file_name
        path.write_bytes(await upload.read())
        paths.append(path)
    return paths

