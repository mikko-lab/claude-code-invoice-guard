import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, "..", "hooks"))
sys.path.insert(0, os.path.join(_here, "..", "mcp_server"))

from gate_core import Invoice, evaluate_write, ALLOW, DENY  # noqa: E402
from mock_data import INVOICES                              # noqa: E402


def _inv(iid):
    return Invoice(invoice_id=iid, **INVOICES[iid])


def test_clear_matching_write_allowed():
    d, kind, _ = evaluate_write(_inv("INV-001"), "KÄÄNNETTY_ALV_0%")
    assert d == ALLOW and kind == "PASS"


def test_ambiguous_denied_as_escalate():
    d, kind, _ = evaluate_write(_inv("INV-002"), "KÄÄNNETTY_ALV_0%")
    assert d == DENY and kind == "ESCALATE"


def test_injection_denied_as_block():
    d, kind, _ = evaluate_write(_inv("INV-003"), "KÄÄNNETTY_ALV_0%")
    assert d == DENY and kind == "BLOCK"


def test_mismatch_denied_as_block():
    d, kind, _ = evaluate_write(_inv("INV-001"), "NORMAALI_ALV")
    assert d == DENY and kind == "BLOCK"


if __name__ == "__main__":
    # Ajaa ilman pytestiä: kerää test_-funktiot ja suorittaa ne.
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    ok = True
    for name, fn in tests:
        try:
            fn()
            print(f"  {name}: OK")
        except AssertionError as e:
            ok = False
            print(f"  {name}: FAIL ({e})")
    print("KAIKKI:", "OK" if ok else "FAIL")
