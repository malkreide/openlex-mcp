# SessionStart-Hook: Klon-Aktualität

`session-start.sh` meldet beim Sessionstart, wie viele Commits der
ausgecheckte Stand hinter `origin/<Default-Branch>` liegt. Registriert ist er
in `.claude/settings.json`.

## Warum

Ein veralteter Klon hat am 3.8.2026 **zweimal** eine rote CI erzeugt, deren
Ursache nicht im Diff stand: Die fehlenden Commits waren jeweils genau die,
die das Gate einführten, an dem der Branch scheiterte. Wer nur den Diff liest,
sucht den Fehler in den falschen Dateien — der Diff ist ja in Ordnung, der
Baum darunter nicht.

Die Prüfung kostet eine Sekunde und ersetzt diese Fehlersuche. Sie ist die
maschinelle Fassung des ersten Absatzes von `CLAUDE.md` («Vor der Arbeit»).

## Was er garantiert

1. **Er blockiert die Session nie.** Kein Netz, kein Remote, detached HEAD,
   flatterndes DNS, kein `git` im `PATH` — jeder dieser Fälle geht still
   durch, Exit-Code 0. Das ist die wichtigste Eigenschaft: Ein Hook, der bei
   Netzproblemen die Arbeit anhält, wird nach dem zweiten Mal abgeschaltet und
   schützt danach gar nichts.
2. **Kurzes Timeout.** Jeder Netzaufruf läuft unter `timeout` (Vorgabe 5 s,
   über `CLAUDE_STALENESS_TIMEOUT` einstellbar); zwei Aufrufe, also höchstens
   ~10 s im schlimmsten Fall, plus 20 s Backstop in `settings.json`.
   Zusätzlich sind Gits interaktive Abfragen abgeschaltet
   (`GIT_TERMINAL_PROMPT=0`, `ssh -oBatchMode=yes`) — ein Credential-Prompt
   wartet sonst die volle Timeout-Zeit bei *jedem* Sessionstart.
3. **Bei 0 schweigt er.** Ausgabe nur, wenn wirklich Commits fehlen.
4. **Der Default-Branch wird ermittelt, nicht angenommen.**
   `git ls-remote --symref origin HEAD`, mit dem lokalen `origin/HEAD` als
   netzfreier Rückfallebene. Dieses Repo heisst seinen Default-Branch
   `master` (wie auch `swiss-courts-mcp` und `swisstopo-mcp`) — die Annahme
   `main` scheitert hier mit «couldn't find remote ref main», was wie ein
   Netzproblem aussieht, und hat schon einmal einen Branch 15 Commits alt
   werden lassen.

## Prüfen

`tests/test_session_start_hook.py` fährt den Hook gegen echte Git-Repos in
`tmp_path` mit `file://`-Remote — kein Netz, und damit auch im Unit-Lauf
(`-m "not live"`) zulässig.

```bash
PYTHONPATH=src pytest tests/test_session_start_hook.py -v
```

Von Hand, im Klon selbst:

```bash
CLAUDE_PROJECT_DIR="$PWD" .claude/hooks/session-start.sh; echo "exit=$?"
```
