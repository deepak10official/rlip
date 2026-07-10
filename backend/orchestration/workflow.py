"""End-to-end OpenAI Agents SDK orchestration."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import uuid4

from agents import Runner, trace

from backend.agents import BillingAgents, build_agents
from backend.billing_rules import get_billing_rules
from backend.config import settings
from backend.document_loader import (
    load_packet_from_corpus,
    load_packet_from_uploads,
    packet_to_prompt,
)
from backend.orchestration.memory import JsonFileSession
from backend.schemas import (
    AuditWorkflowOutput,
    ContractRuleSummary,
    CorrectedInvoice,
    DocumentPacket,
    EvidenceSummary,
    IntakeSummary,
    InvoiceStatus,
    InvoiceValidationReport,
    OrchestrationPlan,
    PaymentReconciliationSummary,
    VisionExtractionReport,
)
from backend.vision_renderer import vision_input_items


class BillingAuditWorkflow:
    """Coordinates specialist agents for invoice validation."""

    def __init__(self, agents: BillingAgents | None = None) -> None:
        self.agents = agents or build_agents()

    async def run(self, packet: DocumentPacket, session_id: str | None = None) -> AuditWorkflowOutput:
        if not settings.api_key_present:
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to .env before running the agent workflow.")

        session_id = session_id or f"billing-{packet.billing_type}-{uuid4().hex[:8]}"
        session = JsonFileSession(session_id)
        packet_prompt = packet_to_prompt(packet)
        source_documents = [asset.file_name for asset in packet.all_assets()]
        billing_rules = get_billing_rules(packet.billing_type)

        with trace(
            "Billing Invoice Validation",
            group_id=session_id,
            metadata={"billing_type": packet.billing_type, "document_count": str(len(source_documents))},
        ):
            plan = await self._run_agent(
                self.agents.orchestrator,
                _prompt(
                    "Create an execution plan for this billing validation packet.",
                    packet_prompt,
                    {"billing_rules": billing_rules.model_dump()},
                ),
                OrchestrationPlan,
                session,
            )

            vision_extraction = await self._run_agent(
                self.agents.vision_document_reader,
                vision_input_items(
                    packet,
                    "Extract billing facts visually from these service agreement, invoice, evidence, and payment record previews.",
                ),
                VisionExtractionReport,
                session,
            )

            intake = await self._run_agent(
                self.agents.document_intake,
                _prompt(
                    "Build audit context for the document packet using the vision extraction as the primary reading source.",
                    packet_prompt,
                    {
                        "billing_rules": billing_rules.model_dump(),
                        "vision_extraction": vision_extraction.model_dump(),
                    },
                ),
                IntakeSummary,
                session,
            )

            contract = await self._run_agent(
                self.agents.contract_rule,
                _prompt(
                    "Extract contract rules from the service agreement documents.",
                    packet_prompt,
                    {
                        "plan": plan.model_dump(),
                        "intake": intake.model_dump(),
                        "billing_rules": billing_rules.model_dump(),
                        "vision_extraction": vision_extraction.model_dump(),
                    },
                ),
                ContractRuleSummary,
                session,
            )

            evidence = await self._run_agent(
                self.agents.evidence_validation,
                _prompt(
                    "Extract billing evidence facts from the raw evidence documents.",
                    packet_prompt,
                    {
                        "contract_rules": contract.model_dump(),
                        "intake": intake.model_dump(),
                        "billing_rules": billing_rules.model_dump(),
                        "vision_extraction": vision_extraction.model_dump(),
                    },
                ),
                EvidenceSummary,
                session,
            )

            invoice_report = await self._run_agent(
                self.agents.invoice_validation,
                _prompt(
                    "Validate whether the invoice was correctly generated.",
                    packet_prompt,
                    {
                        "plan": plan.model_dump(),
                        "intake": intake.model_dump(),
                        "billing_rules": billing_rules.model_dump(),
                        "vision_extraction": vision_extraction.model_dump(),
                        "contract_rules": contract.model_dump(),
                        "billing_evidence": evidence.model_dump(),
                    },
                ),
                InvoiceValidationReport,
                session,
            )

            payment_summary = await self._run_agent(
                self.agents.payment_reconciliation,
                _prompt(
                    "Reconcile the invoice against payment records.",
                    packet_prompt,
                    {
                        "billing_rules": billing_rules.model_dump(),
                        "vision_extraction": vision_extraction.model_dump(),
                        "invoice_validation": invoice_report.model_dump(),
                    },
                ),
                PaymentReconciliationSummary,
                session,
            )

            corrected_invoice: CorrectedInvoice | None = None
            if invoice_report.status == InvoiceStatus.invalid:
                corrected_invoice = await self._run_agent(
                    self.agents.corrected_invoice,
                    _prompt(
                        "Generate a corrected invoice draft or explain why one cannot be generated.",
                        packet_prompt,
                        {
                            "billing_rules": billing_rules.model_dump(),
                            "contract_rules": contract.model_dump(),
                            "billing_evidence": evidence.model_dump(),
                            "vision_extraction": vision_extraction.model_dump(),
                            "invoice_validation": invoice_report.model_dump(),
                        },
                    ),
                    CorrectedInvoice,
                    session,
                )

            final_report = await self._run_agent(
                self.agents.final_report,
                _prompt(
                    "Create the final billing audit report.",
                    packet_prompt,
                    {
                        "plan": plan.model_dump(),
                        "intake": intake.model_dump(),
                        "billing_rules": billing_rules.model_dump(),
                        "vision_extraction": vision_extraction.model_dump(),
                        "contract_rules": contract.model_dump(),
                        "billing_evidence": evidence.model_dump(),
                        "invoice_validation": invoice_report.model_dump(),
                        "payment_reconciliation": payment_summary.model_dump(),
                        "corrected_invoice": corrected_invoice.model_dump() if corrected_invoice else None,
                        "source_documents": source_documents,
                    },
                ),
                AuditWorkflowOutput,
                session,
            )
            return final_report

    async def _run_agent(self, agent, prompt, output_type, session: JsonFileSession):
        result = await Runner.run(
            agent,
            prompt,
            session=session,
            max_turns=6,
        )
        return result.final_output_as(output_type, raise_if_incorrect_type=True)


def run_corpus_audit(billing_type: str, session_id: str | None = None) -> AuditWorkflowOutput:
    return asyncio.run(run_corpus_audit_async(billing_type, session_id=session_id))


async def run_corpus_audit_async(billing_type: str, session_id: str | None = None) -> AuditWorkflowOutput:
    packet = load_packet_from_corpus(billing_type)
    return await BillingAuditWorkflow().run(packet, session_id=session_id)


def run_uploaded_audit(
    billing_type: str,
    service_agreements: list[Path],
    invoices: list[Path],
    billing_evidence: list[Path],
    payment_records: list[Path],
    session_id: str | None = None,
) -> AuditWorkflowOutput:
    return asyncio.run(
        run_uploaded_audit_async(
            billing_type=billing_type,
            service_agreements=service_agreements,
            invoices=invoices,
            billing_evidence=billing_evidence,
            payment_records=payment_records,
            session_id=session_id,
        )
    )


async def run_uploaded_audit_async(
    billing_type: str,
    service_agreements: list[Path],
    invoices: list[Path],
    billing_evidence: list[Path],
    payment_records: list[Path],
    session_id: str | None = None,
) -> AuditWorkflowOutput:
    packet = load_packet_from_uploads(
        billing_type=billing_type,
        service_agreements=service_agreements,
        invoices=invoices,
        billing_evidence=billing_evidence,
        payment_records=payment_records,
    )
    return await BillingAuditWorkflow().run(packet, session_id=session_id)


def _prompt(task: str, packet_prompt: str, context: dict | None = None) -> str:
    context_block = ""
    if context is not None:
        context_block = "\n\nSTRUCTURED CONTEXT:\n" + json.dumps(context, indent=2)
    return f"TASK:\n{task}\n\nDOCUMENT PACKET:\n{packet_prompt}{context_block}"
