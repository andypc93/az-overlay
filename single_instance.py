"""One running copy per user. The first launch listens on a local socket (a named
pipe on Windows); a later launch connects and quits, and the first copy raises
its settings window. Connecting is the whole message: nothing is written, since
a socket that is destroyed right after acquire() returns never flushes."""

import getpass
import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

_CONNECT_MS = 500

_log = logging.getLogger("az.instance")


def default_name():
    try:
        user = getpass.getuser()
    except (OSError, KeyError):  # no user name available: still unique enough per machine
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
            probe.disconnectFromServer()
            return False
        QLocalServer.removeServer(self._name)  # a crashed copy may have left the name behind
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        if not self._server.listen(self._name):
            # Nobody answered, yet the name cannot be claimed either (permissions, a
            # foreign pipe). Running is better than exiting silently.
            _log.warning("Could not claim %s (%s); running without the single-instance guard",
                         self._name, self._server.errorString())
        return True

    def _on_connection(self):
        while self._server.hasPendingConnections():
            conn = self._server.nextPendingConnection()
            conn.disconnected.connect(conn.deleteLater)
            conn.close()
            self.activate_requested.emit()
