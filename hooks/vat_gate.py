#!/usr/bin/env python3
"""PreToolUse-hook: deterministinen gate write_vat_treatment-kutsun edessä.

Exit-koodit (varmistettu Claude Code -dokeista):
  0 = salli (PASS)
  2 = kiellä (BLOCK tai ESCALATE), syy stderriin Claudelle
  (1 = salli varoituksella — ei käytössä tässä; eskalointi on kielto, ei varoitus)

Gate lukee GROUND TRUTH -faktat jaetusta datasta, ei luota agentin syötteeseen
muuhun kuin invoice_id + ehdotettu treatment.
"""
import sys
import os
import json

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.join(_here, "..", "mcp_server"))

from gate_core import Invoice, evaluate_write, ALLOW  # noqa: E402
from mock_data import get_invoice_facts               # noqa: E402

TARGET_TOOL_SUFFIX = "write_vat_treatment"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("Gate: hook-syötettä ei voitu jäsentää — kriittistä kirjoitusta ei sallita.", file=sys.stderr)
        sys.exit(2)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if not tool_name.endswith(TARGET_TOOL_SUFFIX):
        sys.exit(0)

    invoice_id = tool_input.get("invoice_id")
    proposed = tool_input.get("treatment", "")

    facts = get_invoice_facts(invoice_id)
    if facts is None:
        print(f"Gate: tuntematon lasku {invoice_id!r} — ei kirjoiteta.", file=sys.stderr)
        sys.exit(2)

    inv = Invoice(invoice_id=invoice_id, **facts)
    decision, kind, reason = evaluate_write(inv, proposed)

    if decision == ALLOW:
        sys.exit(0)

    print(f"Gate [{kind}]: {reason}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
