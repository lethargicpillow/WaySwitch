"""Регрессии KWin PID-источника, без живого композитора."""

import pytest

from tests.test_focus import editable_tree
from wayswitch import a11y
from wayswitch.backends.kwin_focus import LEASE, FocusState


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


def test_focus_state_requires_recent_pid():
    clock = Clock()
    state = FocusState(clock)
    assert state.snapshot() is None
    assert state.accept(1, 0, 123) == (True, True)
    assert state.snapshot() == a11y.ShellContext(pid=123, window_epoch=0)
    assert state.accept(2, 0, 123, True) == (True, False)
    assert not state.seen()
    assert state.accept(3, 0, 123, True) == (True, False)
    assert state.seen()
    clock.now += LEASE + 0.1
    assert state.snapshot() is None
    assert state.expire()
    assert state.accept(4, 0, 123) == (True, True)


def test_window_epoch_and_reordered_reports():
    state = FocusState()
    state.accept(1, 0, 123)
    old = state.snapshot()
    assert state.accept(3, 1, 123) == (True, True)
    assert state.snapshot() != old
    assert state.accept(2, 0, 456) == (False, False)
    # PID может появиться позже первого сообщения при создании окна.
    assert state.accept(4, 1, 456) == (True, True)
    assert state.snapshot().pid == 456
    assert state.accept(5, 2, 0) == (True, True)
    assert state.snapshot() is None
    assert state.accept(6, 3, 123) == (True, True)
    assert state.lose()
    assert state.snapshot() is None


@pytest.mark.parametrize("password", [False, True])
def test_pid_scopes_focus_not_first_active_window(monkeypatch, password):
    tree = editable_tree()
    tree.nodes[a11y.ROOT] = tree.nodes.pop("root")
    tree.nodes[a11y.ROOT]["kids"] = ["proxy", "app"]
    tree.nodes["proxy"] = {"name": "Proxy", "pid": 456, "kids": ["proxy-window"]}
    tree.nodes["proxy-window"] = {"state": [a11y.ACTIVE], "kids": []}
    tree.nodes["field"]["role"] = 40 if password else 61
    monkeypatch.setattr(a11y, "_a11y_connection", lambda: object())
    monkeypatch.setattr(a11y, "_DbusTree", lambda _: tree)
    state = FocusState()
    state.accept(1, 0, 123)
    snap = a11y.query_focus(state.snapshot)
    assert snap.app == "Editor"
    assert snap.password is password
    assert snap.field == "field"
    state.lose()
    assert not a11y.query_focus(state.snapshot).app


def test_context_changes_during_query_reject_old_field(monkeypatch):
    tree = editable_tree()
    tree.nodes[a11y.ROOT] = tree.nodes.pop("root")
    monkeypatch.setattr(a11y, "_a11y_connection", lambda: object())
    monkeypatch.setattr(a11y, "_DbusTree", lambda _: tree)
    contexts = iter([a11y.ShellContext(pid=123, window_epoch=0),
                     a11y.ShellContext(pid=123, window_epoch=1)])
    assert not a11y.query_focus(lambda: next(contexts)).app


def test_provider_lifecycle(monkeypatch):
    monkeypatch.setattr(a11y, "_query_gnome_context", lambda: a11y.ShellContext())
    state = FocusState()
    state.accept(1, 0, 123)
    try:
        a11y.set_context_provider(state.snapshot)
        assert a11y.query_shell_context().pid == 123
        state.lose()
        assert a11y.query_shell_context() is None
    finally:
        a11y.set_context_provider(None)
    assert a11y.query_shell_context() == a11y.ShellContext()


def test_late_pid_after_window_activation():
    state = FocusState()
    state.accept(1, 0, 0)
    assert state.snapshot() is None
    assert state.accept(2, 0, 123, True) == (True, True)
    assert state.snapshot().pid == 123
