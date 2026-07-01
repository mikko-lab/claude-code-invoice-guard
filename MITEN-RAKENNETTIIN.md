# Miten "Invoice Guard" rakennettiin
### Claude Code -plugin, ja mitä sen live-verifiointi paljasti

Tämä dokumentti ei kuvaa pluginin käyttöä (se on README:ssä). Se kuvaa **rakennus- ja verifiointiprosessin** — mukaan lukien kaksi todellista bugia jotka löytyivät vasta kun plugin oikeasti ajettiin Claude Codella, ei vain lukemalla koodia. Sisarprojekti `refuse-dont-guess` on standalone-guardrail ilman Claude Code -orkestrointia; tämä dokumentti on sen pariteetti tälle pluginille — eri tarina, koska rakennusprosessi oli erilainen.

> **Liputa, älä piilota:** kuvitteellinen keissi, ei oikeaa asiakasdataa. Katso README:n vastaava huomautus.

---

## 1. Scaffolding — rakenne ennen sisältöä

Plugin-hakemistorakenne (`.claude-plugin/`, `skills/`, `agents/`, `mcp_server/`, `hooks/`, `tests/`) luotiin yhdellä idempotentilla shell-skriptillä, joka kirjoittaa jokaisen tiedoston `cat << 'FILEEOF'`-lohkona. Tämä oli tietoinen valinta: skriptiä voi ajaa uudestaan, sen lopputulos on deterministinen, ja se toimii dokumenttina siitä mitä repossa pitäisi olla, riippumatta työkalusta joka sen ajoi.

**Periaate:** rakenne ensin, verifioitavana — ei käsin kopioitu tiedosto kerrallaan eri istunnoista.

## 2. Pre-flight ennen ensimmäistä committia

Ennen `git init`iä ajettiin kaksi deterministista tarkistusta: `grep -ri admicom .` (nolla osumaa — ei asiakasnimien vuotoa demoon) ja `python3 tests/test_gate.py` (KAIKKI: OK, neljä tapausta). Vasta näiden jälkeen initial commit ja push julkiseen repoon.

**Periaate:** julkaisu on portin takana, ei oletusarvo.

## 3. Runtime-verifiointi — ensimmäinen este oli ympäristö, ei koodi

`claude --plugin-dir .`-ajo epäonnistui heti: `ModuleNotFoundError: No module named 'mcp'`. Diagnoosi: `files.pythonhosted.org` resolvasi `0.0.0.0`:aan — paikallinen **AdGuard Home** (DNS-tason mainos-/seurantasuodatin) esti CDN-hostin, vaikka `pypi.org` ja `github.com` toimivat normaalisti. Tämä ei ollut Claude Coden sandboxin este eikä koodin bugi — varmistettu kokeilemalla `dangerouslyDisableSandbox`, joka ei muuttanut mitään, ja tarkistamalla `nameserver 127.0.0.1` + AdGuard Home -paneeli suoraan. Käyttäjä salli domainin AdGuard Homessa, minkä jälkeen `pip install "mcp>=1.27,<2"` venviin onnistui.

**Periaate:** kun jokin epäonnistuu, diagnosoi juurisyy ennen korjausta — älä arvaa PEP 668:aa kun oikea syy on DNS-taso, äläkä oleta oman sandboxin vikaa kun se on koko koneen verkkokerroksessa.

## 4. Kriittinen löydös: plugin-nimi etuliittää MCP-työkalut

README:ssä oli tietoisesti liputettu avoin oletus: *"pluginin nimi ei dokumentaation perusteella etuliitä palvelimen nimeä, mutta tämä kannattaa vahvistaa `/mcp`-komennolla."* Live-ajo paljasti oletuksen vääräksi — todellinen nimi on `mcp__plugin_invoice-guard_invoice-erp__*`, ei `mcp__invoice-erp__*`. Tämä rikkoi kaksi eri tiedostoa samalla juurisyyllä:

1. **`hooks/hooks.json`:n matcher ei osunut** → PreToolUse-hook ei koskaan lauennut. Kaikki kirjoitukset (myös INV-003:n injektioyritys) olisivat menneet läpi täysin ilman gatea, jos tätä ei olisi huomattu. Korjattu: `mcp__.*write_vat_treatment`.
2. **`agents/invoice-inspector.md`:n `tools:`-kenttä osoitti samaan väärään nimeen** → subagentilla ei ollut pääsyä `get_invoice`iin.

**Periaate:** dokumentoitu epävarmuus ("kannattaa vahvistaa") on parempi kuin väärä varmuus — se johti oikeaan testiin sen sijaan että olisi jätetty huomiotta.

