# Invoice Guard — Claude Code -plugin (skill · subagentti · MCP-server · hook)

Osoittaa **Claude Coden runtime-primitiivit** yhden kriittisen datapolun ympärillä, pakattuna asennettavaksi **pluginiksi**. Sisarprojekti standalone-guardrailille (`refuse-dont-guess`) — sama deterministinen gate, nyt Claude Code -natiivina orkestrointina.

> **Liputa, älä piilota:** kuvitteellinen keissi, ei oikeaa asiakasdataa. ALV-sääntö on havainnollistava placeholder, ei lakitulkinta. Artefakti todistaa primitiivien käytön ja deterministisen gaten — **ei tuotanto-orkestrointia skaalassa.**

---

## Arkkitehtuuri

| Primitiivi | Tehtävä | Sijainti (plugin-konventio) |
|-----------|---------|------------------------------|
| **Plugin-manifesti** | metadata, versio, kuvaus | `.claude-plugin/plugin.json` |
| **Itseään isännöivä marketplace** | tekee pluginista asennettavan | `.claude-plugin/marketplace.json` |
| **Skill** | `process-invoice` — toistettava ALV-työnkulku | `skills/process-invoice/SKILL.md` |
| **Subagentti** | `invoice-inspector` — laskun tarkastus eristetyssä kontekstissa | `agents/invoice-inspector.md` |
| **MCP-server** | mock-ERP: `list_pending_invoices`, `get_invoice`, `write_vat_treatment` | `mcp_server/server.py`, `.mcp.json` |
| **PreToolUse-hook** | deterministinen gate kriittisen kirjoituksen edessä | `hooks/vat_gate.py`, `hooks/hooks.json` |

Datavirta:

```
Claude Code (invoice-guard:process-invoice -skill)
  → get_invoice                    (MCP)
  → invoice-inspector               (subagentti, eristetty konteksti)
  → write_vat_treatment             (MCP, KRIITTINEN)
        └─ PreToolUse-hook ajetaan ENNEN kutsua → salli / kiellä
```

Plugin-rakenteessa polut viittaavat pluginin omaan asennushakemistoon `${CLAUDE_PLUGIN_ROOT}`-muuttujalla (dokumentoitu käytäntö), koska plugin kopioidaan asennettaessa cache-hakemistoon eikä suhteellinen polku `../` toimisi enää.

## Gate → hook: exit-koodit

| Tilanne | kind | Exit | Vaikutus |
|---------|------|------|----------|
| Faktat selkeät, ehdotus vastaa sääntöä | `PASS` | **0** | kirjoitus sallitaan |
| Faktat monitulkintaiset | `ESCALATE` | **2** | kirjoitus estetään, ihmiselle |
| Injektio tai ehdotus ristiriidassa säännön kanssa | `BLOCK` | **2** | kirjoitus estetään |

Exit **1** Claude Codessa tarkoittaa *"salli varoituksella"* — se sallisi kirjoituksen, joten sitä ei käytetä eskalointiin. Gate käyttää siis vain 0 (salli) ja 2 (kiellä); ero BLOCK vs ESCALATE näkyy stderr-viestissä.

## Mikä on verifioitu ja missä

**Verifioitu tässä repossa (deterministinen, ei vaadi Claude Codea):**
- Gate-logiikka: neljä tapausta oikein (`tests/test_gate.py`)
- Hookin exit-koodit simuloiduilla PreToolUse-payloadeilla, myös plugin-muotoisen `args`-kutsun kautta
- Kaikki neljä JSON-manifestia (`plugin.json`, `marketplace.json`, `.mcp.json`, `hooks/hooks.json`) validi JSON
- MCP-server importtaa ja rekisteröi kolme työkalua (mcp 1.28.1)

**Verifioit sinä omalla koneella (runtime-käytös):**
- Että Claude Code lataa pluginin, skillin ja subagentin oikein, ja että hook laukeaa oikeasti kirjoituksen edessä
- MCP-työkalujen tarkka nimeäväysi plugin-kontekstissa (`mcp__invoice-erp__*` — pluginin nimi ei dokumentaation perusteella etuliitä palvelimen nimeä, mutta tämä kannattaa vahvistaa `/mcp`-komennolla)

> Runtime-syntaksi voi vaihdella Claude Code -versioittain. Vahvista wiring `/hooks`, `/mcp` ja `/agents` -komennoilla — siellä elää tämän osan "verify by behaviour" -silmukka.

## Asennus ja ajo

**Kokeile ilman asennusta** (nopein tapa, repon juuresta):
```bash
pip install "mcp>=1.27,<2"
claude --plugin-dir .
```

**Asenna pluginina omasta marketplacesta:**
```bash
/plugin marketplace add mikko-lab/claude-code-invoice-guard
/plugin install invoice-guard@mikko-lab-portfolio
```

Kokeile:
```
Käsittele lasku INV-001     → selkeä → hook sallii (exit 0), KÄÄNNETTY_ALV kirjataan
Käsittele lasku INV-002     → ostajan rooli epäselvä → hook estää (exit 2), ihmiselle
Käsittele lasku INV-003     → injektio tekstissä → hook estää (exit 2)
```

Aja deterministiset tarkistukset ilman Claude Codea:
```bash
python3 -m pytest tests/ -q
```

## Tietoisesti rajattu ulos

Oikea ALV-laki (→ havainnollistava sääntö) · pysyvä tietokanta (mock in-memory) · autentikointi · usean laskun rinnakkaisajo · tuotantomittakaava · virallinen Anthropic-plugin-hakemisto (tämä on henkilökohtainen portfolio-marketplace, ei siihen pyritty). Ydin — neljä primitiiviä + deterministinen gate, pakattuna asennettavaksi pluginiksi — todistetaan ensin.
