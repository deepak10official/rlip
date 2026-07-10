"""Shared structured outputs for the agent workflow."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


BillingType = Literal[
    "arc",
    "device_based",
    "managed_services",
    "milestone_based",
    "outcome_based",
    "rrc",
    "time_and_materials",
    "time_and_materials_over_cap",
]


SUPPORTED_BILLING_TYPES: tuple[str, ...] = (
    "arc",
    "device_based",
    "managed_services",
    "milestone_based",
    "outcome_based",
    "rrc",
    "time_and_materials",
    "time_and_materials_over_cap",
)


class DocumentCategory(str, Enum):
    service_agreement = "service_agreement"
    invoice = "invoice"
    billing_evidence = "billing_evidence"
    payment_record = "payment_record"


class InvoiceStatus(str, Enum):
    valid = "valid"
    invalid = "invalid"
    needs_review = "needs_review"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DocumentAsset(BaseModel):
    document_id: str
    category: DocumentCategory
    file_name: str
    path: str
    extension: str
    billing_type: str | None = None
    customer_hint: str | None = None
    extracted_text: str = ""
    parse_status: str = "parsed"


class DocumentPacket(BaseModel):
    billing_type: str
    service_agreements: list[DocumentAsset] = Field(default_factory=list)
    invoices: list[DocumentAsset] = Field(default_factory=list)
    billing_evidence: list[DocumentAsset] = Field(default_factory=list)
    payment_records: list[DocumentAsset] = Field(default_factory=list)

    def all_assets(self) -> list[DocumentAsset]:
        return [
            *self.service_agreements,
            *self.invoices,
            *self.billing_evidence,
            *self.payment_records,
        ]


class MissingDocument(BaseModel):
    category: DocumentCategory
    reason: str


class BillingRuleSet(BaseModel):
    billing_type: str
    document_format: list[str]
    invoice_validation_rules: list[str]
    evidence_rules: list[str]
    payment_rules: list[str]
    clean_scenario_indicators: list[str]
    issue_scenario_indicators: list[str]
    corrected_invoice_rules: list[str]


class OrchestrationPlan(BaseModel):
    billing_type: str
    objective: str
    required_checks: list[str]
    missing_documents: list[MissingDocument] = Field(default_factory=list)


class IntakeSummary(BaseModel):
    billing_type: str
    document_count: int
    service_agreement_count: int
    invoice_count: int
    billing_evidence_count: int
    payment_record_count: int
    detected_customers: list[str] = Field(default_factory=list)
    missing_documents: list[MissingDocument] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ContractRule(BaseModel):
    rule_name: str
    rule_text: str
    source_document: str
    confidence: float = Field(ge=0, le=1)


class ContractRuleSummary(BaseModel):
    billing_type: str
    rules: list[ContractRule]
    pricing_terms: list[str] = Field(default_factory=list)
    acceptance_terms: list[str] = Field(default_factory=list)
    caps_or_limits: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class EvidenceFact(BaseModel):
    fact: str
    source_document: str
    supports_billing: bool
    confidence: float = Field(ge=0, le=1)


class EvidenceSummary(BaseModel):
    billing_type: str
    facts: list[EvidenceFact]
    exceptions: list[str] = Field(default_factory=list)


class VisionDocumentObservation(BaseModel):
    file_name: str
    category: DocumentCategory
    customer_name: str | None = None
    document_type: str
    key_values: list[str] = Field(default_factory=list)
    line_items_or_rows: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    validation_relevant_notes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class VisionExtractionReport(BaseModel):
    billing_type: str
    documents: list[VisionDocumentObservation]
    cross_document_notes: list[str] = Field(default_factory=list)
    missing_or_unclear_visuals: list[str] = Field(default_factory=list)


class PaymentIssue(BaseModel):
    issue_type: str
    description: str
    amount: float | None = None
    source_document: str
    severity: Severity = Severity.medium


class PaymentReconciliationSummary(BaseModel):
    status: InvoiceStatus
    issues: list[PaymentIssue] = Field(default_factory=list)
    paid_amount: float | None = None
    pending_amount: float | None = None
    reasoning: str


class InvoiceFinding(BaseModel):
    finding_type: str
    description: str
    source_documents: list[str]
    expected_value: str | None = None
    actual_value: str | None = None
    variance_amount: float | None = None
    severity: Severity = Severity.medium
    recommended_action: str


class InvoiceValidationReport(BaseModel):
    status: InvoiceStatus
    billing_type: str
    summary: str
    findings: list[InvoiceFinding] = Field(default_factory=list)
    source_documents: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class CorrectedInvoiceLine(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float
    change_reason: str
    source_documents: list[str]


class CorrectedInvoice(BaseModel):
    should_generate: bool
    customer_name: str | None = None
    billing_type: str
    currency: str = "USD"
    line_items: list[CorrectedInvoiceLine] = Field(default_factory=list)
    subtotal: float | None = None
    adjustments: float | None = None
    total: float | None = None
    notes: list[str] = Field(default_factory=list)


class AuditWorkflowOutput(BaseModel):
    status: InvoiceStatus
    billing_type: str
    executive_summary: str
    validation_report: InvoiceValidationReport
    payment_summary: PaymentReconciliationSummary
    corrected_invoice: CorrectedInvoice | None = None
    source_documents: list[str]
    guardrail_notes: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