## 5. Subagentin hallusinaatio — löydös, ei vain bugi

Kun `tools:`-kenttä osoitti väärään työkalunimeen, `invoice-inspector`-subagentti ei ilmoittanut virheestä. Se **keksi laskun tiedot**: INV-001:n myyjäksi raportoitiin "Rakennus Nordic Oy" ja ostajaksi "Kiinteistö Helsinki Oy" — täysin eri nimet kuin `mock_data.py`:n oikeat "RT-Laatta Oy" ja "Rakennusliike Mäkelä Oy". Tämä on täsmälleen se käytös jota koko projekti vastustaa: agentti arvasi sen sijaan että olisi kieltäytynyt.

Korjauksen jälkeen sama testi ajettiin uudestaan livenä. Subagentti kutsui nyt oikeaa työkalua (`mcp__plugin_invoice-guard_invoice-erp__get_invoice`, näkyy suoraan trace-lokissa) ja tuotti täsmälleen `mock_data.py`:n mukaisen datan jokaiselle kolmelle laskulle — ei "OK"-ilmoitusta vaan rivi riviltä täsmäävä sisältö, mikä oli tietoinen vaatimus ennen kuin korjaus hyväksyttiin todistetuksi.

**Mutta huomaa mikä ei koskaan vaarantunut:** vaikka subagentti hallusinoi väärän myyjänimen raporttiinsa, itse ALV-**kirjauspäätöstä** ei koskaan tehty subagentin väitteiden perusteella. `write_vat_treatment`in edessä oleva PreToolUse-hook laskee oikean vastauksen aina uudelleen `mock_data.py`:n ground truthista — ei agentin tekstistä, ei subagentin raportista. Väärä myyjänimi näkyvässä yhteenvedossa ei siis olisi voinut johtaa vääreään ALV-kirjaukseen, koska poiminta (mitä agentti *sanoo*) ja päätös (mitä gate *laskee*) ovat arkkitehtonisesti erotettu toisistaan.

**Periaate:** tämä on arkkitehtuurin ydinväite todistettuna elävän bugin kautta, ei vain väitettynä — juuri sellainen tapaus jota ei voi suunnitella etukäteen, vain löytää verifioimalla oikeasti.

## 6. Todistustason rehellinen kalibrointi

Ei kaikkea voitu todistaa samalla tasolla samalla ajolla:

| Case | Todistustaso |
|---|---|
| PASS (INV-001) | Täysin live — malli erehtyi ensin, hook korjasi, malli oppi |
| BLOCK / ground-truth-ristiriita | Täysin live (sivutuotteena) |
| BLOCK / injektio (INV-003) | Täysin live — hook pysäytti riippumatta mallin omasta arviosta |
| ESCALATE (INV-002) | Vain simuloitu suoralla payloadilla — malli kieltäytyi jo promptitasolla eikä koskaan yrittänyt oikeaa kirjoitusta |
| Subagentti | Täysin live, toisella yrityksellä korjauksen jälkeen |

**Periaate:** "kaikki todistettu" on laiskempi ja vähemmän luotettava väite kuin eritelty taulukko siitä mikä todistui miten. Tämä sama taulukko on README:ssä käyttäjille asti.

---

## Uudelleenkäytettävä malli tästä projektista

1. **Rakenna deterministisesti.** Skripti joka luo rakenteen on parempi dokumentti kuin proosakuvaus.
2. **Pre-flight ennen julkaisua.** Nolla-osumat + vihreät testit ovat portti, ei muodollisuus.
3. **Diagnosoi juurisyy ennen korjausta**, varsinkin kun ensimmäinen este on ympäristö eikä koodi.
4. **Liputettu epävarmuus dokumentaatiossa on arvokas** — se ohjaa oikeaan testiin sen sijaan että jäisi huomaamatta.
5. **Live-verifiointi löytää sen mitä koodin lukeminen ei löydä** — molemmat kriittiset bugit tässä projektissa olivat sellaisia että staattinen tarkastelu (JSON validi, testit vihreät) ei olisi koskaan paljastanut niitä.
6. **Kalibroi todistustaso rehellisesti per tapaus.** "Todistettu" ja "simuloitu" eivät ole sama asia, vaikka molemmat päätyisivät samaan lopputulokseen.

Tämä on se artefaktityyppi jota AI-native-tuotekehitystiimi tuottaa: ei vain toimiva demo, vaan rehellinen kertomus siitä miten se todettiin toimivaksi — mukaan lukien mitä ei toteta ilman lisätyötä.
