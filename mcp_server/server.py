"""Mock-ERP MCP-server (stdio) Claude Code -orkestrointidemoa varten.

Työkalut: list_pending_invoices, get_invoice, write_vat_treatment.
Kriittinen kirjoitus write_vat_treatment on gattitettu PreToolUse-hookilla
(plugin: hooks/hooks.json) — hook ajetaan ENNEN tätä kutsua ja voi estää sen.

SDK: official 'mcp' (>=1.27,<2). Asennus: pip install "mcp>=1.27,<2"
"""
from mcp.server.fastmcp import FastMCP
from mock_data import INVOICES

mcp = FastMCP("invoice-erp")


@mcp.tool()
def list_pending_invoices() -> list[str]:
    """Palauta käsittelyä odottavien laskujen tunnukset."""
    return list(INVOICES.keys())


@mcp.tool()
def get_invoice(invoice_id: str) -> dict:
    """Hae laskun tiedot tunnuksella."""
    inv = INVOICES.get(invoice_id)
    if inv is None:
        return {"error": f"tuntematon lasku {invoice_id}"}
    return {"invoice_id": invoice_id, **inv}


@mcp.tool()
def write_vat_treatment(invoice_id: str, treatment: str) -> dict:
    """Kirjaa ALV-käsittely laskulle. KRIITTINEN kirjoitus.

    Varsinaisen turvatarkistuksen tekee PreToolUse-hook ENNEN tätä kutsua.
    Jos suoritus pääsee tänne, hook on sallinut sen.
    """
    INVOICES.setdefault(invoice_id, {})["vat_treatment"] = treatment
    return {"invoice_id": invoice_id, "written": treatment, "status": "ok"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
