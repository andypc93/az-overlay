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
