# Hardening (release 1.0, batch 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The app never dies silently, never runs twice, never refuses to start over a bad config, and tells the user which version it is.

**Architecture:** Three small new modules (`version.py`, `applog.py`, `single_instance.py`) with no Qt widgets in them, wired into `overlay.main()`. `load_config()` learns to recover from a missing or corrupt `config.json`. The About page shows the version and a link to GitHub Releases. The PyInstaller build stamps the version into the exe.

**Tech Stack:** Python 3.11+, PySide6 (`QLocalServer` / `QLocalSocket` for single instance), stdlib `logging.handlers.RotatingFileHandler`, PyInstaller `--version-file`, pytest.

**Spec:** `.scratch/release-1.0/spec.md`, section "Batch 1: hardening" (items 1 to 4).

## Global Constraints

- Version string is exactly `1.0.0`, in one place (`version.py`), everything else reads it.
- Log file: `<data folder>/az-overlay.log`, rotating. Data folder is `overlay._BASE` (repo folder from source, `%APPDATA%\az-overlay` when frozen).
- No network call at startup. "Check for updates" only opens a browser.
- Second launch raises the running instance's settings window and exits with code 0.
- Corrupt `config.json` is copied to `config.json.bak` next to it, then defaults are used and the app keeps running. A missing `config.json` is a first run, not an error.
- UI copy says "layout", never "profile" (see `CONTEXT.md`).
- Commit messages: short imperative sentence, no prefix tag, matching `git log` (for example "Undo the last pad deletion"), followed by a blank line and `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Run the whole suite with `python -m pytest -q` (baseline: 153 pass, about 95 s). Run single files while iterating.
- `python` on this machine is Python 3.14 at `C:\Python314\python.exe` and has PySide6. Use it, not `py -3.11`.

---

## File Structure

| File | Responsibility |
| :--- | :--- |
| `version.py` (new) | `__version__ = "1.0.0"`. Nothing else. Imported by the app and by the build. |
| `applog.py` (new) | `setup(log_dir) -> str` (installs rotating file logging, returns the log path) and `install_excepthook()` (routes uncaught exceptions to the log). No Qt. |
| `single_instance.py` (new) | `SingleInstance(QObject)`: `acquire() -> bool`, `activate_requested` Signal. Owns a `QLocalServer`. |
| `make_version.py` (new) | Writes `build/version_info.txt` (PyInstaller VSVersionInfo) from `version.__version__`. |
| `overlay.py` | `load_config()` recovers from missing or corrupt config; `main()` wires logging, single instance, recovery balloon, `app.setApplicationVersion`. |
| `settings_ui.py` | About page: version line and "Check for updates" button. |
| `build.bat` | Runs `make_version.py`, passes `--version-file`. |
| `README.md` | Troubleshooting section: log path, `config.json.bak`, second launch behaviour. |
| `tests/test_applog.py`, `tests/test_single_instance.py`, `tests/test_overlay.py`, `tests/test_settings_ui.py` | Tests for the above. |

---

### Task 1: Version constant, About page, exe metadata

**Files:**
- Create: `version.py`
- Create: `make_version.py`
- Modify: `settings_ui.py:26-33` (constants) and `settings_ui.py:1517-1531` (`_about_page`)
- Modify: `overlay.py:1393-1400` (`main`, add `setApplicationVersion`)
- Modify: `build.bat`
- Test: `tests/test_settings_ui.py`

**Interfaces:**
- Produces: `version.__version__: str` (`"1.0.0"`); `settings_ui.RELEASES_URL: str`; `SettingsWindow._open_releases()`.
- Later tasks log `__version__` at startup (Task 2).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_settings_ui.py`:

```python
# ---- release 1.0: version ------------------------------------------------------
def test_about_page_shows_the_version_and_a_releases_link(editor, monkeypatch):
    import version
    about = editor.stack.widget(editor.PAGES.index("About"))
    text = " ".join(lbl.text() for lbl in about.findChildren(settings_ui.QLabel))
    assert f"Version {version.__version__}" in text
    button = next(b for b in about.findChildren(settings_ui.QPushButton) if b.text() == "Check for updates")
    opened = []
    monkeypatch.setattr(settings_ui.QDesktopServices, "openUrl", lambda url: opened.append(url.toString()) or True)
    button.click()
    assert opened == [settings_ui.RELEASES_URL]
    assert settings_ui.RELEASES_URL.startswith("https://github.com/")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_settings_ui.py::test_about_page_shows_the_version_and_a_releases_link -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'version'`

