"""Billing-type rules derived from the sample document formats."""

from __future__ import annotations

from backend.schemas import BillingRuleSet


RULES: dict[str, BillingRuleSet] = {
    "arc": BillingRuleSet(
        billing_type="arc",
        document_format=[
            "ARC means Actual Resource Consumption: the agreement defines billable resource categories, consumption units, rates or pricing tiers, billing period, and required usage evidence.",
            "Invoice uses an actual-consumption model with line items such as CPU hours, storage, network usage, seats consumed, API calls, or other measured resources.",
            "Evidence should include usage records, resource logs, consumption reports, account/resource identifiers, measured quantities, units, billing period, and pricing inputs.",
            "Payment record includes invoice total, cash received, cash applied, pending payment/cash issue amount, and open balance.",
        ],
        invoice_validation_rules=[
            "Invoice quantities are valid only when they match consumption records for the same customer, account/resource scope, and billing period.",
            "Unit prices, tiers, discounts, and calculations must match contract or approved rate card for each resource.",
            "Out-of-period usage, duplicate resources, unsupported adjustments, or wrong customer/account usage must not be billed.",
            "Missing usage logs or unclear units should produce needs_review; clear quantity/rate/calculation mismatches should produce invalid.",
        ],
        evidence_rules=[
            "Clean evidence has logs or consumption reports with quantities, units, billing period, customer/account identifiers, and pricing inputs.",
            "Issue evidence includes missing logs, unmatched totals, duplicate usage, out-of-period usage, unclear units, or unsupported adjustments.",
            "Compare invoice quantities and amounts to supported consumption totals and contract pricing.",
        ],
        payment_rules=[
            "Paid in full with zero pending/open balance is clean.",
            "Partially paid, pending internal review, or non-zero open balance is a payment issue, not automatically an invoice-generation error.",
        ],
        clean_scenario_indicators=[
            "Cloud infrastructure invoice quantities match CPU-hour, storage, and network consumption reports for the billing period.",
            "The invoice rate calculation matches the contract or approved rate card.",
        ],
        issue_scenario_indicators=[
            "Invoice includes unsupported resource usage, duplicated consumption rows, out-of-period usage, or a pricing calculation that does not tie to the rate card.",
            "Partial payment, pending usage review, or non-zero open balance should be reported separately as a payment issue.",
        ],
        corrected_invoice_rules=[
            "Recalculate the invoice from supported actual consumption records and approved contract pricing. Remove unsupported, duplicated, out-of-period, or wrong-account usage.",
        ],
    ),
    "device_based": BillingRuleSet(
        billing_type="device_based",
        document_format=[
            "Agreement defines per-device or per-asset billing, covered device classes, active/inactive status rules, decommissioning treatment, contract rates, and billing period.",
            "Invoice uses device-based line items such as managed laptops, endpoints, devices, or covered assets multiplied by a contract rate.",
            "Evidence should include an inventory or device snapshot with active devices, asset IDs, coverage status, additions/removals, decommissioned devices, and billing-period dates.",
            "Payment record includes invoice total, cash received, cash applied, pending payment/cash issue amount, and open balance.",
        ],
        invoice_validation_rules=[
            "Invoice quantity is valid only when it equals the active covered device or asset count for the billing period.",
            "Exclude decommissioned, inactive, duplicate, non-covered, or out-of-period devices unless the contract allows billing them.",
            "Per-device rates, minimums, prorations, and device classes must match contract or approved rate card.",
            "Missing inventory evidence, unclear status, or unsupported prorations should produce needs_review; clear overcount, wrong rate, or excluded-device billing should produce invalid.",
        ],
        evidence_rules=[
            "Clean evidence has inventory snapshots with active status, covered class, billing period, and auditable asset identifiers.",
            "Issue evidence includes decommissioned devices counted as active, duplicate asset IDs, inactive/non-covered devices, missing status, or stale inventory dates.",
            "Compare invoice device count and rate to active covered inventory after exclusions.",
        ],
        payment_rules=[
            "Paid in full with zero pending/open balance is clean.",
            "Partially paid, pending inventory review, disputed device counts, or non-zero open balance is a payment issue and may indicate invoice needs review.",
        ],
        clean_scenario_indicators=[
            "Active managed-device inventory count matches the invoice quantity and the per-device contract rate.",
            "Decommissioned and non-covered assets are excluded from the billed quantity.",
        ],
        issue_scenario_indicators=[
            "Invoice count includes decommissioned, inactive, duplicate, or non-covered devices.",
            "Payment is pending because the customer disputes the inventory count or device eligibility.",
        ],
        corrected_invoice_rules=[
            "Recalculate using only active covered devices or assets at supported contract rates. Remove decommissioned, inactive, duplicate, non-covered, or unsupported devices.",
        ],
    ),
    "managed_services": BillingRuleSet(
        billing_type="managed_services",
        document_format=[
            "Agreement defines a fixed monthly managed-services charge subject to SLA/KPI targets, service reporting, penalties, approvals, and other contractual obligations.",
            "Invoice uses Billing Model SUBSCRIPTION and managed-services monthly run descriptions.",
            "Evidence is an SLA/KPI service report or email roll-up with availability, uptime, P1/P2 response, monthly report timing, ticket SLA, billing exception clearance, repeat incident rate, penalties, and billing approval status.",
            "Payment record reports paid-in-full or partial payment/open balance.",
        ],
        invoice_validation_rules=[
            "Monthly managed-services invoice is valid when amount matches the fixed charge and evidence shows SLA/KPI compliance or no credit/penalty condition.",
            "Validate SLA compliance, KPI targets, service reports, penalty/service-credit calculations, and required approvals before billing.",
            "If SLA/KPI evidence misses targets, penalties remain unresolved, approval is absent, or evidence proposes a credit before invoice release, mark invalid or needs review.",
            "Invoice should reference the managed-services period and customer/service run in the agreement.",
        ],
        evidence_rules=[
            "Clean evidence meets availability, response, ticket, billing exception, repeat incident, service-report, and approval thresholds.",
            "Issue evidence includes low availability, P1/P2 misses, late report, ticket SLA miss, billing exception miss, repeat incidents, unresolved penalties, or missing approval.",
        ],
        payment_rules=[
            "Partial payment and non-zero pending/open balance should be reported as a payment issue.",
            "Full remittance equal to invoice total is clean.",
        ],
        clean_scenario_indicators=[
            "Northwind evidence shows 99.82% availability, 18-minute P1 response, 1h11 P2 update, KPIs above targets, and 42,500 paid in full.",
        ],
        issue_scenario_indicators=[
            "Northwind late-close evidence misses multiple SLA/KPI targets.",
            "Redwood payment record shows 15,000 pending/open balance.",
        ],
        corrected_invoice_rules=[
            "If service-credit terms and amounts are visible, subtract the supported service credit; otherwise mark corrected invoice as requiring finance review.",
        ],
    ),
    "milestone_based": BillingRuleSet(
        billing_type="milestone_based",
        document_format=[
            "Agreement says consultant invoices only when the applicable milestone deliverable is completed and accepted by the customer manager.",
            "Invoice uses Billing Model MILESTONE and describes a specific milestone code such as TR-M2, TR-M3, or OSS-M2.",
            "Evidence is an email acceptance/non-acceptance thread with explicit milestone acceptance language.",
            "Payment record maps payment to the milestone invoice and reports open balance.",
        ],
        invoice_validation_rules=[
            "Milestone invoice is valid only when evidence accepts the same milestone referenced on the invoice.",
            "Do not accept go-live notes, acceptance requests, or incomplete closure packs unless the customer says accepted/approved for billing.",
            "If evidence says cannot accept or do not bill, the invoice is invalid.",
        ],
        evidence_rules=[
            "Clean evidence includes accepted/approved billing, milestone code match, and expected value.",
            "Issue evidence includes cannot accept, missing closure pack, open critical defects, or do not bill language.",
        ],
        payment_rules=[
            "Paid in full against the accepted milestone is clean.",
            "Pending/short/unpaid milestone records should be reported separately as payment issues.",
        ],
        clean_scenario_indicators=[
            "CrownBank TR-M2 thread says accepted and milestone value should be 85,000; payment is paid in full.",
        ],
        issue_scenario_indicators=[
            "TR-M3 thread says cannot accept yet and do not bill until closure pack is complete and defects are resolved.",
            "Northstar pending records indicate issue scenario if payment is unresolved.",
        ],
        corrected_invoice_rules=[
            "Remove any milestone line that lacks explicit customer acceptance. Keep only accepted milestone lines with accepted values.",
        ],
    ),
    "outcome_based": BillingRuleSet(
        billing_type="outcome_based",
        document_format=[
            "Agreement says payment is made only when an agreed business outcome or deliverable is successfully achieved and accepted.",
            "Invoice uses Billing Model OUTPUT_BASED and describes accepted outcomes or verified outcome alerts.",
            "Evidence is an email approval/hold thread, acceptance certificate, deliverable record, or measurement report proving outcome completion and customer sign-off.",
            "Payment record reports paid-in-full or payment pending due to support attachment/acceptance issue.",
        ],
        invoice_validation_rules=[
            "Outcome invoice is valid only when evidence proves the deliverable/outcome was achieved, acceptance criteria were met, and customer sign-off is complete.",
            "If evidence says hold billing, workbook mismatch, exclusion issue, missing criteria/sign-off, or cannot accept current package, mark invalid.",
            "Expected amount must equal accepted outcome quantity times accepted unit price when visible.",
        ],
        evidence_rules=[
            "Clean evidence includes accepted outcome, completed deliverable, approved measurement window, accepted quantity, unit price, sign-off, and proceed-with-billing language.",
            "Issue evidence includes hold billing, incomplete deliverable, failed criteria, missing sign-off/support, workbook mismatch, or request for corrected workbook.",
        ],
        payment_rules=[
            "Payment pending with zero cash received is a payment issue and may reinforce missing support/acceptance.",
            "Paid in full for accepted outcomes is clean.",
        ],
        clean_scenario_indicators=[
            "Lumina accepted 3.00 conversion lift points at 18,500 each, expected amount 55,500, and paid in full.",
        ],
        issue_scenario_indicators=[
            "Lumina hold thread says attribution workbook does not match exclusion list and billing should be held.",
            "Clearwater payment record shows 52,080 pending because support attachment is missing.",
        ],
        corrected_invoice_rules=[
            "Remove unaccepted outcome charges. Keep only accepted outcomes with supported quantity, unit price, and amount.",
        ],
    ),
    "rrc": BillingRuleSet(
        billing_type="rrc",
        document_format=[
            "RRC means Recurring Resource Charges: the agreement defines fixed recurring charges for reserved or dedicated resources regardless of actual usage.",
            "Invoice uses recurring resource line items such as dedicated server, reserved support team, reserved capacity, or allocated resource charges for a billing period.",
            "Evidence should confirm resource allocation, contract validity, billing period, recurring rate, resource IDs/rosters, and any additions/removals.",
            "Payment record reports paid-in-full or disputed/pending recurring-resource balance.",
        ],
        invoice_validation_rules=[
            "RRC invoice is valid when the contract is active, period is correct, resources are reserved/allocated, and recurring rate matches contract.",
            "Actual usage need not equal the charge unless contract makes usage a billing condition.",
            "Do not bill unallocated resources, outside contract dates, duplicated periods, or unsupported recurring rates.",
            "Missing allocation evidence or unclear contract validity should produce needs_review; clear non-allocation, expired contract, wrong period, or wrong recurring rate should produce invalid.",
        ],
        evidence_rules=[
            "Clean evidence confirms reserved/dedicated allocation, active contract dates, period alignment, and recurring rate.",
            "Issue evidence has missing allocation, inactive/expired resource, overlapping period, incorrect rate, missing addition approval, or resources outside scope.",
        ],
        payment_rules=[
            "Partial payment with disputed allocation, rate, or period is a payment issue.",
            "Paid in full with zero open balance is clean.",
        ],
        clean_scenario_indicators=[
            "Dedicated server or reserved support-team charge matches active allocation records and the contracted monthly recurring rate.",
        ],
        issue_scenario_indicators=[
            "Invoice bills an unallocated, expired, duplicated, or out-of-period reserved resource.",
            "Payment is pending because the customer disputes resource allocation, billing period, or recurring rate.",
        ],
        corrected_invoice_rules=[
            "Keep only active allocated reserved/dedicated resources for the correct period at supported recurring rates. Remove unallocated, expired, duplicated, or unsupported resource charges.",
        ],
    ),
    "time_and_materials": BillingRuleSet(
        billing_type="time_and_materials",
        document_format=[
            "Agreement says billing is based on actual hours worked and materials used, with different resource roles carrying different hourly rates.",
            "Invoice uses Billing Model T&M with line items for approved labor hours by role and any approved materials or reimbursable costs.",
            "Evidence is a timesheet and/or material-cost support with employee, role/level, dates, start/end/break, billable or claimed hours, manager/customer approval, rate, material cost, and calculated/claimed amount.",
            "Payment record reports paid-in-full or short-paid amount tied to timesheet clarifications.",
        ],
        invoice_validation_rules=[
            "T&M invoice is valid only for actual hours and approved materials, with complete support and manager/customer approval.",
            "Expected labor amount is approved billable hours multiplied by the role rate.",
            "Expected material amount must be supported by cost evidence and allowed by contract.",
            "Claimed hours with missing start/end/break values, wrong role/rate, unsupported materials, or blank approval must not be treated as billable.",
        ],
        evidence_rules=[
            "Clean evidence has Billable Hrs, complete time fields, role/level, Approved By, total hours, rate, material support when billed, and calculated amount.",
            "Issue evidence has Claimed Hrs, incomplete time fields, wrong/missing role/rate, blank approval, unsupported materials, incomplete supervisor approval, or claimed amount only.",
        ],
        payment_rules=[
            "Short-pay tied to timing clarifications should be reported as payment issue and may indicate invoice review.",
            "Paid in full for approved T&M is clean.",
        ],
        clean_scenario_indicators=[
            "BluePeak timesheet has 40 approved hours at 145 and paid-in-full payment record.",
        ],
        issue_scenario_indicators=[
            "Draft timesheet has 44 claimed hours, missing time fields, blank approvals, and approval column incomplete.",
            "Meridian payment record shows 5,000 held back for timing clarifications.",
        ],
        corrected_invoice_rules=[
            "Recalculate using only approved hours with complete time entries, correct role rates, and supported material costs. Exclude unapproved or incomplete claimed entries and unsupported materials.",
        ],
    ),
    "time_and_materials_over_cap": BillingRuleSet(
        billing_type="time_and_materials_over_cap",
        document_format=[
            "Agreement says T&M billing is based on actual hours/materials but cannot exceed a predefined cap unless additional customer approval is obtained.",
            "Invoice uses Billing Model SOW_CAP or capped T&M descriptions for base work up to the cap plus any separately approved over-cap hours or materials.",
            "Evidence is a cap tracker with base hours/rates/amount, material costs, over-cap hours/rates/amount, contract cap, approval reference, and total billable amount.",
            "Payment record distinguishes base amount paid from over-cap portion pending approval.",
        ],
        invoice_validation_rules=[
            "Base amount up to the cap is valid when supported by approved hours/materials and tracker evidence.",
            "The agent must calculate total billable amount, compare it with the cap, identify overages, and validate customer approval if exceeded.",
            "Over-cap amount is valid only when every over-cap line has written customer approval/reference.",
            "Over-cap lines with blank approval reference, unsupported materials, or notes saying approval must be located are invalid or needs review.",
        ],
        evidence_rules=[
            "Clean evidence has contract cap, base subtotal, material-cost support, over-cap subtotal, total tracker amount, and approval reference for each over-cap line.",
            "Issue evidence has amount above cap without approval, blank approval references, unsupported materials, high over-cap subtotal, or note to locate approval before billing.",
        ],
        payment_rules=[
            "Pending over-cap is a payment issue and may reinforce missing approval.",
            "Paid in full for base plus approved over-cap is clean.",
        ],
        clean_scenario_indicators=[
            "Apex tracker has 32,000 base plus 2,225 approved over-cap with CAP-APPR reference and paid-in-full record.",
        ],
        issue_scenario_indicators=[
            "MetroTransit payment leaves 8,450 over-cap pending approval.",
            "Tracker B has 7,900 over-cap subtotal with blank approval references and note to locate approval before billing.",
        ],
        corrected_invoice_rules=[
            "Keep supported base amount up to the cap and approved over-cap only. Remove or hold over-cap amounts, unsupported materials, or excess charges without written customer approval.",
        ],
    ),
}


def get_billing_rules(billing_type: str) -> BillingRuleSet:
    try:
        return RULES[billing_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported billing type for rules: {billing_type}") from exc
