# CLAUDE.md

## Teil 1 — Portfolio-Konventionen

### Vor der Arbeit

Klon-Aktualität prüfen — Standard-Branch ermitteln, nicht `main` annehmen:

```bash
B=$(git ls-remote --symref origin HEAD | sed -n 's|^ref: refs/heads/\([^[:space:]]*\).*|\1|p')
git fetch origin "${B:?Standard-Branch nicht ermittelbar}" &&
  git rev-list --count HEAD..FETCH_HEAD
```

Drei Server im Portfolio heissen ihren Standard-Branch `master`
(`openlex-mcp`, `swiss-courts-mcp`, `swisstopo-mcp`); dort scheitert ein fest
verdrahtetes `origin/main` mit «couldn't find remote ref main». Wer das für ein
Netzproblem hält, arbeitet weiter auf genau dem veralteten Klon, vor dem dieser
Absatz warnt. Den `:?`-Schutz nicht weglassen: Bei leerem `B` fetcht git still
den Remote-HEAD und endet mit 0.

Ein veralteter Klon erzeugt eine rote CI, deren Ursache nicht im Diff steht.
Am 3.8.2026 zweimal passiert — beide Male fehlten genau die Commits, die
das Gate einführten, an dem der Branch scheiterte.

Gates lokal fahren, mit der GEPINNTEN ruff-Version aus der CI. Eine andere
Version meldet Abweichungen, die niemand verursacht hat.

### Tests

Gegenprobe ist Pflicht. Ein Test, der grün bleibt, wenn man die
Implementierung entfernt, prüft nichts. Jede neue Zusicherung einzeln
neutralisieren und zeigen, dass genau die zugehörigen Tests fallen.

Zwei Fallen, die beide grün blieben:

- Eine Fake-Uhr, die nur beim Schlafen vorrückt, kann eine Zusicherung über
  echte Zeit nicht widerlegen.
- `monkeypatch.setattr(modul.asyncio, "sleep", ...)` greift ins Modul
  `asyncio` selbst und entschärft die Mechanik im ganzen Prozess. Patche
  einen Modul-Alias (`_sleep = asyncio.sleep`), nicht das fremde Modul.

Handgeschriebene Fixtures kodieren die Annahme des Autors und können sie
nicht widerlegen. Mindestens eine aufgezeichnete Antwort pro externem
Endpunkt, mit Aufnahmedatum.

### Wenn etwas rot ist

Roter Live-Test: erst die Quelle abfragen, dann einordnen. Nicht aus der
Fehlermeldung schliessen. Am 3.8.2026 hiess «nicht gefunden» nicht, dass der
Datensatz weg war, sondern dass die Quelle die Schreibweise ihrer Kopfzeile
gewechselt hatte — vier von sechs Datensätzen produktiv kaputt, alle
Unit-Tests grün.

PR ohne jeden Check ist selten ein Repo ohne CI, meistens ein
Merge-Konflikt: GitHub berechnet dafür keinen Merge-Commit und startet nichts.

Ein Codex-Review auf einem PR wird beantwortet oder behoben, nie ignoriert.

### Wenn Codex gar nicht erst hinsieht

Die Zeile oben unterstellt, dass es einen Befund geben *kann*. Das ist nicht
immer so, und man sieht es dem PR nicht an.

Am 21.8.2026 war das Code-Review-Kontingent zwischen 08:41 und 09:48
aufgebraucht — davor echte Reviews, danach in 30 Repos nur noch:

```
You have reached your Codex usage limits for code reviews.
```

Wie lange die Sperre dauerte, geben die Beobachtungen nur als Spanne her. Vier
Zeitpunkte sind belegt: letzter gelungener Review am 21.8. um 08:41, erste
Limit-Meldung um 09:48, letzte beobachtete Limit-Meldung am 22.8. um 11:03,
erste *andere* Meldung am 23.8. um 08:22.

