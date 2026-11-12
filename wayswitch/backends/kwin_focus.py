"""Доверенный PID активного окна Plasma 6 через официальный KWin Scripting API.

JS существует только в течение работы демона; отдельный сервис, установка
скрипта в профиль и подмена функций AT-SPI не нужны. Событие активации
инвалидирует снимок, даже если два окна принадлежат одному PID.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from pathlib import Path

from wayswitch.a11y import ShellContext

log = logging.getLogger("wayswitch")
SERVICE = "org.kde.KWin"
SCRIPT_IFACE = "org.kde.kwin.Scripting"
SCRIPT_PATH = "/Scripting"
BRIDGE_PATH = "/org/wayswitch/KWinFocus"
BRIDGE_IFACE = "org.wayswitch.KWinFocus"
LEASE = 1.8
HEARTBEAT_MS = 450
XML = """<node><interface name="org.wayswitch.KWinFocus">
<method name="Report">
  <arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="in"/>
</method>
<method name="Heartbeat">
  <arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="in"/>
</method>
</interface></node>"""

# Ответ на heartbeat задерживается на стороне Python, не в потоке KWin.
# Передаём только PID, номер сообщения и поколение окна, никаких заголовков.
JS = """var destination = __DEST__;
var sequence = 0;
var epoch = 0;
function report(method, window, callback) {
    var pid = 0;
    if (window && window.pid > 0 && !window.deleted) pid = window.pid;
    sequence += 1;
    if (callback) {
        callDBus(destination, "/org/wayswitch/KWinFocus", "org.wayswitch.KWinFocus", method,
                 String(sequence), String(epoch), String(pid), callback);
    } else {
        callDBus(destination, "/org/wayswitch/KWinFocus", "org.wayswitch.KWinFocus", method,
                 String(sequence), String(epoch), String(pid));
    }
}
function tick() { report("Heartbeat", workspace.activeWindow, tick); }
workspace.windowActivated.connect(function(window) {
    epoch += 1;
    report("Report", window, null);
});
report("Report", workspace.activeWindow, null);
tick();
"""


class FocusState:
    """Снимок, доступный из фонового AT-SPI-потока без вызова D-Bus."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.Lock()
        self.seq = -1
        self.epoch = -1
        self.pid = 0
        self.last = None
        self.invalidated = True
        self.heartbeats = 0

    def accept(self, seq, epoch, pid, heartbeat=False):
        with self.lock:
            if seq <= self.seq or epoch < self.epoch or not 0 <= pid <= 2147483647:
                return False, False
            change = self.invalidated or (self.epoch, self.pid) != (epoch, pid)
            self.seq, self.epoch, self.pid = seq, epoch, pid
            self.last = self.clock()
            self.heartbeats += int(heartbeat)
            self.invalidated = False
            return True, change

    def snapshot(self):
        with self.lock:
            if (self.invalidated or self.last is None
                    or self.clock() - self.last > LEASE or not self.pid):
                return None
            return ShellContext(pid=self.pid, window_epoch=self.epoch)

    def expire(self):
        with self.lock:
            if not self.invalidated and self.last is not None and self.clock() - self.last > LEASE:
                self.invalidated = True
                return True
            return False

    def lose(self):
        with self.lock:
            change = not self.invalidated
            self.invalidated = True
            return change

    def seen(self):
        with self.lock:
            return (self.heartbeats >= 2 and self.last is not None and not self.invalidated
                    and self.clock() - self.last <= LEASE)


