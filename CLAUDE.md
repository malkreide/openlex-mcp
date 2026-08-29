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

**Ein 4xx ist kein Nein.** Am 29.8.2026 antwortete `past-publications` in
`swiss-procurement-mcp` auf jede Publikation mit Losen mit HTTP 400. Daraus war
geschlossen worden, die Quelle verweigere diese Auskunft; der Befund stand
datiert im Fixture-Nachweis, ein Test bestätigte ihn, alles blieb grün. Die
Spec desselben Endpunkts führt einen als *optional* deklarierten Parameter
`lotId` — für Publikationen mit Losen ist er Pflicht. Mit ihm antwortet
dieselbe Publikation mit 200. Ein Projekt trug sieben Vorgängerpublikationen,
die der Server als «Quelle nicht erreichbar» wegwarf.

Drei Handgriffe daraus:

- **Die Parameterliste der Spec durchgehen, bevor ein Statuscode eingeordnet
  wird.** «Optional» heisst dort oft «optional für die Mehrheit».
- **Einer deterministischen Absage keinen Wiederholungsrat geben.** «Nicht
  erreichbar, bitte später erneut» ist bei einem 400 falsch und liest sich für
  das Modell wie eine Störung. Den Status mitführen und den fehlenden
  Parameter benennen — den Status, nicht den Antwortkörper.
- **Beide Antworten aufzeichnen, mit und ohne den Parameter.** Eine
  Aufzeichnung nur des Fehlschlags kann nicht zeigen, dass er vermeidbar war;
  dass nur der 400er aufgezeichnet war, ist der Grund, warum der falsche
  Befund nicht auffiel.

**Und ein 403 ist gar keine Auskunft.** Am 29.8.2026 sollten für 42 Repos die
Dependabot-Labels nachgemessen werden. Alle 13 Abfragen des ersten Stapels
kamen zurück als:

```
Failed to find label: API rate limit already exceeded for user ID 8864492.
```

Der gefährliche Teil steht vorn: Das Werkzeug verpackt eine Sperre als
Fund-Fehlschlag. Wer die Zeile überfliegt oder nur auf ein leeres Ergebnis
prüft, zählt 39 Repos als «Label fehlt» und hat seine eigene Erschöpfung
gemessen. Das Limit hängt am Konto, nicht am Repo — derselbe Vormittag hatte
es mit 42 eröffneten und 42 gemergten PRs verbraucht.

Das ist der Absatz darüber, andersherum gelesen: dort war ein 400 eine echte,
wiederholbare Antwort und galt als Störung; hier ist eine Störung als Antwort
verpackt. Entscheidend ist nie der Statuscode, sondern ob die Quelle überhaupt
geantwortet hat.

- **Positivkontrolle im selben Repo.** Ein «nicht gefunden» wird erst dadurch
  zur Messung, dass eine gleichzeitige Abfrage etwas findet.
- **Die Messung entlang der Sperre teilen.** `raw.githubusercontent.com` ist
  ein CDN und nicht die REST-API. Um 11:19:27 UTC lieferte es für
  `register-mcp` HTTP 200, während die Label-Abfrage desselben Repos in
  derselben Minute die Sperre meldete. Alle 42 `dependabot.yml` kamen so
  durch, während die Label-Hälfte stand.
- **Am Token vorbei geht es nicht.** Beide Umwege enden am Agent-Proxy, und
  jeder mit einer eigenen irreführenden Begründung. `api.github.com` ohne
  Zugangsdaten:

  ```
  GitHub access is not enabled for this session. An org admin must connect
  the Claude GitHub App for this organization.
  ```

  Das ist keine Aussage über die Organisation, sondern das, was ohne Token
  kommt. Wer ihr folgt, sucht einen Admin für ein Problem, das keiner hat.
  Die HTML-Seite `github.com/<owner>/<repo>/labels` fällt ebenfalls, aber
  anders:

  ```
  This GitHub API path is not available: sessions are bound to their
  configured repositories. Use repository-scoped endpoints
  (repos/{owner}/{repo}/...).
  ```

  Der Proxy behandelt also auch `github.com` als API-Pfad; die zweite Meldung
  klingt nach einem Scope-Problem und ist doch nur dieselbe Sackgasse. Den
  Token aus der Umgebung in einen curl-Header zu setzen, blockiert der
  Klassifikator. Ob es überhaupt hülfe, ist offen: die Sperre nennt ein
  Nutzerkonto, und ob der Token zu diesem gehört, wurde nie geprüft.