Zwischen erster und letzter Limit-Meldung liegen **25 h 15 min**. Das ist der
Abstand zweier Fehlschläge, nicht die Dauer einer Sperre. Wer ihn Untergrenze
nennt, hat die durchgehende Erschöpfung schon vorausgesetzt, die er belegen
soll: Öffnete sich das Fenster zwischendurch und schloss es sich durch neue
Auslöser wieder, waren es zwei kurze Sperren und nie eine von 25 Stunden.
Untergrenze einer *einzelnen* Sperre sind die 25 h 15 min nur unter genau dieser
Annahme — und die ist unbelegt.

Nach oben trägt die Rechnung dagegen. Die längste mit den Beobachtungen
verträgliche Sperre reicht vom letzten Erfolg um 08:41 bis zur abweichenden
Meldung um 08:22, also **47 h 41 min**; länger kann keine einzelne gewesen sein.
Wer stattdessen ab der ersten Limit-Meldung rechnet, unterschlägt die 67
Minuten, in denen das Kontingent schon weg gewesen sein kann, und nennt die
Spanne zwischen zwei Beobachtungen eine Obergrenze.

Beobachtungspunkte sind keine Messreihe — die 21 Stunden vor der abweichenden
Meldung liefen ganz ohne Codex-Auslöser, dort hat niemand gemessen.

In der Zwischenzeit sind 32 PRs mit formal erfülltem Häkchen gemergt worden,
ohne dass jemand hineingesehen hat, und am 22.8. noch einmal 43.

**Vier** Gründe, warum Codex schweigt, und nur einer davon ist harmlos:

- **Kein Befund** — dann schreibt er einen gewöhnlichen Issue-Kommentar:

  ```
  Codex Review: Didn't find any major issues. Swish!
  ```

  Der Schlusssatz wechselt bei jedem Lauf («Delightful!», «Keep it up!»,
  «More of your lovely PRs please.»); stabil ist nur der Satz davor. Der
  Infokasten, den Codex unter jeden Review setzt, behauptet weiterhin eine
  Reaktion («otherwise it will react with 👍») — am 23.8. kam in sechs Repos
  die Meldung und in keinem die Reaktion. Der Kasten ist keine Quelle.
- **Der PR ist ein Draft** — darauf läuft Codex nicht an.
- **Das Kontingent ist weg** — dann schreibt er die Meldung oben.
- **Für das Repo fehlt eine Environment** — dann schreibt er:

  ```
  To use Codex here, create an environment for this repo.
  ```

Der vierte kam erst zum Vorschein, als der dritte wegfiel, und das ist kein
Zufall: Die Prüfungen liegen hintereinander. Dass es diese Reihenfolge ist und
nicht die umgekehrte, lässt sich an einem einzigen Repo ablesen — in
`swiss-public-data-mcp` bekam PR #54 am 22.8. um 10:56:55 die Kontingent-Meldung
und PR #56 am 23.8. um 08:22:20 die Environment-Meldung. Läge die
Environment-Prüfung vorn, hätte #54 sie schon am Vortag gesehen; die Environment
fehlte ja bereits. Zwei Meldungen aus demselben Repo schlagen hier jede
Vermutung über die Reihenfolge.

Praktisch heisst das: **Eine verschwundene Limit-Meldung ist keine Entwarnung.**
Sie kann bedeuten, dass das Kontingent wieder da ist — und dass jetzt etwas
anderes den Review verhindert. Belegt ist eine Prüfung erst durch ein
Review-Objekt **oder** eine Befundlos-Meldung. Wer nur das Objekt gelten lässt,
zählt jeden befundlosen Review als ungeprüft — und baut sich denselben Fehlalarm
ein, den dieser Abschnitt verhindern soll, nur in die andere Richtung.

«Kein Kommentar» heisst also nicht «geprüft und sauber». Unterscheiden lässt es
sich an der Form: Ein Review **mit** Befund ist ein Review-Objekt
(«💡 Codex Review», mit Commit-Angabe); ein Review **ohne** Befund und die
beiden Ausfallmeldungen — Kontingent wie Environment — sind gewöhnliche
Issue-Kommentare und trennen sich nur im Text. Beim Draft gibt es überhaupt
nichts, weil Codex nicht anläuft; ein kommentarloser Draft ist deshalb kein
Beleg, sondern ein nicht durchgeführter Test.

