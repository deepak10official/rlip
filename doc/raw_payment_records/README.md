# Raw Payment Records

This folder contains professional Word payment records for the billing validation corpus.

Each billing type has two DOCX records:

| Billing type | Records |
|---|---:|
| Managed Services | 2 |
| ERP Based | 2 |
| Time and Materials | 2 |
| Time and Materials Over Cap | 2 |
| Outcome Based | 2 |
| Milestone Based | 2 |
| Device Based | 2 |
| ARC | 2 |
| RRC | 2 |

The records match the invoice IDs and customer names from the previously generated invoice set. Each billing type includes one fully paid record and one pending, short-paid, unpaid, or unapplied-cash record.

Inside each pending sample, the payment summary includes a non-zero `Pending payment / cash issue amount` row. The payment-details table also carries the same pending amount or pending cash issue amount.

## Pending Payment Samples

| Billing type | Pending payment record |
|---|---|
| Managed Services | `managed_services/redwood_pending_payment_record_02.docx` |
| ERP Based | `erp_based/orion_pending_payment_record_02.docx` |
| Time and Materials | `time_and_materials/meridian_pending_payment_record_02.docx` |
| Time and Materials Over Cap | `time_and_materials_over_cap/metrotransit_pending_payment_record_02.docx` |
| Outcome Based | `outcome_based/clearwater_pending_payment_record_02.docx` |
| Milestone Based | `milestone_based/northstar_pending_payment_record_02.docx` |
| Device Based | `device_based/supplypro_pending_payment_record_02.docx` |
| ARC | `arc/deltabank_pending_payment_record_02.docx` |
| RRC | `rrc/citynet_pending_payment_record_02.docx` |

## Fully Paid Samples

| Billing type | Fully paid record |
|---|---|
| Managed Services | `managed_services/northwind_remittance_advice_01.docx` |
| ERP Based | `erp_based/terrabuild_bank_receipt_advice_01.docx` |
| Time and Materials | `time_and_materials/bluepeak_cash_receipt_01.docx` |
| Time and Materials Over Cap | `time_and_materials_over_cap/apex_payment_allocation_01.docx` |
| Outcome Based | `outcome_based/lumina_wire_remittance_01.docx` |
| Milestone Based | `milestone_based/crownbank_payment_application_01.docx` |
| Device Based | `device_based/supplypro_ach_receipt_01.docx` |
| ARC | `arc/omniretail_receivables_statement_01.docx` |
| RRC | `rrc/blueharbor_renewal_payment_01.docx` |
