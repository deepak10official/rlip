"""Factory for all OpenAI Agents SDK agents."""

from __future__ import annotations

from dataclasses import dataclass

from agents import Agent

from backend.agents.guardrails import billing_scope_guardrail, final_report_quality_guardrail
from backend.config import settings
from backend.prompts import load_prompt
from backend.schemas import (
    AuditWorkflowOutput,
    ContractRuleSummary,
    CorrectedInvoice,
    EvidenceSummary,
    IntakeSummary,
    InvoiceValidationReport,
    OrchestrationPlan,
    PaymentReconciliationSummary,
    VisionExtractionReport,
)


@dataclass(frozen=True)
class BillingAgents:
    orchestrator: Agent
    vision_document_reader: Agent
    document_intake: Agent
    contract_rule: Agent
    evidence_validation: Agent
    invoice_validation: Agent
    payment_reconciliation: Agent
    corrected_invoice: Agent
    final_report: Agent


def build_agents() -> BillingAgents:
    """Create all agents with prompts, output schemas, and guardrails."""

    orchestrator = Agent(
        name="Billing Validation Orchestrator",
        instructions=load_prompt("orchestrator"),
        model=settings.fast_model,
        input_guardrails=[billing_scope_guardrail],
        output_type=OrchestrationPlan,
    )
    vision_document_reader = Agent(
        name="Vision Document Reader Agent",
        instructions=load_prompt("vision_document_reader"),
        model=settings.vision_model,
        input_guardrails=[billing_scope_guardrail],
        output_type=VisionExtractionReport,
    )
    document_intake = Agent(
        name="Audit Context Agent",
        instructions=load_prompt("document_intake"),
        model=settings.fast_model,
        input_guardrails=[billing_scope_guardrail],
        output_type=IntakeSummary,
    )
    contract_rule = Agent(
        name="Contract Rule Agent",
        instructions=load_prompt("contract_rule"),
        model=settings.model,
        input_guardrails=[billing_scope_guardrail],
        output_type=ContractRuleSummary,
    )
    evidence_validation = Agent(
        name="Evidence Validation Agent",
        instructions=load_prompt("evidence_validation"),
        model=settings.model,
        input_guardrails=[billing_scope_guardrail],
        output_type=EvidenceSummary,
    )
    invoice_validation = Agent(
        name="Invoice Validation Agent",
        instructions=load_prompt("invoice_validation"),
        model=settings.model,
        input_guardrails=[billing_scope_guardrail],
        output_type=InvoiceValidationReport,
    )
    payment_reconciliation = Agent(
        name="Payment Reconciliation Agent",
        instructions=load_prompt("payment_reconciliation"),
        model=settings.model,
        input_guardrails=[billing_scope_guardrail],
        output_type=PaymentReconciliationSummary,
    )
    corrected_invoice = Agent(
        name="Corrected Invoice Generation Agent",
        instructions=load_prompt("corrected_invoice"),
        model=settings.model,
        input_guardrails=[billing_scope_guardrail],
        output_type=CorrectedInvoice,
    )
    final_report = Agent(
        name="Final Billing Audit Report Agent",
        instructions=load_prompt("final_report"),
        model=settings.model,
        input_guardrails=[billing_scope_guardrail],
        output_guardrails=[final_report_quality_guardrail],
        output_type=AuditWorkflowOutput,
    )
    return BillingAgents(
        orchestrator=orchestrator,
        vision_document_reader=vision_document_reader,
        document_intake=document_intake,
        contract_rule=contract_rule,
        evidence_validation=evidence_validation,
        invoice_validation=invoice_validation,
        payment_reconciliation=payment_reconciliation,
        corrected_invoice=corrected_invoice,
        final_report=final_report,
    )