Das sind verschiedene Abfragen — `get_reviews` fürs Objekt, `get_comments` für
alles andere; wer nur eine nimmt, übersieht den Rest. Genau so ist die
Limit-Meldung zuerst durchgerutscht.

Der Kommentarzähler allein reicht ohnehin nicht: `comments: 1` kann die
Befundlos-, die Kontingent- **oder** die Environment-Meldung sein — drei
gegensätzliche Bedeutungen unter derselben Zahl. Den Text lesen, nicht die Zahl.
Und einen unbekannten vierten Text wörtlich zitieren, statt ihn in eine der
bekannten Schubladen zu zwingen: Dieser Abschnitt musste schon einmal von drei
auf vier Gründe wachsen, und die 👍-Reaktion stand hier zwei Fassungen lang als
Tatsache.

Und ein befundloser Lauf ist kein Freispruch. Am 23.8. lief derselbe Text durch
42 Reviews: 36 meldeten denselben P2-Befund, 6 die Befundlos-Meldung — gleiche
Eingabe, gegenteiliges Urteil, alles in denselben neun Minuten. Ein sauberer
Lauf sagt damit etwas über den Lauf, nicht über den Text. Wer sein Häkchen
daran hängt, hängt es an einen Münzwurf.

Portfolio-weit nachsehen:

```
search_pull_requests: user:malkreide commenter:chatgpt-codex-connector[bot] updated:>=<Datum>
```

Findet nur, wo er *kommentiert* hat. Repos ohne PR-Aktivität tauchen nicht auf
— das ist kein Beleg, dass dort geprüft wurde.

Zweiter Weg, den Prüfer zu verlieren, ganz ohne Kontingentproblem: zu schnell
mergen. Am 21./22.8. lagen zwischen «ready for review» und Merge mehrfach drei
bis fünf Sekunden. Codex wird beim Umschalten von Draft auf ready ausgelöst und
braucht danach Zeit; wer sofort mergt, hat das Häkchen gesetzt und den Review
nicht abgewartet.

Das Kontingent hängt am Konto, nicht am Repo, und Code-Reviews haben einen
eigenen Topf — nur GitHub-getriggerte Reviews zählen hinein. ChatGPT-Pläne
fahren ein rollendes Fünf-Stunden-Fenster plus Wochenlimits; welches greift,
steht im Codex-Dashboard. Welches hier griff, ist **offen**. Die Lücke oben
schliesst das Fünf-Stunden-Fenster nicht aus: Es kann sich zwischendurch
geöffnet und durch neue Auslöser wieder erschöpft haben. Das auszuschliessen
bräuchte den Nachweis, dass in der ganzen Spanne kein einziger Review durchlief
— den gibt es nicht, weil nur Fehlschläge beobachtet wurden. Eine lange Reihe
von Fehlschlägen belegt eine lange Reihe von Fehlschlägen, nicht ihre Ursache.

Zeigt das Dashboard freies Kontingent, während Reviews weiter scheitern, ist
das ein bekannter Fehler bei mehreren verbundenen Konten — dann den
GitHub-Connector in den Codex-Einstellungen trennen und neu verbinden.

Die Environment legt man unter `chatgpt.com/codex/cloud/settings/environments`
an, und zwar **je Repo**. Die Meldung sagt es selbst («for this repo»), und am
23.8. war es genau so: In `swiss-public-data-mcp` fehlte sie, dort kam kein
Review; in den übrigen Repos lief Codex am selben Morgen durch. Eine
Environment fürs Konto genügt also nicht — wer eine anlegt und den Rest für
erledigt hält, mergt weiter Ungeprüftes.

### Wenn zwei Agenten dasselbe tun

Vor dem Anlegen eines Branches mit vorgegebenem Namen prüfen, ob es ihn schon
gibt:

