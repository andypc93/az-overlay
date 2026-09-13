"""Logging goes to a rotating file in the data folder; uncaught exceptions land there too."""

import logging
import logging.handlers
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
    file_handlers = [h for h in logging.getLogger().handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
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
