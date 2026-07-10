"""Command-line entry point for the billing agent workflow."""

from __future__ import annotations

import argparse
import json

from backend.billing_rules import get_billing_rules
from backend.document_loader import load_packet_from_corpus
from backend.orchestration.workflow import run_corpus_audit
from backend.schemas import SUPPORTED_BILLING_TYPES


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a billing validation audit.")
    parser.add_argument("--billing-type", choices=SUPPORTED_BILLING_TYPES, help="Billing type to audit from documents corpus.")
    parser.add_argument("--session-id", help="Optional memory session id.")
    parser.add_argument("--list", action="store_true", help="List supported billing types.")
    parser.add_argument("--inspect-docs", action="store_true", help="Show document counts without calling OpenAI.")
    parser.add_argument("--show-rules", action="store_true", help="Show sample-derived billing rules without calling OpenAI.")
    args = parser.parse_args()

    if args.list:
        print("\n".join(SUPPORTED_BILLING_TYPES))
        return

    if not args.billing_type:
        parser.error("--billing-type is required unless --list is used.")

    if args.inspect_docs:
        packet = load_packet_from_corpus(args.billing_type)
        print(
            json.dumps(
                {
                    "billing_type": packet.billing_type,
                    "service_agreements": len(packet.service_agreements),
                    "invoices": len(packet.invoices),
                    "billing_evidence": len(packet.billing_evidence),
                    "payment_records": len(packet.payment_records),
                    "files": [asset.file_name for asset in packet.all_assets()],
                },
                indent=2,
            )
        )
        return

    if args.show_rules:
        print(get_billing_rules(args.billing_type).model_dump_json(indent=2))
        return

    report = run_corpus_audit(args.billing_type, session_id=args.session_id)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
