"""Unit-Tests für den SessionStart-Hook `.claude/hooks/session-start.sh`.

Der Hook meldet, wie viele Commits der ausgecheckte Stand hinter
``origin/<Default-Branch>`` liegt. Seine wichtigste Eigenschaft ist nicht die
Meldung, sondern dass er die Session **nie** blockiert: Ein Hook, der bei
Netzproblemen anhält, wird abgeschaltet und schützt danach gar nichts. Die
Tests hier fahren ihn deshalb vor allem gegen kaputte Lagen.

Gearbeitet wird mit echten Git-Repos in ``tmp_path`` und ``file://``-Remotes —
kein Netz, damit im Unit-Lauf zulässig. Der einzige Socket ist ein
Loopback-Listener, der absichtlich nie antwortet; er hält die Timeout-Zusage
fest, die sich ohne hängende Gegenstelle nicht widerlegen lässt.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "session-start.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or shutil.which("timeout") is None,
    reason="git und timeout werden gebraucht; ohne sie schweigt der Hook per Bauart",
)


def _git(repo: Path, *args: str) -> str:
    """Ruft git in ``repo`` mit fester Identität auf und gibt stdout zurück."""
    fertig = subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "protocol.file.allow=always",
            *args,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert fertig.returncode == 0, f"git {args} scheiterte:\n{fertig.stderr}"
    return fertig.stdout


def _commit(repo: Path, text: str) -> None:
    (repo / "datei.txt").write_text(text, encoding="utf-8")
    _git(repo, "add", "datei.txt")
    _git(repo, "commit", "-m", text)


def _hook(projekt: Path, timeout_s: str = "5", subprocess_timeout: float = 60.0):
    """Fährt den Hook über ``projekt`` und gibt (returncode, stdout, sekunden)."""
    start = time.monotonic()
    fertig = subprocess.run(
        ["bash", str(HOOK)],
        cwd=str(projekt),
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": str(projekt),
            "CLAUDE_PROJECT_DIR": str(projekt),
            "CLAUDE_STALENESS_TIMEOUT": timeout_s,
        },
        capture_output=True,
        text=True,
        timeout=subprocess_timeout,
    )
    return fertig.returncode, fertig.stdout, time.monotonic() - start


@pytest.fixture
def welt(tmp_path):
    """Baut ein Origin, einen Klon und einen zweiten Klon zum Vorausschieben.

    Der Default-Branch heisst absichtlich **nicht** ``main``: Genau die Annahme
    ``main`` ist der Fehler, den dieser Hook nicht machen darf.
    """

    def bauen(default_branch: str = "master"):
        # Branch-Namen duerfen Schraegstriche enthalten, Verzeichnisnamen hier nicht.
        kurz = default_branch.replace("/", "-")
        origin = tmp_path / f"origin-{kurz}.git"
        origin.mkdir()
        _git(origin, "init", "--bare", "-b", default_branch, ".")

        seed = tmp_path / f"seed-{kurz}"
        seed.mkdir()
        _git(seed, "clone", f"file://{origin}", ".")
        _commit(seed, "erster Commit")
        _git(seed, "push", "origin", f"HEAD:{default_branch}")

        klon = tmp_path / f"klon-{kurz}"
        klon.mkdir()
        _git(klon, "clone", f"file://{origin}", ".")
        return origin, seed, klon

    return bauen


def _vorausschieben(seed: Path, default_branch: str, anzahl: int) -> None:
    for i in range(anzahl):
        _commit(seed, f"neuer Commit {i}")
    _git(seed, "push", "origin", f"HEAD:{default_branch}")


# ---------------------------------------------------------------------------
# Er meldet, wenn Commits fehlen — und nur dann
# ---------------------------------------------------------------------------


def test_meldet_die_zahl_der_fehlenden_commits(welt):
    _origin, seed, klon = welt("master")
    _vorausschieben(seed, "master", 2)

    code, out, _ = _hook(klon)

    assert code == 0
    nutzlast = json.loads(out)
    text = nutzlast["hookSpecificOutput"]["additionalContext"]
    assert "2 Commits" in text
    assert "origin/master" in text


def test_bei_null_fehlenden_commits_schweigt_er(welt):
    _origin, _seed, klon = welt("master")

    code, out, _ = _hook(klon)

    assert code == 0
    assert out == "", f"Der Hook hat geredet, obwohl nichts fehlt: {out!r}"


def test_ein_einzelner_commit_wird_im_singular_gemeldet(welt):
    _origin, seed, klon = welt("master")
    _vorausschieben(seed, "master", 1)

    _code, out, _ = _hook(klon)

    text = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "1 Commit hinter" in text


def test_die_ausgabe_ist_gueltiges_json_fuer_den_hook_kanal(welt):
    _origin, seed, klon = welt("master")
    _vorausschieben(seed, "master", 3)

    _code, out, _ = _hook(klon)

    nutzlast = json.loads(out)
    assert nutzlast["hookSpecificOutput"]["hookEventName"] == "SessionStart"


# ---------------------------------------------------------------------------
# Der Default-Branch wird ermittelt, nicht angenommen
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("default_branch", ["master", "trunk", "haupt/zweig"])
def test_der_default_branch_wird_ermittelt_nicht_geraten(welt, default_branch):
    """Fällt, sobald jemand ``main`` (oder sonst einen Namen) fest verdrahtet.

    ``master`` ist der Fall dieses Repos, ``trunk`` und ``haupt/zweig`` zeigen,
    dass auch eine zweite fest verdrahtete Annahme auffliegt.
    """
    _origin, seed, klon = welt(default_branch)
    _vorausschieben(seed, default_branch, 2)

    code, out, _ = _hook(klon)

    assert code == 0
    text = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert f"origin/{default_branch}" in text
    assert "2 Commits" in text


# ---------------------------------------------------------------------------
# Er blockiert nie — die kaputten Lagen
# ---------------------------------------------------------------------------


def test_kein_git_repo_geht_still_durch(tmp_path):
    kein_repo = tmp_path / "kein-repo"
    kein_repo.mkdir()

    code, out, _ = _hook(kein_repo)

    assert code == 0
    assert out == ""


def test_repo_ohne_remote_geht_still_durch(tmp_path):
    allein = tmp_path / "allein"
    allein.mkdir()
    _git(allein, "init", "-b", "master", ".")
    _commit(allein, "einziger Commit")

    code, out, _ = _hook(allein)

    assert code == 0
    assert out == ""


def test_repo_ohne_jeden_commit_geht_still_durch(tmp_path):
    leer = tmp_path / "leer"
    leer.mkdir()
    _git(leer, "init", "-b", "master", ".")

    code, out, _ = _hook(leer)

    assert code == 0
    assert out == ""


def test_unerreichbares_remote_geht_still_durch(welt):
    """Kein Netz, kaputte URL, geloeschtes Origin — alles derselbe Fall."""
    _origin, _seed, klon = welt("master")
    _git(klon, "remote", "set-url", "origin", "file:///gibt/es/nicht/origin.git")

    code, out, _ = _hook(klon)

    assert code == 0
    assert out == ""


def test_detached_head_wird_gemeldet_und_blockiert_nicht(welt):
    """Detached HEAD ist kein Fehlerfall: HEAD ist dort ein Commit wie jeder andere."""
    _origin, seed, klon = welt("master")
    _vorausschieben(seed, "master", 2)
    sha = _git(klon, "rev-parse", "HEAD").strip()
    _git(klon, "checkout", "--detach", sha)

    code, out, _ = _hook(klon)

    assert code == 0
    text = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "2 Commits" in text


def test_ein_haengendes_remote_laeuft_ins_timeout_statt_die_session_anzuhalten(welt):
    """Die Zusage «kurzes Timeout» braucht eine Gegenstelle, die wirklich haengt.

    Ein Listener auf Loopback nimmt die TCP-Verbindung an und antwortet nie.
    ``git`` wartet darauf ohne eigenes Zeitlimit — ohne ``timeout`` im Hook
    kaeme dieser Aufruf nie zurueck, und der Sessionstart haenge mit ihm. Der
    ``subprocess``-Timeout unten laesst genau das als Testfehler auflaufen
    statt als haengenden Lauf.
    """
    _origin, _seed, klon = welt("master")

    lauscher = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lauscher.bind(("127.0.0.1", 0))
    lauscher.listen(8)  # annehmen, aber nie accept()en: die Verbindung steht, nichts kommt
    port = lauscher.getsockname()[1]
    try:
        _git(klon, "remote", "set-url", "origin", f"git://127.0.0.1:{port}/repo.git")

        code, out, dauer = _hook(klon, timeout_s="2", subprocess_timeout=30.0)
    finally:
        lauscher.close()

    assert code == 0
    assert out == ""
    assert dauer < 15.0, f"Der Hook hielt {dauer:.1f}s an — das ist kein kurzes Timeout"
