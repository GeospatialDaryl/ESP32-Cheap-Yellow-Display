"""Helpers for optional third-party dependencies.

This module keeps dependency discovery in a single location so that other
modules can simply import the symbols they need.  The approach avoids
sprinkling conditional imports around the codebase and makes unit testing
simpler because every dependent module can patch this module instead of the
upstream packages.
"""
from __future__ import annotations

import importlib
import importlib.util
from types import ModuleType
from typing import Optional, Tuple


def _load_gi_modules() -> Tuple[Optional[ModuleType], Optional[ModuleType], Optional[ModuleType], Optional[ModuleType], Optional[ModuleType]]:
    """Attempt to load GTK/libadwaita bindings.

    The loader intentionally avoids ``try/except`` around the import
    statements.  Instead it inspects module specifications first; only when
    a module is advertised as present do we request it via
    :func:`importlib.import_module`.  If any intermediate step fails the
    function returns ``None`` placeholders so that callers can react without
    raising immediate ImportErrors.
    """

    if importlib.util.find_spec("gi") is None:
        return None, None, None, None, None

    # ``importlib`` keeps the logic compact while still avoiding ``try``/``except``
    # blocks around the import statement itself as mandated by the project's
    # guidelines.
    gi_module = importlib.import_module("gi")

    # ``require_version`` raises ``ValueError`` when the bindings are missing
    # the requested ABI; this is caught so the UI layer can degrade gracefully.
    try:
        gi_module.require_version("Gtk", "4.0")
        gi_module.require_version("Adw", "1")
    except ValueError:
        return None, None, None, None, None

    module_names = ["Adw", "Gio", "GLib", "Gtk"]
    loaded: list[Optional[ModuleType]] = [gi_module]
    for name in module_names:
        if importlib.util.find_spec(f"gi.repository.{name}") is None:
            return None, None, None, None, None
        loaded.append(importlib.import_module(f"gi.repository.{name}"))
    # ``loaded`` now holds ``[gi, Adw, Gio, GLib, Gtk]`` as modules.
    return tuple(loaded)  # type: ignore[return-value]


gi, Adw, Gio, GLib, Gtk = _load_gi_modules()


def load_mido() -> Optional[ModuleType]:
    """Load the ``mido`` package on demand.

    The MIDI layer does not strictly depend on the library.  By exposing the
    helper we can keep module level state inside :mod:`midi` reusable in unit
    tests without having to mock ``importlib`` directly.
    """

    # ``mido`` is optional; returning ``None`` allows callers to disable MIDI
    # functionality without raising import errors on systems that only need the
    # audio routing capabilities.
    if importlib.util.find_spec("mido") is None:
        return None
    return importlib.import_module("mido")


__all__ = ["gi", "Adw", "Gio", "GLib", "Gtk", "load_mido"]