- **Die Sperre gilt nicht dem Dienst, sondern dem Zugangspfad.** Unmittelbar
  nachdem eine Abfrage der Checks eines PR sauber durchlief, meldete die
  Label-Abfrage weiter die Sperre. Von einem blockierten Werkzeug also nicht
  auf «GitHub ist zu» schliessen — und umgekehrt eine gelungene Abfrage nicht
  als Entwarnung für die gesperrte nehmen. Das ist dieselbe Asymmetrie wie
  bei der verschwundenen Codex-Meldung weiter unten.

Wann die Sperre fällt, geben diese Beobachtungen nicht her. Die Meldung nennt
keinen Zeitpunkt, und die `X-RateLimit`-Kopfzeilen sind hinter dem Proxy nicht
zu sehen. Belegt sind drei gesperrte Zeitpunkte — 11:14, 11:16 und 11:19 UTC.
Wer daraus eine Dauer macht, hat sie erfunden.

**Dieselbe Falle bei einer Konfigurationsoption: die Vorgabe lesen, bevor man
einen Schlüssel für wirkungslos hält.** Am 29.8.2026 fielen die
`labels:`-Zeilen aus den `dependabot.yml` des Portfolios, begründet mit
«Dependabot legt Labels nicht an». Eine Messung danach zeigte, dass
`dependencies` in 36 von 42 Repos sehr wohl existiert, 35 davon mit GitHubs
Standardbeschreibung. Das las sich zuerst wie ein Beleg, dass die Aktion
falsch war.

Die Optionsreferenz kehrt es um:

```
Dependabot creates these default labels automatically, as necessary in
your repository.

The labels specified are used instead of the default labels.
```

Ohne `labels:` vergibt Dependabot also `dependencies` plus ein Ökosystem-Label
und legt beide selbst an; eine eigene Liste **ersetzt** diesen Satz, und «if
any of these labels is not defined in the repository, it is ignored». Die
Zeile war nicht wirkungslos — sie tauschte einen sich selbst pflegenden
Vorgabesatz gegen eine starre Liste.

Was das kostet, ist an `openlex-mcp` gemessen: zwei Ökosysteme deklariert,
also stünden `dependencies` **und** ein Ökosystem-Label zu; vorhanden ist nur
das erste, `github-actions` und `github_actions` fehlen beide (Kontrolle `bug`
vorhanden). `register-mcp` ist die Gegenprobe: dort existieren alle vier
deklarierten Namen mit handgeschriebener Beschreibung, die Liste ist gewollt
und vollständig.

**Dreimal falsch eingeordnet, in drei Richtungen.** Erst die Zeile für bloss
wirkungslos gehalten. Dann die gefundenen Labels für einen Widerspruch. Dann,
auf denselben Fund gestützt, einen richtigen PR geschlossen mit dem Argument,
das Label existiere ja — obwohl es existiert, *weil* die Vorgabe es anlegt.
Der dritte Fehler ist der teuerste, weil er wie eine Messung aussah.

Was die Messung **nicht** hergibt: wer die 36 Labels angelegt hat. Die
Referenz sagt, Dependabot tue es; die Objekt-IDs liegen aber so dicht
beieinander, dass sie eher aus einem Stapellauf stammen. Beides passt zum
Befund, keines ist belegt — die Herkunft blieb ungemessen.

Beim Aufräumen gilt deshalb dieselbe Frage wie bei `lotId`: Was ist die
*Vorgabe*, wenn man das Ding weglässt — nicht bloss, ob der aktuelle Wert
etwas bewirkt.