class KWinFocusBridge:
    """Сессионный D-Bus объект и временный KWin JS, с проверкой отправителя."""

    def __init__(self, label="wayswitch-kwin-focus", *, exclusive=True):
        from gi.repository import Gio, GLib

        self.Gio, self.GLib = Gio, GLib
        self.context = GLib.MainContext.get_thread_default() or GLib.MainContext.default()
        self.state = FocusState()
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.label = label
        self.exclusive = exclusive
        self.owns_name = False
        self.owner = self._call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                                "org.freedesktop.DBus", "GetNameOwner",
                                "(s)", (SERVICE,), "(s)")[0]
        self.on_change = lambda: None
        self.on_lost = lambda: None
        self.registration = self.watch = self.timer = None
        self.temp = None
        self.loaded = False
        self.closed = False
        self.owner_lost = False
        self.replies = {}

    def _call(self, dest, path, iface, method, signature=None, args=(), reply=None):
        gio, glib = self.Gio, self.GLib
        value = glib.Variant(signature, args) if signature else None
        typ = glib.VariantType.new(reply) if reply else None
        result = self.bus.call_sync(dest, path, iface, method, value, typ,
                                    gio.DBusCallFlags.NONE, 2500, None)
        return result.unpack() if result is not None else ()

    def _timeout(self, ms, callback):
        source = self.GLib.timeout_source_new(ms)
        source.set_callback(callback)
        source.attach(self.context)
        return source

    def _owner_changed(self, _bus, _sender, _path, _iface, _signal, params):
        name, old, new = params.unpack()
        if name == SERVICE and old == self.owner and new != self.owner:
            self.owner_lost = True
            self.state.lose()
            self.on_change()
            self.on_lost()

    def _method(self, _bus, sender, _path, _iface, method, params, invocation):
        if self.closed or self.owner_lost or sender != self.owner:
            invocation.return_dbus_error(BRIDGE_IFACE + ".Rejected", "unexpected sender")
            return
        try:
            seq, epoch, pid = (int(x) for x in params.unpack())
            if seq < 1 or epoch < 0 or method not in ("Report", "Heartbeat"):
                raise ValueError("invalid metadata")
            accepted, changed = self.state.accept(seq, epoch, pid, method == "Heartbeat")
        except (TypeError, ValueError):
            invocation.return_dbus_error(BRIDGE_IFACE + ".Rejected", "invalid metadata")
            return
        if accepted and changed:
            self.on_change()

        def reply(*_args):
            self.replies.pop(seq, None)
            invocation.return_value(self.GLib.Variant("()", ()))
            return False

        if method == "Heartbeat":
            self.replies[seq] = (self._timeout(HEARTBEAT_MS, reply), invocation)
        else:
            reply()

    def _watchdog(self, *_args):
        if self.state.expire():
            self.on_change()
            log.warning("KWin: снимок активного окна просрочен")
        return not self.closed

    def start(self):
        gio = self.Gio
        if self.exclusive:
            # Не выгружаем рабочий скрипт, если случайно запущен второй демон.
            # DO_NOT_QUEUE: повторный экземпляр не сможет перехватить имя позже.
            result = self._call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                                "org.freedesktop.DBus", "RequestName",
                                "(su)", (BRIDGE_IFACE, 4), "(u)")[0]
            if result != 1:
                raise RuntimeError("another KWin focus bridge is running")
            self.owns_name = True
        self.node_info = gio.DBusNodeInfo.new_for_xml(XML)
        self.registration = self.bus.register_object(
            BRIDGE_PATH, self.node_info.interfaces[0], self._method, None, None)
        self.watch = self.bus.signal_subscribe(
            "org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
            "/org/freedesktop/DBus", SERVICE, gio.DBusSignalFlags.NONE, self._owner_changed)
        self.timer = self._timeout(200, self._watchdog)
        self.temp = tempfile.TemporaryDirectory(
            prefix="wayswitch-kwin-", dir=os.environ.get("XDG_RUNTIME_DIR"))
        js = Path(self.temp.name) / "focus.js"
        js.write_text(JS.replace("__DEST__", json.dumps(self.bus.get_unique_name())),
                      encoding="utf-8")
        # Удаляем только собственный экземпляр, оставшийся после аварийного завершения.
        try:
            self._call(self.owner, SCRIPT_PATH, SCRIPT_IFACE, "unloadScript",
                       "(s)", (self.label,), "(b)")
        except Exception:
            pass
        script_id = -1
        for _ in range(8):
            script_id = self._call(self.owner, SCRIPT_PATH, SCRIPT_IFACE, "loadScript",
                                   "(ss)", (str(js), self.label), "(i)")[0]
            if script_id >= 0:
                break
            time.sleep(.1)
        if script_id < 0:
            raise RuntimeError("KWin rejected focus script")
        self.loaded = True
        self._call(self.owner, f"/Scripting/Script{script_id}", "org.kde.kwin.Script", "run")
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and not self.state.seen():
            while self.context.pending():
                self.context.iteration(False)
            time.sleep(.02)
        if not self.state.seen():
            raise RuntimeError("KWin focus heartbeat unavailable")

    def close(self):
        self.closed = True
        self.state.lose()
        self.on_change()
        if self.loaded:
            try:
                self._call(self.owner, SCRIPT_PATH, SCRIPT_IFACE, "unloadScript",
                           "(s)", (self.label,), "(b)")
            except Exception:
                pass
        if self.timer is not None:
            self.timer.destroy()
        for source, invocation in self.replies.values():
            source.destroy()
            invocation.return_dbus_error(BRIDGE_IFACE + ".Rejected", "bridge closed")
        self.replies.clear()
        if self.watch is not None:
            self.bus.signal_unsubscribe(self.watch)
        if self.registration is not None:
            self.bus.unregister_object(self.registration)
        if self.temp is not None:
            self.temp.cleanup()
        if self.owns_name:
            try:
                self._call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                           "org.freedesktop.DBus", "ReleaseName",
                           "(s)", (BRIDGE_IFACE,), "(u)")
            except Exception:
                pass
            self.owns_name = False


def query_active_focus():
    """Однократная диагностика KDE; отдельный экземпляр не трогает демон."""
    from gi.repository import GLib

    from wayswitch import a11y

    context = GLib.MainContext.new()
    context.push_thread_default()
    bridge = None
    try:
        bridge = KWinFocusBridge(label=f"wayswitch-kwin-doctor-{os.getpid()}", exclusive=False)
        bridge.start()
        result = []

        def worker():
            try:
                result.append(a11y.query_focus(bridge.state.snapshot))
            except Exception:
                result.append(a11y.FocusSnapshot())

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        while thread.is_alive():
            while context.pending():
                context.iteration(False)
            thread.join(.02)
        return result[0]
    except Exception:
        return a11y.FocusSnapshot()
    finally:
        try:
            if bridge is not None:
                bridge.close()
        finally:
            context.pop_thread_default()
