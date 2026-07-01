# Invoice VAT — Claude Code -orkestrointidemo

> **Huom — tämä tiedosto on havainnollistava/informatiivinen, ei toiminnallinen.**
> `claude plugin tag` varoittaa tästä suoraan: pluginin juuren `CLAUDE.md` ei lataudu
> projektikontekstiksi Claude Codessa (dokumentoitu rajoitus). Se ei siis ohjaa mallin
> käytöstä ajon aikana — se on ihmislukijalle tarkoitettu yleiskuvaus repon tarkoituksesta.
>
> **Kaikki toiminnallinen ohjaus on kahdessa paikassa:**
> - `skills/process-invoice/SKILL.md` — työnkulku ja ehdoton "älä arvaa" -sääntö
> - `hooks/vat_gate.py` + `hooks/hooks.json` — deterministinen gate, joka ei luota
>   agentin väitteisiin vaan laskee päätöksen aina uudelleen ground truthista
>
> Tämä on myös se rakenne joka live-verifioinnissa todistettiin toimivaksi
> (ks. `MITEN-RAKENNETTIIN.md`) — CLAUDE.md ei ollut osa testattua polkua missään vaiheessa.

## Mitä tämä on

Osoittaa Claude Coden runtime-primitiivit yhdessä kriittisen datapolun ympärillä:
skill (työnkulku) · subagentti (eristetty tarkastus) · MCP-server (mock-ERP) ·
PreToolUse-hook (deterministinen gate).

## Työnkulku (kuvaus, ei ohjaus)

Käyttäjä käynnistää `process-invoice`-skillin. Useille laskuille skilli delegoi
tarkastuksen `invoice-inspector`-subagentille. Kriittinen kirjoitus
(`write_vat_treatment`) menee aina PreToolUse-hookin läpi ennen ERP-kirjausta.
