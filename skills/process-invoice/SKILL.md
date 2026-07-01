---
name: process-invoice
description: Käsittele saapuva ostolasku — hae tiedot, määritä ALV-käsittely ja kirjaa se. Käytä kun käyttäjä pyytää laskun ALV-käsittelyä.
---
# process-invoice

Toistettava työnkulku yhden ostolaskun ALV-käsittelyyn.

## Vaiheet
1. Hae laskun tiedot: `get_invoice(invoice_id)`.
2. Jos laskuja on useita tarkastettavana, delegoi tarkastus `invoice-inspector`-subagentille.
3. Päättele ALV-käsittely laskun faktojen perusteella (käännetty ALV vs normaali).
4. Kirjaa tulos: `write_vat_treatment(invoice_id, treatment)`.

## Ehdoton sääntö
Älä arvaa. Jos faktat ovat monitulkintaiset, ÄLÄ kirjoita arvausta — ilmoita että lasku vaatii ihmisen tarkistuksen. Kriittinen kirjoitus on lisäksi gattitettu deterministisellä PreToolUse-hookilla, joka estää epävarman tai ristiriitaisen kirjoituksen. Hookin päätös on lopullinen; älä yritä kiertää sitä.