**`results[0]` ist nur so verlässlich wie die Zusicherung danach.** Pinnt die
Abfrage einen bekannten Datensatz, ist der erste Treffer eine Drift-Wache und
in Ordnung. Hängt die Zusicherung dagegen davon ab, *welche* Variante die
Quelle heute zuoberst hat, prüft der Test den Tag: am 25.8.2026 rot, weil die
neueste Zürcher Publikation zufällig Lose hatte, am 26.8. grün, ohne dass sich
etwas geändert hätte. Den Fall gezielt wählen und beide Zweige fahren.

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
  die Meldung und in keinem die Reaktion. Dieser Befund hat sich am 29.8. nicht
  gehalten — was am Ende des Abschnitts gemessen ist, erklärt ihn anders.
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
Review-Objekt, eine Befundlos-Meldung **oder** einen Statuskommentar auf
`✅ Completed` — der Zustand gehört zur Bedingung, nicht bloss die Form: derselbe
Kommentar steht direkt nach dem Umschalten auf `🔄 Running` und belegt dann
nichts als den Start. Wer nur das Objekt gelten lässt, zählt jeden befundlosen
Review als ungeprüft — und baut sich denselben Fehlalarm ein, den dieser
Abschnitt verhindern soll, nur in die andere Richtung.

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
Befundlos-, die Kontingent-, die Environment-Meldung **oder** den
Statuskommentar sein — vier gegensätzliche Bedeutungen unter derselben Zahl, und
die letzte wechselt ihre eigene noch, während sie dasteht. Den Text lesen, nicht
die Zahl. Und einen unbekannten Text wörtlich zitieren, statt ihn in eine der
bekannten Schubladen zu zwingen: Dieser Abschnitt musste schon zweimal wachsen —
erst von drei auf vier Gründe, dann um die Form unten —, und die 👍-Reaktion
stand hier zwei Fassungen lang als Tatsache.

**Es gibt eine fünfte Form, und sie ist die einzige, die den Lauf selbst
datiert.** Am 29.8.2026 wurde in diesem Repo PR #77 von Draft auf ready
gestellt. Um 12:20:56.72Z begann daraufhin ein Lauf, und um 12:21:00Z stand
darunter ein gewöhnlicher Issue-Kommentar von `chatgpt-codex-connector[bot]`,
erkennbar am verborgenen Marker `<!-- codex-pull-request-review-summary -->`:

```
## Codex Review Summary

| Review         | Status                       | Commit    | Review trigger     |
| -------------- | ---------------------------- | --------- | ------------------ |
| 📝 Code Review | 🔄 Running since 12:20:56.72Z | `8273d03` | Draft marked ready |
```

Um 12:22:28.07Z wurde derselbe Kommentar **an Ort und Stelle** überschrieben:
aus `🔄 Running` wurde `✅ Completed`. `get_reviews` blieb dabei `[]`, und eine
Befundlos-Meldung kam nie.

Nach der Regel, wie sie hier bis heute stand, wäre dieser PR damit **ungeprüft**
gewesen — es gab weder ein Review-Objekt noch eine Befundlos-Meldung. Gelaufen
ist der Review trotzdem, mit Zeitstempel, Commit und Auslöser. Die Regel hätte
also in genau die Richtung geirrt, vor der sie warnt, nur einen Schritt weiter.

Drei Dinge, die man dabei auseinanderhalten muss:

- **Der Statuskommentar belegt den Lauf, nicht das Urteil.** `✅ Completed` heisst
  «fertig», nicht «sauber». Ob es Befunde gab, sagt weiterhin allein, ob ein
  Review-Objekt dasteht. Wer sein Häkchen an das grüne Symbol hängt, hängt es an
  die falsche Aussage.
- **Er wird überschrieben, nicht ergänzt.** Dieselbe Kommentar-ID bedeutete
  binnen anderthalb Minuten erst «läuft» und dann «fertig». Was man vorhin
  gelesen hat, ist deshalb kein Befund, sondern ein Zwischenstand — vor dem
  Urteil neu abfragen.
- **Er ersetzt das Review-Objekt nicht.** Am selben Tag lief #79 mit Befund: da
  standen Statuskommentar **und** Review-Objekt nebeneinander. Der Kommentar
  kam bei beiden Läufen, das Objekt nur beim Lauf mit Befund. Beide Abfragen
  bleiben also nötig, der Kommentar erspart keine.
- **Zwei Läufe sind noch keine Regel.** Belegt ist die Form für ein Repo, zwei
  PRs, einen Tag. Ob jedes Repo sie bekommt, ist offen; ihr Fehlen ist vorerst
  kein Gegenbeweis, und ein Repo ohne sie fällt zurück auf die vier Fälle oben.