```bash
git ls-remote --heads origin claude/<name> | wc -l
```

Steht dort `1`, arbeitet jemand anderes daran — mit Schreibrecht auf denselben
Ref.

Ein PR mit leerem Diff wird geschlossen, nicht gemergt. Der Test ist
`get_files` auf dem PR: kommt `[]` zurück, ändert er nichts. Ein grüner Check
sagt dazu nichts — die CI prüft den Head, nicht die Differenz zur Basis.

Am 21.8.2026 liefen zwei Sessions dieselbe Aufgabe über 45 Repos, auf den
Branches `claude/codex-review-audit-templates-9sn6mx` und
`claude/codex-review-audit-7ioh56`. Wo die eine zuerst nach `main` kam, wurde
`main` in den Branch der anderen gemergt und der add/add-Konflikt zugunsten
von `main` aufgelöst. Übrig blieben 14 PRs, die durch sämtliche Gates grün
liefen und nichts enthielten; sie wurden gemergt und hinterliessen leere
Merge-Commits. Mit den zwei Folge-PRs, die aus demselben Grund gegenstandslos
waren, waren 16 der 59 PRs jenes Tages reine Reibung.

Dieselbe Klasse wie der handgeschriebene Stub, der denselben Feldnamen annahm
wie der Code: Nichts ist rot, weil nichts geprüft wird, worauf es ankommt.

## Teil 2 — Dieses Repo

Default-Branch ist `master` (CI triggert auf `[main, master]`). Der Befehl
oben lautet hier `git fetch origin master && git rev-list --count HEAD..origin/master`.

### Gates, wörtlich aus `.github/workflows/ci.yml`

```
pip install -e ".[dev]"                       # enthält den ruff-Pin, siehe unten
PYTHONPATH=src pytest tests/ -m "not live"
python scripts/check_ruff_pin.py
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
python scripts/check_version_sync.py
```

Matrix: Python 3.11 / 3.12 / 3.13; alle Gates laufen auf allen drei Feldern,
keine `if:`-Ausnahme. Ein `fail-fast: false` steht nicht da.

**SEC-022 ist jetzt ein Gate.** `tests/test_tool_hashes.py` vergleicht
`docs/tool-hashes.json` mit den aktuellen Definitionen; die Suite läuft in der
CI, also fällt ein vergessenes Nachziehen auf. `scripts/gen_tool_hashes.py`
kann beides: `--check` (Standard) und `--write` nach einer gewollten Änderung.

Der Absatz stand hier zwei Tage lang anders — «eine Konvention, kein Gate», und
das traf zu. Was er beschrieb, ist genau eingetreten: Der Schnappschuss war acht
Hashes weit veraltet, ohne dass ein Lauf rot wurde. Die Ursache lag nicht bei
jemandem, der das Nachziehen vergessen hat, sondern in der Hash-Eingabe — das
alte Skript las `mcp._tool_manager._tools` und hashte dort `parameters`. Über
die öffentliche Liste heisst dasselbe Feld `input_schema`; es sind zwei
verschiedene Objekte. Die 2.x-Migration baute die Interna um, und damit
änderten sich alle acht Hashes, obwohl seit der letzten Erzeugung kein einziger
Commit `server.py` angefasst hatte.

Die Nutzlast steht deshalb auf den Wire-Namen `inputSchema`/`outputSchema` —
gebunden an das, was Clients über das Protokoll sehen, nicht an die
SDK-Schreibweise. Dieselbe Lösung fährt `bag-health-mcp`, dort als CI-Schritt
statt als Test.

### Live-Tests

Geplanter Workflow vorhanden: `.github/workflows/live.yml`, cron `0 4 * * *`
(04:00 UTC) plus `workflow_dispatch`, Befehl `PYTHONPATH=src pytest -m live -v`.
DRIFT-005 ist damit erfüllt — Live-Tests sind nicht bloss per `-m "not live"`
ausgeschlossen. Fixture-Provenienz: `tests/fixtures/PROVENANCE.md`,
zuletzt aufgezeichnet 2026-08-14, erzeugt von `scripts/record_fixtures.py`.

