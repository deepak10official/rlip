# Revenue Leakage Detective - Business Logic

## Overview

Revenue Leakage Detective is a finance audit workflow that identifies revenue that has been missed, mispriced, delayed, duplicated, or unapplied. The demo presentation describes a multi-agent AI system that audits enterprise finance documents and produces a quantified recovery report.

The main business goal is simple: compare what the customer contract says should happen against what was invoiced, paid, and supported by operational evidence, then calculate the financial impact.

## Business Problem

Enterprises can lose revenue silently when contract terms, service delivery, invoicing, pricing, and payment records do not line up. The presentation frames this as revenue leakage, with an estimated 1-5% of annual revenue lost and manual audits taking weeks.

The system is meant to reduce that manual audit cycle to minutes by automating document review, reconciliation, variance detection, and final reporting.

## Input Data

The workflow expects finance and customer evidence such as:

- Customer contracts and service agreements
- Invoices and invoice line items
- Billing evidence, such as timesheets, usage ledgers, SLA reports, approvals, device snapshots, and trackers
- Payment records, such as ACH receipts, remittance advice, bank receipts, payment applications, and receivables statements

## Core Actors

The business process is split into specialized agents:

| Actor | Business Responsibility | Output |
| --- | --- | --- |
| Orchestrator | Coordinates the full audit and preserves context across all agents. | Complete audit context |
| Billing Auditor | Compares contracted deliverables and service evidence against invoiced amounts. | Unbilled service findings |
| Pricing Validator | Compares contract pricing rules against invoice pricing. | Pricing discrepancies |
| Payment Reconciler | Matches payment records to invoices and customer accounts. | Payment issues |
| Recovery Agent | Combines all findings into a final recovery report. | Executive-ready report |

## End-to-End Workflow

1. A user starts a revenue audit.
2. The Orchestrator validates that the request is a legitimate financial audit.
3. The Orchestrator sends the same audit context to the specialist agents.
4. The Billing Auditor checks whether all delivered services were invoiced.
5. The Pricing Validator checks whether invoiced rates match contract terms.
6. The Payment Reconciler checks whether invoices and payments reconcile cleanly.
7. The Recovery Agent consolidates all findings, validates totals, and creates the final report.
8. The dashboard presents recoverable revenue, total impact, and recommended action areas.

## Detection Logic

### 1. Unbilled Services

The Billing Auditor looks for services that appear in contracts or supporting evidence but do not appear on invoices.

Typical checks:

- Contracted support hours vs. invoiced support hours
- SLA upgrades vs. invoice line items
- Training sessions vs. invoice line items
- Custom integrations or milestone work vs. invoice line items
- Delivered quantities vs. billed quantities

Business rule:

```text
unbilled_amount = contracted_or_delivered_amount - invoiced_amount
```

Only positive differences are treated as missed billing. In the demo, this category contributes `147,500`.

### 2. Pricing Errors

The Pricing Validator checks whether each invoice uses the correct contract rate, tier, discount, and effective date.

Typical checks:

- Expired discounts still being applied
- Incorrect volume tiers
- Incorrect monthly or usage-based rates
- Overbilling, which is flagged as a compliance/customer trust issue

Business rule:

```text
pricing_variance = expected_contract_price - actual_invoice_price
```

If the customer was undercharged, the variance is recoverable leakage. If the customer was overcharged, the issue should be corrected even though it is not revenue recovery. In the demo, pricing issues contribute `89,200`.

### 3. Payment Issues

The Payment Reconciler checks whether every invoice has a matching payment and whether every payment has a valid invoice allocation.

Typical checks:

- Duplicate payments
- Overdue invoices
- Unapplied cash
- Partial payments
- Payments matched to the wrong customer or invoice

Business rules:

```text
duplicate_payment_issue = repeated payment with same or highly similar customer, amount, date, invoice, or reference
overdue_amount = unpaid_invoice_amount when invoice age exceeds the collection threshold
unapplied_cash = payment_amount not matched to a valid invoice or account
```

In the demo, payment issues contribute `359,700`.

## Financial Rollup

The presentation's business logic now focuses on recoverable revenue from billing, pricing, and payment issues.

| Category | Amount |
| --- | ---: |
| Unbilled services | 147,500 |
| Pricing errors | 89,200 |
| Payment issues | 359,700 |
| Total impact | 596,400 |

Calculation:

```text
total_recoverable = unbilled_services + pricing_errors + payment_issues
total_recoverable = 147,500 + 89,200 + 359,700 = 596,400
```

## Required Finding Structure

Every finding should include enough information for a finance team to verify and act on it.

Recommended fields:

- Customer name
- Finding category
- Description of the issue
- Source documents used as evidence
- Contract term or expected value
- Invoice, payment, or actual value
- Dollar variance
- Recoverable classification
- Severity or priority
- Recommended next action

## Control Logic

The presentation describes three control mechanisms:

- Structured output: Findings are returned as typed records instead of free-form text.
- Guardrails: Inputs are checked to confirm the request is financial and legitimate; outputs are checked so totals add up correctly.
- Tracing: Every agent step, decision, and timestamp is logged for auditability.

These controls matter because finance findings need to be explainable, reproducible, and reviewable before anyone bills a customer or changes accounting records.

## Business Output

The final business output is a recovery report and dashboard showing:

- Total recoverable revenue
- Total revenue impact
- Findings grouped by category
- Customer-level issues
- Evidence-backed explanation for each issue
- Recommended next actions for finance, billing, collections, or customer success teams

## Important Note About The HTML

The supplied HTML is a presentation/demo of the business logic. It contains slide content, animations, audio timing, sample findings, sample dollar amounts, and a simulated terminal audit output. It does not itself perform the real document audit. The actual production implementation would need backend logic to parse documents, normalize financial records, run the agent workflow, validate calculations, and persist audit results.
