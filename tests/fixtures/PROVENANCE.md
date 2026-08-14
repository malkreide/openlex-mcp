# Herkunft der Fixtures

**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**

Aufgezeichnet am **2026-08-14**.

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

## Gemessen: die Live-Metadaten

`zhlaw_get_law_metadata` fragt `zh.ch` ab. Am 2026-08-08 war der
Host aus der Aufzeichnungsumgebung nicht erreichbar und blieb
ungemessen; `live_metadata.json` schliesst diese Luecke.

Aufgezeichnet ist der **Seitentitel**, denn das ist der Teil, der
still kaputtgeht. Im Portfolio hiess «nicht gefunden» schon einmal
nicht, dass der Datensatz weg war, sondern dass die Quelle die
Schreibweise ihrer Kopfzeile gewechselt hatte — vier von sechs
Datensaetzen produktiv kaputt, alle Unit-Tests gruen.

Gemessen wird ueber `api_client.fetch_zhlex_metadata`, also mit dem
IP-Pinning und der Egress-Sperre des Servers. Wer den Rekorder
hinter einem HTTPS-Proxy laufen laesst, sieht hier `Connection
reset`: Der Proxy weist die IP-Literal-URL ab. Das ist eine Grenze
der Aufzeichnungsumgebung, keine Aussage ueber die Quelle.

## `bestand_stand.json`

- **Quelle:** `https://huggingface.co/api/datasets/rcds/swiss_legislation + lokaler Cache`
- **Aufgezeichnet:** 2026-08-14
- **Auswahl:** der Stand des Bestands, nicht der des Caches: juengste Fassung, Aenderungsdatum des Datensatzes und die Verteilung von `is_active`. Die letzte Zahl ist ein Nullbefund und steht deshalb hier — ohne sie wird beim naechsten Mal erneut ein Fehler vermutet, wo die Quelle schlicht nur gueltige Erlasse fuehrt
- **Groesse:** 420 B
- **SHA-256:** `883a553aa302ca22897f6cf5ccff80c2d76863b945f723eecb61e1fa8eda4a7a`

## `live_hosts_dns.json`

- **Quelle:** `https://cloudflare-dns.com/dns-query`
- **Aufgezeichnet:** 2026-08-14
- **Auswahl:** die Hosts der Live-Metadaten ueber oeffentliches DNS-over-HTTPS, samt einer NXDOMAIN-Kontrolle. Bewusst NICHT ueber den eigenen Netzpfad: Aus der Aufzeichnungsumgebung waren zh.ch und zhlex.zh.ch nicht erreichbar, und daraus folgt nichts ueber die Quelle. Eine Zustellgrenze der eigenen Umgebung ist keine Aussage ueber den Bestand — dieser Unterschied ist im Portfolio schon mehrfach verwechselt worden
- **Groesse:** 824 B
- **SHA-256:** `80dd17ba402972e5444181fcd31544e16d5d81cf5eb54d7ea61dd0607bdcea40`

## `live_metadata.json`

- **Quelle:** `https://www.zhlex.zh.ch/... (Ordnr=412.100)`
- **Aufgezeichnet:** 2026-08-14
- **Auswahl:** die Antwort von `zhlaw_get_law_metadata` ueber den Netzpfad des Servers, samt Seitentitel. Der Titel ist der Teil, der still kaputtgeht: Im Portfolio hiess «nicht gefunden» schon einmal nicht, dass der Datensatz weg war, sondern dass die Quelle die Schreibweise ihrer Kopfzeile gewechselt hatte
- **Groesse:** 299 B
- **SHA-256:** `247bc149a96c0bd2aa7071e2545ed6c16461615edfdce5ba5ed23c89ca3936af`
