"""OpenAI Agents SDK guardrails for billing validation."""

from __future__ import annotations

from typing import Any

from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, input_guardrail, output_guardrail

from backend.schemas import AuditWorkflowOutput, InvoiceStatus


FINANCE_SCOPE_TERMS = {
    "invoice",
    "billing",
    "contract",
    "agreement",
    "payment",
    "evidence",
    "service",
    "revenue",
    "amount",
    "rate",
    "milestone",
    "timesheet",
    "ledger",
}


@input_guardrail(name="billing_scope_guardrail")
async def billing_scope_guardrail(
    context: RunContextWrapper[Any],
    agent: Agent[Any],
    input_data: str | list[Any],
) -> GuardrailFunctionOutput:
    text = _input_to_text(input_data).lower()
    in_scope = any(term in text for term in FINANCE_SCOPE_TERMS)
    return GuardrailFunctionOutput(
        output_info={
            "agent": agent.name,
            "in_scope": in_scope,
            "reason": "Input contains billing or finance document context."
            if in_scope
            else "Input does not appear to be a billing validation request.",
        },
        tripwire_triggered=not in_scope,
    )


@output_guardrail(name="final_report_quality_guardrail")
async def final_report_quality_guardrail(
    context: RunContextWrapper[Any],
    agent: Agent[Any],
    agent_output: Any,
) -> GuardrailFunctionOutput:
    issues: list[str] = []
    if not isinstance(agent_output, AuditWorkflowOutput):
        issues.append("Final output did not match AuditWorkflowOutput.")
    else:
        if not agent_output.source_documents:
            issues.append("Final report must cite source documents.")
        if not agent_output.executive_summary.strip():
            issues.append("Final report must include an executive summary.")
        if agent_output.status == InvoiceStatus.invalid and not agent_output.validation_report.findings:
            issues.append("Invalid invoice reports must include at least one finding.")
        if agent_output.status == InvoiceStatus.invalid and agent_output.corrected_invoice is None:
            issues.append("Invalid invoice reports must include a corrected invoice decision.")

    return GuardrailFunctionOutput(
        output_info={"agent": agent.name, "quality_issues": issues},
        tripwire_triggered=bool(issues),
    )


def _input_to_text(input_data: str | list[Any]) -> str:
    if isinstance(input_data, str):
        return input_data
    return "\n".join(str(item) for item in input_data)

