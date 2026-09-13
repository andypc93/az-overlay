"""Only one copy of the app runs; a second launch wakes the first one's settings window."""

import uuid

import pytest
from PySide6.QtCore import QDeadlineTimer, QEventLoop
from PySide6.QtNetwork import QLocalServer
from PySide6.QtWidgets import QApplication

import single_instance


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def _pump(app, ms=300):
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
    stale = QLocalServer()
    assert stale.listen(name)
    stale.close()  # closes the pipe on Windows; on Unix a socket file can linger
    fresh = single_instance.SingleInstance(name)
    assert fresh.acquire() is True


def test_default_name_is_per_user():
    name = single_instance.default_name()
    assert name.startswith("az-overlay-")
    assert len(name) > len("az-overlay-")