Der Infokasten wurde derweil umgeschrieben und verspricht zwei Reaktionen:
👀 während des Laufs, 👍 nach einem Lauf ohne Befund. Beide Hälften sind am
29.8. gemessen worden, und beide stimmen:

| PR  | Lauf                | `reactions` am PR                  |
| --- | ------------------- | ---------------------------------- |
| #79 | während des Laufs   | `eyes: 1`                          |
| #79 | fertig, mit Befund  | `total_count: 0` — 👀 wieder weg    |
| #77 | fertig, ohne Befund | `+1: 1`                            |

Damit ist der Kasten in diesem Punkt **bestätigt**, nicht bloss unwiderlegt.
Wichtig daran ist das mittlere Feld: **die 👀 wird nach dem Lauf wieder
entfernt.** Eine Reaktion, die man nicht findet, kann deshalb dreierlei heissen
— es lief nie etwas, es lief und fand etwas, oder man hat zu spät gesehen.

**Und sie sitzt am PR, nicht am Statuskommentar.** Daran bin ich selbst
hängengeblieben: `reactions` am Kommentar liefert immer `total_count: 0`, und
das sieht aus wie ein Ausbleiben. Es ist aber keine Messung des Versprechens,
sondern eine am falschen Objekt — und stand deshalb zwei Stunden lang falsch in
der Beschreibung von #77. Beides zusammen erklärt die sechs Repos vom 23.8.
zwanglos: am Kommentar gemessen oder nach einem Lauf mit Befund gesehen, und
schon fehlt die Reaktion, ohne dass jemand sein Versprechen gebrochen hätte.
Der Satz «der Kasten ist keine Quelle» stützt sich damit auf eine Messung, die
ihn nicht mehr trägt.

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
python scripts/check_dependabot_labels.py     # braucht GH_TOKEN, siehe unten
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

### Ein Label, das nur in der Konfiguration existiert

`dependabot.yml` verlangt unter `labels:` ein Label. Fehlt es im Repo, legt
Dependabot es **nicht** an — es kommentiert an jedem erzeugten PR:

```
The following labels could not be found: `dependencies`.
```

Der PR entsteht trotzdem, die CI bleibt grün, und die Meldung sieht aus wie
Rauschen. Am 28.8.2026 verlangten 24 Repos des Portfolios zusammen 50 Labels,
und **alle 50 fehlten** — einzeln mit `get_label` nachgemessen, mit drei
Positivkontrollen (`bug`, `enhancement`, `documentation` lieferten echte
Objekte, «not found» war also eine Messung und kein Werkzeugartefakt).
Aufgefallen ist es an einem Bot-Kommentar unter einem Dependabot-PR.

`scripts/check_dependabot_labels.py` macht daraus ein Gate: es liest die eigene
`dependabot.yml`, holt die Labels des Repos über die API und fällt, wenn eines
fehlt. Der Standard-`GITHUB_TOKEN` genügt; der Job braucht dafür `issues: read`,
deshalb steht in `ci.yml` jetzt ein `permissions:`-Block.

**Ohne Token wird nichts still grün.** In der CI (`CI` gesetzt) ist ein
fehlender Token ein Fehler. Ein Überspringen sähe in der Ausgabe genauso aus wie
ein Erfolg — das wäre wieder der Schnappschuss, den niemand vergleicht.
`tests/test_dependabot_labels.py` hält beide Richtungen fest, dazu die
Extraktion: Block- und Inline-Form, und der Abbruch an der Einrückung. Ohne den
läse der Parser über die Blockgrenze hinaus und meldete
`package-ecosystem: "github-actions"` als fehlendes Label — ein dauerhaft rotes
Gate, das jemand abschaltet.

Der Check ist bewusst Standardbibliothek und ohne YAML-Parser, damit er zwischen
den Repos kopierbar bleibt (fünf fahren ihre CI auch auf 3.10). Die Extraktion
ist gegen alle 31 echten `dependabot.yml` des Portfolios gegengeprüft.

Wo Labels fehlen, legt `labels-sync.py` sie an — es leitet sie aus jeder
`dependabot.yml` ab, statt eine Liste zu pflegen, die still veraltet.

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

Und nur dort — `[project.optional-dependencies].dev` sagt `ruff==0.16.4`, die
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
