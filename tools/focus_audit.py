"""Read-only, bounded KWin/AT-SPI focus audit for a live Plasma session.

Run with /usr/bin/python3 tools/focus_audit.py. Switch among the affected
editors while it runs. No keyboard events, field contents, window titles or
URLs are collected. The production daemon remains running.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wayswitch import a11y as a  # noqa: E402
from wayswitch.backends.kwin_focus import KWinFocusBridge  # noqa: E402


def sample(context, state):
    started = time.monotonic()
    report = {"pid": context.pid if context else None,
              "epoch": context.window_epoch if context else None}
    if context is None:
        report["result"] = "no-live-kwin-context"
        return report

    class TraceTree(a._DbusTree):
        def __init__(self, conn):
            super().__init__(conn)
            self.calls = collections.Counter()
            self.errors = collections.Counter()
            self.focused = set()
            self.roles = {}
            self.candidates = []
            self.collection_hits = 0

        def _call(self, node, iface, method, arg, sig):
            if time.monotonic() - started > 5.0:
                raise TimeoutError("audit budget exhausted")
            self.calls[method] += 1
            value = super()._call(node, iface, method, arg, sig)
            if value is None:
                self.errors[method] += 1
            return value

        def role(self, node):
            role = super().role(node)
            self.roles[node] = role
            return role

        def state(self, node):
            bits = super().state(node)
            if a._state_focused(bits):
                self.focused.add(node)
            return bits

        def focused_path(self, node):
            path = super().focused_path(node)
            self.collection_hits += int(bool(path))
            return path

    tree = None
    original = a._caret_field

    def trace_field(t, node, parents, remaining, depth):
        # Record only roles and boolean validation outcome, not actual text.
        result = original(t, node, parents, remaining, depth)
        chain = []
        ancestor = node
        while ancestor is not None and len(chain) <= a.MAX_DEPTH:
            chain.append(t.roles.get(ancestor))
            ancestor = parents.get(ancestor)
        t.candidates.append({"role_chain": chain, "depth": depth,
                             "verified": result is not None,
                             "protected": bool(result[1]) if result else None})
        return result

    try:
        tree = TraceTree(a._a11y_connection())
        roots = tree.children(a.ROOT)
        apps = []
        for node in roots or ():
            pid = tree.pid(node)
            name = tree.app_name(node)
            match = a._same_application(pid, context.pid)
            row = {"app": name, "pid": pid, "match": match}
            if match:
                windows = tree.children(node) or []
                row["windows"] = len(windows)
                row["active"] = sum(a._state_bit(tree.state(w), a.ACTIVE)
                                    for w in windows)
            apps.append(row)
        report["apps"] = apps
        a._caret_field = trace_field
        snap = a.find_focus(tree, a.ROOT, context.pid)
        if state.snapshot() != context:
            report["result"] = "window-changed-during-query"
        elif snap.app and snap.field:
            report.update(result="verified", app=snap.app, protected=snap.password)
        elif not any(row["match"] for row in apps):
            report["result"] = "no-matching-atspi-app"
        else:
            report["result"] = "no-verified-field"
    except Exception as exc:
        report["result"] = type(exc).__name__
    finally:
        a._caret_field = original
        if tree is not None:
            report["focused_nodes"] = len(tree.focused)
            report["focus_candidates"] = tree.candidates
            report["collection_hits"] = tree.collection_hits
            report["calls"] = dict(tree.calls)
            report["errors"] = dict(tree.errors)
        report["ms"] = round((time.monotonic() - started) * 1000)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=55)
    args = parser.parse_args()
    from gi.repository import GLib

    context = GLib.MainContext.default()
    bridge = None

    def pump():
        while context.pending():
            context.iteration(False)

    try:
        bridge = KWinFocusBridge(label=f"wayswitch-focus-audit-{os.getpid()}",
                                 exclusive=False)
        bridge.start()
        print("KWin bridge ready. Switch between Kate, Chrome, Telegram, LibreWolf.",
              flush=True)
        print("Keep each editor active for 8-12 s; click its text field.", flush=True)
        end = time.monotonic() + max(5, min(args.seconds, 180))
        next_sample = time.monotonic() + 3
        while time.monotonic() < end:
            pump()
            if time.monotonic() < next_sample:
                time.sleep(.02)
                continue
            snapshot = bridge.state.snapshot()
            rows = []
            worker = threading.Thread(
                target=lambda rows=rows, snapshot=snapshot: rows.append(
                    sample(snapshot, bridge.state)),
                daemon=True,
            )
            worker.start()
            while worker.is_alive():
                pump()
                worker.join(.02)
            if rows:
                print(json.dumps(rows[0], ensure_ascii=False), flush=True)
            next_sample = time.monotonic() + 1.5
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print("BRIDGE_ERROR:", type(exc).__name__, flush=True)
        return 1
    finally:
        if bridge is not None:
            bridge.close()


if __name__ == "__main__":
    raise SystemExit(main())
