# Invoice VAT — Claude Code -orkestrointidemo

## Mitä tämä on
Osoittaa Claude Coden runtime-primitiivit yhdessä kriittisen datapolun ympärillä:
skill (työnkulku) · subagentti (eristetty tarkastus) · MCP-server (mock-ERP) ·
PreToolUse-hook (deterministinen gate).

## Ehdottomat säännöt (jokaisella vuorolla)
- ÄLÄ koskaan kirjoita ALV-käsittelyä jota faktat eivät yksiselitteisesti tue.
- Monitulkintainen lasku → ilmoita ihmiselle, älä arvaa.
- Kriittisen kirjoituksen `write_vat_treatment` valvoo deterministinen PreToolUse-hook.
  Hookin päätös on lopullinen; älä yritä kiertää sitä.

## Työnkulku
Käytä `process-invoice`-skilliä. Useille laskuille delegoi `invoice-inspector`-subagentille.