- [ ] **Step 3: Create `version.py`**

```python
"""The one place the app version lives. Read by the app, the About page, and the build."""

__version__ = "1.0.0"
```

- [ ] **Step 4: Add the constant and the About page widgets**

In `settings_ui.py`, after line 33 (`VENMO_DONATION_URL = ...`) add:

```python
RELEASES_URL = "https://github.com/andypc93/az-overlay/releases"
```

Add `from version import __version__` to the imports (after `import templates`, line 17).

In `_about_page`, replace the `overview` card block (lines 1518-1523) with:

```python
        overview, overview_layout = card()
        overview_layout.addWidget(section(APP_NAME))
        overview_layout.addWidget(muted(
            "A customizable input overlay for Azeron keypads, keyboards, and controllers. "
            "Show your inputs as you play with a transparent, click-through overlay "
            "and live layout editing."))
        overview_layout.addWidget(muted(f"Version {__version__}"))
        updates = QPushButton("Check for updates")
        updates.setCursor(Qt.CursorShape.PointingHandCursor)
        updates.setToolTip("Open the releases page in your browser")
        updates.clicked.connect(self._open_releases)
        updates_row = QHBoxLayout()
        updates_row.addWidget(updates)
        updates_row.addStretch(1)
        overview_layout.addLayout(updates_row)
```

After `_open_donation` (line 1550-1554) add:

```python
    def _open_releases(self):
        if not QDesktopServices.openUrl(QUrl(RELEASES_URL)):
            QMessageBox.information(
                self, "Check for updates",
                f"Could not open your browser. Visit this link to see releases:\n{RELEASES_URL}")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_settings_ui.py::test_about_page_shows_the_version_and_a_releases_link -q`
Expected: PASS

- [ ] **Step 6: Tell Qt the version**

In `overlay.py`, add `from version import __version__` after `from gamepad import Gamepad, is_gamepad_input` (line 28). In `main()`, after `app.setApplicationName(APP_NAME)` add:

```python
    app.setApplicationVersion(__version__)
```

- [ ] **Step 7: Create `make_version.py`**

```python
"""Write build/version_info.txt so PyInstaller stamps the exe with the app version
(visible in Explorer under Properties > Details)."""

import os

from version import __version__

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "version_info.txt")

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({tuple}),
    prodvers=({tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Andres Perez'),
        StringStruct('FileDescription', 'AZ-Overlay input overlay'),
        StringStruct('FileVersion', '{version}'),
        StringStruct('InternalName', 'AZ-Overlay'),
        StringStruct('LegalCopyright', 'Copyright 2026 Andres Perez. MIT License.'),
        StringStruct('OriginalFilename', 'AZ-Overlay.exe'),
        StringStruct('ProductName', 'AZ-Overlay'),
        StringStruct('ProductVersion', '{version}')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def version_tuple(version):
    parts = [int(p) for p in version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    return ", ".join(str(p) for p in parts[:4])


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(tuple=version_tuple(__version__), version=__version__))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Update `build.bat`**

Replace the whole file with:

```bat
@echo off
python make_icon.py
python make_version.py
python -m PyInstaller --noconfirm --onefile --noconsole --name AZ-Overlay --icon assets\icon.ico ^
  --version-file build\version_info.txt ^
  --add-data "config.json;." --add-data "profiles;profiles" --add-data "assets;assets" ^
  --hidden-import pygame._sdl2.controller overlay.py
