"""Deterministinen gate-logiikka — jaettu PreToolUse-hookin ja testien kesken.

Sama "refuse, don't guess" -periaate kuin standalone-projektissa, nyt kirjoituksen
(write_vat_treatment) porttina: agentti ei saa kirjoittaa ALV-käsittelyä jota faktat
eivät yksiselitteisesti tue. Epävarma → eskaloi. Injektio/ristiriita → torju.

HAVAINNOLLISTAVA sääntö — ei lakitulkinta. Tuotannossa domain-asiantuntijan omistama.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import unicodedata

INJECTION_PATTERNS = [
    r"ohita\s+(aiemma|edell|kaikki)",
    r"ignore\s+(previous|all|prior)",
    r"merkitse.*?alv\s*0",
    r"set\s+vat\s*(to\s*)?0",
    r"\bälä\s+eskaloi\b",
    r"do\s+not\s+escalate",
    r"järjestelmälle\s*:",
    r"\bsystem\s*:",
]
_INJECTION_RE = [re.compile(p, re.DOTALL) for p in INJECTION_PATTERNS]
MAX_INPUT_CHARS = 50_000

ALLOW, DENY = "ALLOW", "DENY"


def scan_for_injection(raw_text: str) -> str | None:
    norm = unicodedata.normalize("NFC", raw_text).casefold()
    for rx in _INJECTION_RE:
        if rx.search(norm):
            return rx.pattern
    return None


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    raw_text: str
    service_is_construction: bool | None
    supplier_sells_construction: bool | None
    buyer_resells_construction: bool | None


def correct_treatment(inv: Invoice) -> str | None:
    """Deterministinen sääntö. None = monitulkintainen (jokin ennakkoehto tuntematon)."""
    facts = (inv.service_is_construction, inv.supplier_sells_construction, inv.buyer_resells_construction)
    if any(f is None for f in facts):
        return None
    if all(facts):
        return "KÄÄNNETTY_ALV_0%"
    return "NORMAALI_ALV"


def evaluate_write(inv: Invoice, proposed_treatment: str) -> tuple[str, str, str]:
    """Portin päätös kirjoitukselle. Palauttaa (decision, kind, reason).

    kind ∈ {PASS, ESCALATE, BLOCK}. Gate käyttää GROUND TRUTH -faktoja (ei agentin
    väittämiä), joten agentti ei voi valehdella faktoja päästäkseen läpi.
    """
    if len(inv.raw_text) > MAX_INPUT_CHARS:
        return DENY, "ESCALATE", "Syöte poikkeavan pitkä — ei kirjoiteta automaattisesti, ihmiselle."
    inj = scan_for_injection(inv.raw_text)
    if inj is not None:
        return DENY, "BLOCK", "Prompt injection torjuttu; ehdotettua arvoa ei kirjoiteta."
    correct = correct_treatment(inv)
    if correct is None:
        return DENY, "ESCALATE", "Faktat monitulkintaiset — ei kirjoiteta arvausta, ohjataan ihmiselle."
    if proposed_treatment != correct:
        return DENY, "BLOCK", f"Ehdotettu '{proposed_treatment}' ristiriidassa säännön ('{correct}') kanssa."
    return ALLOW, "PASS", f"Vahvistettu deterministisesti: {correct}."
