"""MIDI controller bindings for mixer faders."""
from __future__ import annotations

import threading
from typing import Dict, Optional, Tuple

from .environment import GLib, Gtk, load_mido

mido = load_mido()


class MidiController:
    """Handle MIDI Continuous Controller messages for GTK sliders."""

    def __init__(self) -> None:
        # ``mido`` exposes ``BaseInput`` objects that we store generically to
        # avoid importing optional typing helpers from the library itself.
        self._input: Optional[object] = None
        self._bindings: Dict[Tuple[int, int], Gtk.Scale] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    @property
    def available(self) -> bool:
        """Return ``True`` when both GTK and ``mido`` are available."""

        return mido is not None and Gtk is not None and GLib is not None

    def get_ports(self) -> list[str]:
        """Return all available MIDI input port names."""

        if not self.available:
            return []
        # Sorting the ports keeps the UI deterministic even when the ALSA
        # enumeration order changes between boots.
        return sorted(mido.get_input_names())  # type: ignore[no-any-return]

    def open(self, name: Optional[str]) -> bool:
        """Open the selected MIDI input port and attach a callback."""

        if not self.available:
            return False
        with self._lock:
            if self._input is not None:
                # Closing the previous input ensures we never leak file
                # descriptors when the user switches ports repeatedly.
                self._input.close()
                self._input = None
            if not name:
                return True
            try:
                self._input = mido.open_input(name, callback=self._handle_message)
            except (IOError, OSError):
                return False
        return True

    def bind(self, channel: int, control: int, slider: Gtk.Scale) -> None:
        """Bind a slider to a MIDI channel/control pair."""

        if not self.available:
            return
        key = (channel, control)
        with self._lock:
            self._bindings[key] = slider

    def unbind_slider(self, slider: Gtk.Scale) -> None:
        """Remove existing bindings referencing ``slider``."""

        if not self.available:
            return
        with self._lock:
            for key, bound in list(self._bindings.items()):
                if bound is slider:
                    self._bindings.pop(key)

    # ------------------------------------------------------------------
    def _handle_message(self, message):  # type: ignore[override]
        """Handle incoming MIDI CC messages and update the slider value."""

        if message.type != "control_change":
            return
        # MIDI CC values range from 0..127; scaling to ``1.5`` mirrors the
        # volume limits enforced in :meth:`PipewireBackend.set_volume`.
        value = message.value / 127.0 * 1.5
        key = (message.channel + 1, message.control)
        with self._lock:
            slider = self._bindings.get(key)
        if slider is None or GLib is None:
            return
        # ``idle_add`` marshals the update back onto the GTK main loop to keep
        # thread interactions safe.
        GLib.idle_add(slider.set_value, value, priority=GLib.PRIORITY_DEFAULT)


__all__ = ["MidiController"]
