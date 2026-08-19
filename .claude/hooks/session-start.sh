#!/usr/bin/env bash
#
# SessionStart-Hook: meldet, wie viele Commits der ausgecheckte Stand hinter
# origin/<Default-Branch> liegt.
#
# WARUM
# -----
# Ein veralteter Klon hat am 3.8.2026 zweimal eine rote CI erzeugt, deren
# Ursache nicht im Diff stand: Die fehlenden Commits waren jeweils genau die,
# die das Gate einfuehrten, an dem der Branch scheiterte. Die Fehlersuche lief
# dadurch in den falschen Dateien. Diese Pruefung kostet eine Sekunde und
# ersetzt sie.
#
# ERSTE REGEL: DIESER HOOK BLOCKIERT DIE SESSION NIE.
# Kein Netz, kein Remote, detached HEAD, flatterndes DNS, kaputtes Git — jeder
# dieser Faelle geht still durch. Deshalb:
#   * kein `set -e` (ein einzelnes fehlgeschlagenes Kommando darf nicht toeten),
#   * jeder Netzaufruf unter `timeout`,
#   * jede Interaktivitaet von Git abgeschaltet (ein Credential-Prompt haengt
#     laenger als jedes Timeout),
#   * `exit 0` als letzte Zeile, ohne Ausnahme.
# Ein Hook, der bei Netzproblemen die Arbeit anhaelt, wird nach dem zweiten Mal
# abgeschaltet und schuetzt danach gar nichts.
#
# ZWEITE REGEL: BEI 0 SCHWEIGT ER. Ausgabe nur, wenn wirklich Commits fehlen.

# Sekunden pro Netzaufruf (ls-remote und fetch je einzeln).
readonly TIMEOUT_SEKUNDEN="${CLAUDE_STALENESS_TIMEOUT:-5}"

still_durch() { exit 0; }

haupt() {
  cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || return

  # Git muss da sein, ein Arbeitsbaum muss da sein, HEAD muss auf einen Commit
  # zeigen (frisch initialisiertes Repo ohne Commit: unborn branch).
  command -v git >/dev/null 2>&1 || return
  command -v timeout >/dev/null 2>&1 || return
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return
  git rev-parse --verify --quiet HEAD >/dev/null 2>&1 || return
  git remote get-url origin >/dev/null 2>&1 || return

  # Nichts darf nach einer Eingabe fragen. Ein Prompt auf Passwort oder
  # Host-Key wartet, bis jemand tippt — `timeout` faengt das zwar ab, aber
  # erst nach der vollen Wartezeit bei jedem Sessionstart.
  export GIT_TERMINAL_PROMPT=0
  export GIT_ASKPASS=/bin/true
  export SSH_ASKPASS=/bin/true
  export GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=accept-new"

  # Default-Branch ERMITTELN, nicht raten. `main` anzunehmen ist genau der
  # Fehler, der hier schon einmal einen Branch 15 Commits alt werden liess:
  # openlex-mcp, swiss-courts-mcp und swisstopo-mcp heissen ihren
  # Default-Branch `master`, und `git fetch origin main` scheitert dort mit
  # «couldn't find remote ref main» — was wie ein Netzproblem aussieht.
  local branch
  branch="$(
    timeout "$TIMEOUT_SEKUNDEN" git ls-remote --symref origin HEAD 2>/dev/null |
      sed -n 's|^ref: refs/heads/\([^[:space:]]*\).*|\1|p' | head -n 1
  )"

  # Kein Netz? Dann fragt der naechste Versuch das lokale origin/HEAD, das beim
  # Klonen gesetzt wurde. Kein Netzzugriff, kann aber veraltet sein — als
  # Rueckfallebene besser als aufzugeben.
  if [ -z "$branch" ]; then
    branch="$(
      git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null |
        sed 's|^origin/||'
    )"
  fi
  [ -n "$branch" ] || return

  # Ein Branch-Name darf Anfuehrungszeichen und Backslashes enthalten; beides
  # zerlegt die JSON-Ausgabe unten. Was nicht in diese Zeichenklasse passt,
  # wird verworfen statt escaped.
  case "$branch" in
    *[!A-Za-z0-9._/-]*) return ;;
  esac

  timeout "$TIMEOUT_SEKUNDEN" git fetch --quiet origin "$branch" 2>/dev/null || return

  # Funktioniert auch bei detached HEAD — HEAD ist dort ein Commit wie jeder
  # andere, nur ohne Branch-Namen.
  local dahinter
  dahinter="$(git rev-list --count HEAD..FETCH_HEAD 2>/dev/null)" || return
  case "$dahinter" in
    '' | *[!0-9]*) return ;;
  esac
  [ "$dahinter" -gt 0 ] || return

  local commit_wort="Commits"
  [ "$dahinter" -eq 1 ] && commit_wort="Commit"

  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
    "Klon-Aktualitaet: Der ausgecheckte Stand liegt $dahinter $commit_wort hinter origin/$branch. \
Vor der Arbeit den Default-Branch einholen (git merge origin/$branch bzw. rebase) — sonst laeuft \
die CI gegen Gates, die im lokalen Baum noch fehlen, und der Fehler steht nicht im Diff."
}

haupt
still_durch