**Den Rekorder ohne Proxy-Variablen laufen lassen.** Der Server verbindet auf
die gepinnte IP, ein HTTPS-Proxy weist die IP-Literal-URL mit `Connection
reset` ab. Dasselbe lässt `pytest -m live` den Metadaten-Test überspringen —
das ist eine Grenze der Umgebung, kein Fehler der Quelle und keiner im Code.

### Der Unit-Lauf geht nicht ans Netz

Zwei autouse-Fixtures, beide ausser Kraft bei `@pytest.mark.live`:

- `_kein_datensatz_download_im_unit_lauf` sperrt `datasets.load_dataset`.
  Wer den Datensatz braucht, markiert den Cache per `mark_fresh()` als frisch
  oder stubbt den Aufruf.
- `_kein_netz_im_unit_lauf` sperrt `getaddrinfo` **und** `socket.connect` —
  eins allein reicht nicht, eine gepinnte IP-Verbindung umgeht die Auflösung.
  Loopback bleibt erlaubt, `test_transport_security` braucht es.

Beide werfen eine `BaseException`: `load_from_huggingface` fängt jeden
`Exception`, `fetch_zhlex_metadata` jeden `httpx.HTTPError`. Ein gewöhnlicher
Fehler verschwände dort, und der Test bliebe grün.

`_kein_netz_im_unit_lauf` löscht ausserdem die Proxy-Variablen. Ohne das war
die Sperre wirkungslos: Der Proxy dieser Umgebung sitzt auf `127.0.0.1`, also
auf Loopback, und der Verkehr verliess den Rechner trotzdem.

### Der ruff-Pin steht in `pyproject.toml`

Und nur dort — `[project.optional-dependencies].dev` sagt `ruff==0.16.3`, die
CI installiert ihn über `pip install -e ".[dev]"` mit. Keinen zweiten Pin in
einen Workflow schreiben: Vorher stand `ruff==0.16.1` allein in `ci.yml`,
während `pyproject.toml` `ruff>=0.4.0` sagte — eine frische venv zog damit
0.16.3, die CI überschrieb sie mit 0.16.1. `tests/test_toolchain_pin.py` lässt
beide Hälften dieser Drift auflaufen. Bump gehört in einen eigenen Commit,
samt der Formatierungen, die er auslöst.

`.pre-commit-config.yaml` existiert nicht.

Vor dem Lauf `ruff --version` prüfen: ein älteres ruff früher im `PATH`
schlägt den Pin, ohne dass der Install etwas meldet.

### Backoff in Tests

Die autouse-Fixture `_no_backoff` in `tests/conftest.py` nullt die Wartezeit
über den Alias `api_client._sleep`. Einzeltests patchen das **nicht** noch
einmal selbst.

Drei Tests in `tests/test_retry_policy.py` halten sie fest, jeder gegen eine
andere Art, sie kaputtzumachen:

- `test_die_fixture_nullt_die_wartezeit` — wirkt sie überhaupt? Fällt, sobald
  sie entfernt oder wirkungslos wird.
- `test_der_erschoepfte_retry_pfad_kostet_keine_echte_zeit` — wirkt sie dort,
  wo der Code wirklich schläft? Drei Versuche schlafen real ≥ 1.5 s.
- `test_die_fixture_laesst_das_echte_asyncio_sleep_in_ruhe` — trifft sie den
  Alias und nicht `asyncio.sleep` selbst?

Gemessen wird an der Wanduhr (`time.monotonic`), weil nur sie diese Aussagen
widerlegen kann. Den Jitter dabei **nicht** festnageln: `api_client.random`
ist das stdlib-Modul, ein Patch darauf wirkt prozessweit — dieselbe Falle wie
bei `asyncio.sleep`. Die Schranken hängen deshalb an der garantierten
Untergrenze der Leiter, die unabhängig vom Zufall gilt.