echo Built dist\AZ-Overlay.exe  (settings live in %%APPDATA%%\az-overlay, untouched by rebuilds)
```

- [ ] **Step 9: Check the generator output parses**

Run: `python make_version.py && python -c "exec(open('build/version_info.txt').read()) if False else print(open('build/version_info.txt').read()[:60])"`
Expected: prints `wrote ...build\version_info.txt` then `VSVersionInfo(` on the first line. `build/` is gitignored, nothing to commit from it.

- [ ] **Step 10: Run the settings suite**

Run: `python -m pytest tests/test_settings_ui.py -q`
Expected: all pass (56 tests).

- [ ] **Step 11: Commit**

```bash
git add version.py make_version.py settings_ui.py overlay.py build.bat tests/test_settings_ui.py
git commit -m "Version 1.0.0 on the About page and in the exe metadata

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Crash log

**Files:**
- Create: `applog.py`
- Test: `tests/test_applog.py`

**Interfaces:**
- Produces: `applog.setup(log_dir: str) -> str` (returns full log path, safe to call twice), `applog.install_excepthook() -> None`, `applog.LOG_NAME = "az-overlay.log"`.
- Consumed by Task 5 (`main()` calls both before anything else).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_applog.py`:

```python
"""Logging goes to a rotating file in the data folder; uncaught exceptions land there too."""

import logging
import sys

import applog


def test_setup_creates_the_log_file_and_returns_its_path(tmp_path):
    path = applog.setup(str(tmp_path))
    logging.getLogger("az").info("hello from the test")
    for h in logging.getLogger().handlers:
        h.flush()
    assert path == str(tmp_path / applog.LOG_NAME)
    assert "hello from the test" in (tmp_path / applog.LOG_NAME).read_text(encoding="utf-8")


def test_setup_twice_does_not_duplicate_handlers(tmp_path):
    applog.setup(str(tmp_path))
    applog.setup(str(tmp_path))
    file_handlers = [h for h in logging.getLogger().handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1


def test_excepthook_writes_the_traceback_and_chains(tmp_path, monkeypatch):
    applog.setup(str(tmp_path))
    seen = []
    monkeypatch.setattr(sys, "excepthook", lambda *args: seen.append(args))
    applog.install_excepthook()
    try:
        raise RuntimeError("boom for the log")
    except RuntimeError:
        sys.excepthook(*sys.exc_info())
    for h in logging.getLogger().handlers:
        h.flush()
    text = (tmp_path / applog.LOG_NAME).read_text(encoding="utf-8")
    assert "Unhandled exception" in text
    assert "RuntimeError: boom for the log" in text
    assert len(seen) == 1  # the previous hook still runs (stderr output when not frozen)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_applog.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'applog'`

- [ ] **Step 3: Create `applog.py`**

```python
"""File logging for the app. One rotating file in the user data folder, so a crash
on a stranger's machine leaves something to read. No Qt in here: it must work
before QApplication exists."""

import logging
import logging.handlers
import os
import sys

LOG_NAME = "az-overlay.log"
_MAX_BYTES = 512 * 1024
_BACKUPS = 2
_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"

_log = logging.getLogger("az")


def setup(log_dir):
    """Install a rotating file handler on the root logger. Returns the log path.
    Calling it again re-points the handler (tests) instead of adding another."""
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, LOG_NAME)
    root = logging.getLogger()
    for h in list(root.handlers):
        if getattr(h, "_az_log", False):
            root.removeHandler(h)
            h.close()
    handler = logging.handlers.RotatingFileHandler(
        path, maxBytes=_MAX_BYTES, backupCount=_BACKUPS, encoding="utf-8")
    handler.setFormatter(logging.Formatter(_FORMAT))
    handler._az_log = True
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    return path


def install_excepthook():
    """Log uncaught exceptions with their traceback, then hand off to whatever
    hook was there (the default prints to stderr, which the exe has none of)."""
    previous = sys.excepthook

    def hook(exc_type, exc, tb):
        _log.critical("Unhandled exception", exc_info=(exc_type, exc, tb))
        for h in logging.getLogger().handlers:
            h.flush()
        previous(exc_type, exc, tb)

    sys.excepthook = hook
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_applog.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add applog.py tests/test_applog.py
git commit -m "Rotating log file and an excepthook that writes crashes to it

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Recover from a missing or corrupt config.json

**Files:**
- Modify: `overlay.py:329-337` (`load_config`, the `open`/`json.load` at the top)
- Test: `tests/test_overlay.py`

**Interfaces:**
- Produces: `overlay.load_config()` never raises for a missing, unreadable, or non-object `config.json`. Module global `overlay.RECOVERED_CONFIG_BACKUP: str | None` holds the `.bak` path when the last `load_config()` had to back a corrupt file up, else `None`. `overlay.CONFIG_BACKUP_SUFFIX = ".bak"`.
- Consumed by Task 5 (`main()` shows a balloon when `RECOVERED_CONFIG_BACKUP` is set).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_overlay.py`:

```python
# ---- release 1.0: config recovery -------------------------------------------------
def _isolate_config(tmp_path, monkeypatch):
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path / "profiles"))


def test_missing_config_is_a_first_run_not_an_error(tmp_path, monkeypatch):
    _isolate_config(tmp_path, monkeypatch)
    cfg = overlay.load_config()
    assert cfg["theme"] == "dark"
    assert cfg["hotkeys"]["toggle"] == "O"
    assert cfg["profile"]  # a layout was seeded and selected
    assert overlay.RECOVERED_CONFIG_BACKUP is None
    assert not (tmp_path / "config.json").exists()  # load never writes config.json


@pytest.mark.parametrize("bad", ['{"theme": "light",', "[1, 2, 3]", ""])
def test_corrupt_config_is_backed_up_and_defaults_used(bad, tmp_path, monkeypatch):
    _isolate_config(tmp_path, monkeypatch)
    (tmp_path / "config.json").write_text(bad, encoding="utf-8")
    cfg = overlay.load_config()
    assert cfg["theme"] == "dark"
    assert cfg["profile"]
    backup = tmp_path / "config.json.bak"
    assert backup.read_text(encoding="utf-8") == bad
    assert overlay.RECOVERED_CONFIG_BACKUP == str(backup)


def test_corrupt_config_leaves_saved_layouts_alone(tmp_path, monkeypatch):
    good = overlay.load_config()
    _isolate_config(tmp_path, monkeypatch)
    overlay.save_profile("Keep me", good)
    (tmp_path / "config.json").write_text("not json", encoding="utf-8")
    cfg = overlay.load_config()
    assert cfg["profile"] == "Keep me"
    assert overlay.list_profiles() == ["Keep me"]


def test_backup_flag_resets_on_a_clean_load(tmp_path, monkeypatch):
    _isolate_config(tmp_path, monkeypatch)
    (tmp_path / "config.json").write_text("{", encoding="utf-8")
    overlay.load_config()
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    overlay.load_config()
    assert overlay.RECOVERED_CONFIG_BACKUP is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_overlay.py -q -k "config_is or config_leaves or backup_flag"`
Expected: FAIL. First test with `FileNotFoundError`, the corrupt ones with `json.decoder.JSONDecodeError` or `AttributeError` (list has no `.items`), the flag test with `AttributeError: module 'overlay' has no attribute 'RECOVERED_CONFIG_BACKUP'`.

- [ ] **Step 3: Implement recovery in `load_config`**

In `overlay.py`, add `import logging` to the imports and, after `LOGO_PATH = ...` (line 46), add:

```python
CONFIG_BACKUP_SUFFIX = ".bak"
# Set by load_config() when config.json was unreadable and moved aside; main()
# tells the user once. None after a clean load.
RECOVERED_CONFIG_BACKUP = None

_log = logging.getLogger("az.config")
```

Add above `load_config`:

```python
def _read_config_file():
    """config.json as a dict. Missing file: first run, empty dict. Unreadable or not
    an object: copy it to config.json.bak so nothing is lost, log it, empty dict."""
    global RECOVERED_CONFIG_BACKUP
    RECOVERED_CONFIG_BACKUP = None
    if not os.path.exists(CONFIG_PATH):
        _log.info("No config.json at %s: first run", CONFIG_PATH)
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError(f"top level is {type(raw).__name__}, expected an object")
        return raw
    except (OSError, ValueError) as e:
        backup = CONFIG_PATH + CONFIG_BACKUP_SUFFIX
        try:
            shutil.copy(CONFIG_PATH, backup)
            RECOVERED_CONFIG_BACKUP = backup
            _log.warning("config.json unreadable (%s); copied to %s and using defaults", e, backup)
        except OSError as copy_err:
            _log.error("config.json unreadable (%s) and could not be backed up: %s", e, copy_err)
        return {}
```

Then in `load_config`, replace

```python
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
```

with

```python
    raw = _read_config_file()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_overlay.py -q`
Expected: all pass (the existing 27 plus 6 new).

- [ ] **Step 5: Commit**

```bash
git add overlay.py tests/test_overlay.py
git commit -m "Start with defaults when config.json is missing or corrupt, keeping a backup

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Single instance

**Files:**
- Create: `single_instance.py`
- Test: `tests/test_single_instance.py`

**Interfaces:**
- Produces: `single_instance.SingleInstance(name: str, parent=None)` with `acquire() -> bool` and Signal `activate_requested()`. `single_instance.default_name() -> str` (`"az-overlay-<username>"`).
- Consumed by Task 5: `main()` exits when `acquire()` is False, connects `activate_requested` to `settings.present`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_single_instance.py`:

```python
"""Only one copy of the app runs; a second launch wakes the first one's settings window."""

import uuid

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

import single_instance


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def _pump(app, ms=300):
    from PySide6.QtCore import QDeadlineTimer, QEventLoop
    deadline = QDeadlineTimer(ms)
    while not deadline.hasExpired():
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)


def test_first_acquire_wins_second_loses_and_wakes_the_first(app):
    name = f"az-overlay-test-{uuid.uuid4().hex}"
    first = single_instance.SingleInstance(name)
    woken = []
    first.activate_requested.connect(lambda: woken.append(True))
    assert first.acquire() is True
    second = single_instance.SingleInstance(name)
    assert second.acquire() is False
    _pump(app)
    assert woken == [True]


def test_stale_server_name_is_reclaimed(app):
    name = f"az-overlay-test-{uuid.uuid4().hex}"
    from PySide6.QtNetwork import QLocalServer
    stale = QLocalServer()
    assert stale.listen(name)
    stale.close()  # closes the pipe on Windows; on Unix a socket file can linger
    fresh = single_instance.SingleInstance(name)
    assert fresh.acquire() is True


def test_default_name_is_per_user():
    name = single_instance.default_name()
    assert name.startswith("az-overlay-")
    assert len(name) > len("az-overlay-")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_single_instance.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'single_instance'`

- [ ] **Step 3: Create `single_instance.py`**

```python
"""One running copy per user. The first launch listens on a local socket (a named
pipe on Windows); a later launch connects, says "show", and quits, and the first
copy raises its settings window."""

import getpass

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

_CONNECT_MS = 500
_MESSAGE = b"show\n"


def default_name():
    try:
        user = getpass.getuser()
    except Exception:  # no user name available: still unique enough per machine
        user = "user"
    return f"az-overlay-{user}"


class SingleInstance(QObject):
    activate_requested = Signal()

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self._name = name
        self._server = None

    def acquire(self):
        """True if this process is now the one instance. False if another one is
        running, in which case it has already been asked to show its settings."""
        probe = QLocalSocket()
        probe.connectToServer(self._name)
        if probe.waitForConnected(_CONNECT_MS):
            probe.write(_MESSAGE)
            probe.waitForBytesWritten(_CONNECT_MS)
            probe.disconnectFromServer()
            return False
        QLocalServer.removeServer(self._name)  # a crashed copy may have left the name behind
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        return self._server.listen(self._name)

    def _on_connection(self):
        while self._server.hasPendingConnections():
            conn = self._server.nextPendingConnection()
            conn.readyRead.connect(lambda c=conn: self._on_ready(c))
            conn.disconnected.connect(conn.deleteLater)
            if conn.bytesAvailable():
                self._on_ready(conn)

    def _on_ready(self, conn):
        conn.readAll()  # the content does not matter; any connection means "show"
        self.activate_requested.emit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_single_instance.py -q`
Expected: 3 passed. If `test_first_acquire_wins...` fails on `woken == [True]` with `[]`, the connection arrived after the client disconnected and `readyRead` never fired: the `if conn.bytesAvailable()` branch in `_on_connection` covers that; check it is present. If it fails with `[True, True]`, `readyRead` and the immediate branch both fired: guard with a `conn.setProperty("seen", True)` check in `_on_ready` and return early when already seen.

- [ ] **Step 5: Commit**

```bash
git add single_instance.py tests/test_single_instance.py
git commit -m "Single-instance guard: a second launch wakes the running copy

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Wire main(), tell the user about recovery, document

**Files:**
- Modify: `overlay.py:1393-1425` (`main`)
- Modify: `README.md` (new "Troubleshooting" section before "## Support AZ-Overlay")
- Modify: `settings_ui.py:1612` area (Help page "Can't see your overlay?" card gets one line about the log file)
- Test: `tests/test_overlay_widget.py`

**Interfaces:**
- Consumes: `applog.setup`, `applog.install_excepthook`, `single_instance.SingleInstance`, `single_instance.default_name`, `overlay.RECOVERED_CONFIG_BACKUP`, `version.__version__`.
- Produces: `overlay.recovery_message(backup_path) -> tuple[str, str]` (balloon title and body), `overlay.LOG_PATH` set by `main()`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_overlay_widget.py`:

```python
def test_recovery_message_names_the_backup_file():
    title, body = overlay.recovery_message(r"C:\data\config.json.bak")
    assert "reset" in title.lower() or "reset" in body.lower()
    assert "config.json.bak" in body
    assert "profile" not in (title + body).lower()  # UI says layout, never profile
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_overlay_widget.py::test_recovery_message_names_the_backup_file -q`
Expected: FAIL with `AttributeError: module 'overlay' has no attribute 'recovery_message'`

- [ ] **Step 3: Add `recovery_message` and rewrite `main()`**

In `overlay.py`, add to the imports:

```python
import applog
from single_instance import SingleInstance, default_name as instance_name
```

Add before `main()`:

```python
LOG_PATH = None  # set by main()


def recovery_message(backup_path):
    """Tray balloon shown once after config.json had to be moved aside. Layouts
    live in their own files and are untouched, so only globals were reset."""
    return (f"{APP_NAME} settings were reset",
            f"config.json could not be read. Hotkeys and theme are back to defaults; "
            f"your layouts are untouched. The old file is saved as {os.path.basename(backup_path)}.")
```

Replace `main()` with:

```python
def main():
    global LOG_PATH
    ensure_user_data()
    LOG_PATH = applog.setup(_BASE)
    applog.install_excepthook()
    logging.getLogger("az").info("%s %s starting (frozen=%s, data=%s)", APP_NAME, __version__, FROZEN, _BASE)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # consistent widget rendering; stylesheet in settings_ui relies on it
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    icon = app_icon()
    app.setWindowIcon(icon)

    instance = SingleInstance(instance_name(), app)
    if not instance.acquire():
        logging.getLogger("az").info("Another copy is running; asked it to show settings and exiting")
        sys.exit(0)

    cfg = load_config()

    overlay = Overlay(cfg)
    overlay.show()

    from settings_ui import SettingsWindow  # local import keeps overlay importable in tests

    settings = SettingsWindow(overlay)
    app.aboutToQuit.connect(settings._save_now)
    overlay.open_settings.connect(settings.present)
    instance.activate_requested.connect(settings.present)

    tray = QSystemTrayIcon(icon)
    tray.setToolTip(f"{APP_NAME} — right-click for settings")
    tray.setContextMenu(tray_menu(overlay, settings.present))
    tray.activated.connect(lambda r: settings.present() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None)
    tray.show()
    if RECOVERED_CONFIG_BACKUP:
        title, body = recovery_message(RECOVERED_CONFIG_BACKUP)
        tray.showMessage(title, body, QSystemTrayIcon.MessageIcon.Warning, 8000)
    else:
        tray.showMessage(f"{APP_NAME} running", "Double-click the tray icon or press Ctrl+Alt+S for settings.",
                         icon, 3000)

    sys.exit(app.exec())
```

Note: `sys.exit(1)` on a config error is gone on purpose; `load_config()` no longer raises for a bad file (Task 3). The `import logging` was added in Task 3.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_overlay_widget.py -q`
Expected: all pass (9 existing plus 1).

- [ ] **Step 5: Smoke-run the real app twice**

Run from the repo folder, first copy in the background:

```bash
C:/Python314/python.exe overlay.py &
sleep 3
C:/Python314/python.exe overlay.py; echo "second exit code: $?"
tail -5 az-overlay.log
```

Expected: second copy exits with code 0 within a second; the log ends with a line containing `Another copy is running`; the first copy's settings window came to the front (visible on screen). Then quit the first copy with Ctrl+Alt+Q or the tray menu. `az-overlay.log` is created in the repo folder when running from source: add it to `.gitignore`:

```
# Runtime log (from-source runs write it next to overlay.py)
az-overlay.log
az-overlay.log.*
config.json.bak
```

- [ ] **Step 6: Help page line**

In `settings_ui.py` `_help_page`, in the "Can't see your overlay?" card (the `tip` card around line 1612), append one label after the existing text:

```python
        tip_layout.addWidget(muted(
            "Something else wrong? The log file az-overlay.log in the app's data folder "
            "records errors. Include it when you write in."))
```

Use whatever the card's layout variable is actually named in that function (read the surrounding lines; the pattern is `tip, tip_layout = card()`).

- [ ] **Step 7: README Troubleshooting section**

In `README.md`, insert before `## Support AZ-Overlay`:

```markdown
## Troubleshooting

| Symptom | What to do |
| :--- | :--- |
| Nothing happens when you launch it | It is already running: the launch brought the existing copy's settings window to the front. Look for the tray icon. |
| A balloon says settings were reset | `config.json` could not be read and was copied to `config.json.bak` next to it. Layouts are separate files and are untouched. |
| It crashed or misbehaves | Read `az-overlay.log` in the data folder (see the table above). Include it when reporting a problem. |
| Which version do I have? | **About** in settings shows it, and **Check for updates** opens the releases page. |
```

"the table above" refers to the existing "Settings and saved layouts" table, which lists the data folder per run mode. Its columns (Run mode / Working settings / Named layouts) do not fit a log row, so add one sentence directly under that table instead:

```markdown
The log file `az-overlay.log` sits in the same folder as `config.json`.
```

- [ ] **Step 8: Full suite**

Run: `python -m pytest -q`
Expected: all pass (153 baseline + 1 About + 3 applog + 6 config + 3 single instance + 1 recovery message = 167).

- [ ] **Step 9: Commit**

```bash
git add overlay.py settings_ui.py README.md .gitignore tests/test_overlay_widget.py
git commit -m "Log to a file, refuse a second copy, and recover from a bad config at startup

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Build check (manual, exe only)

**Files:** none changed.

- [ ] **Step 1: Build**

Run: `.\build.bat` from PowerShell in the repo folder (needs `pyinstaller`, `pillow`, `pygame-ce` installed for `C:\Python314\python.exe`).
Expected: ends with `Built dist\AZ-Overlay.exe`.

- [ ] **Step 2: Check metadata**

Run: `powershell -c "(Get-Item dist\AZ-Overlay.exe).VersionInfo | Select-Object FileVersion, ProductVersion, FileDescription"`
Expected: `FileVersion 1.0.0`, `ProductVersion 1.0.0`, `FileDescription AZ-Overlay input overlay`.

- [ ] **Step 3: Run the exe twice**

Double-click `dist\AZ-Overlay.exe`, wait for the tray icon, double-click it again.
Expected: no second tray icon; the settings window comes to the front. `%APPDATA%\az-overlay\az-overlay.log` exists and contains the startup line with `1.0.0` and the `Another copy is running` line. Quit via the tray menu.

No commit: `dist/` and `build/` are gitignored.

---

## Self-review

**Spec coverage.** Item 1 (crash log, excepthook): Tasks 2 and 5. Item 2 (single instance, raise settings): Tasks 4 and 5. Item 3 (backup, defaults, keep running, log): Task 3, balloon in Task 5. Item 4 (version in code, About, exe metadata, Check for updates link, no network): Task 1. Nothing in batch 1 is uncovered.

**Placeholders.** Step 6 of Task 5 tells the engineer to read the card's variable name rather than asserting it; that is deliberate because the line numbers around `_help_page` shift after Task 1's edits. Every other step carries its code.

**Type consistency.** `applog.setup(log_dir) -> str` used in Task 5 as `LOG_PATH = applog.setup(_BASE)`. `SingleInstance(name, parent)` with `acquire()` and `activate_requested` used identically in Tasks 4 and 5. `RECOVERED_CONFIG_BACKUP` defined in Task 3, read in Task 5. `recovery_message(backup_path) -> (title, body)` defined and tested in Task 5. `__version__` from `version.py` used in Tasks 1, 5, and `make_version.py`.
