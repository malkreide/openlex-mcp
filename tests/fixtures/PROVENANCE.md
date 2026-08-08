# Herkunft der Fixtures

**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**

Aufgezeichnet am **2026-08-08**.

Ohne Datum ist «gemessen» nach zwei Jahren von «angenommen» nicht mehr
zu unterscheiden — die Datei sieht gleich aus.

## Aufgezeichnet ist der Stand des Bestands

Dieser Server liefert aus einem lokalen Cache, und der Cache gilt 24
Stunden. Der **Bestand** darin ist Jahre alt: Die juengste Fassung
traegt `version_active_since = 2023-01-01`. `provenance="cache"` sagt,
woher eine Antwort kam — nicht, wie alt die Gesetze darin sind. Genau
diese beiden Fragen wurden verwechselt.

Der Nullbefund gehoert dazu: Alle Eintraege sind `is_active = True`,
keiner traegt ein `version_inactive_since`. Das ist kein Fehler des
Servers, sondern die Form der Quelle — sie fuehrt nur gueltige
Erlasse. Ohne diese Zeile wird beim naechsten Durchgang erneut ein
Fehler vermutet, wo keiner ist.

## NICHT gemessen: die Live-Metadaten

`zhlaw_get_law_metadata` fragt `www.zh.ch` ab. Aus der
Aufzeichnungsumgebung war der Host nicht erreichbar. **Daraus folgt
nichts.** Das oeffentliche DNS fuehrt ihn (NOERROR, 194.247.8.174),
und die NXDOMAIN-Kontrolle zeigt, dass die Abfrage unterscheidet — die
Grenze liegt also bei der Aufzeichnungsumgebung, nicht bei der Quelle.

Der entsprechende Live-Test ist deshalb **nicht** angepasst worden.
Ein Test, den man rot sieht, weil die eigene Umgebung nicht
hinauskommt, gehoert nicht umgeschrieben — sonst misst er danach die
Umgebung statt die Quelle.

## `bestand_stand.json`

- **Quelle:** `https://huggingface.co/api/datasets/rcds/swiss_legislation + lokaler Cache`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** der Stand des Bestands, nicht der des Caches: juengste Fassung, Aenderungsdatum des Datensatzes und die Verteilung von `is_active`. Die letzte Zahl ist ein Nullbefund und steht deshalb hier — ohne sie wird beim naechsten Mal erneut ein Fehler vermutet, wo die Quelle schlicht nur gueltige Erlasse fuehrt
- **Groesse:** 420 B
- **SHA-256:** `0d2011791393c5da0b5356db19d3320faf4f9602cc15345be04269dd0557490c`

## `live_hosts_dns.json`

- **Quelle:** `https://cloudflare-dns.com/dns-query`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** die Hosts der Live-Metadaten ueber oeffentliches DNS-over-HTTPS, samt einer NXDOMAIN-Kontrolle. Bewusst NICHT ueber den eigenen Netzpfad: Aus der Aufzeichnungsumgebung waren zh.ch und zhlex.zh.ch nicht erreichbar, und daraus folgt nichts ueber die Quelle. Eine Zustellgrenze der eigenen Umgebung ist keine Aussage ueber den Bestand — dieser Unterschied ist im Portfolio schon mehrfach verwechselt worden
- **Groesse:** 824 B
- **SHA-256:** `e5dc3aef838475c6766d3a76409a566c2c823ff83c4ed5aa71c4addd8c809ba1`
