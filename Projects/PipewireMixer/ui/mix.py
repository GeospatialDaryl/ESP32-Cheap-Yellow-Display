"""Mixer tab with dynamic faders and MIDI bindings."""
from __future__ import annotations

from ..backend import PipewireBackend
from ..environment import Gtk
from ..midi import MidiController
from .fader import FaderRow


if Gtk is None:  # pragma: no cover - import guard for environments without GTK

    class MixView:  # type: ignore[too-many-ancestors]
        """Placeholder used when GTK is not available."""

        def __init__(self, *_: object, **__: object) -> None:
            raise RuntimeError("GTK is required for MixView")

else:

    class MixView(Gtk.Box):
        """Container for the mixer tab."""

        def __init__(self, backend: PipewireBackend, midi: MidiController):
            super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            self.backend = backend
            self.midi = midi

            # The header mirrors the routing tab by exposing refresh and MIDI
            # selection widgets in a single row.
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            header.set_margin_top(6)
            header.set_margin_start(6)
            header.set_margin_end(6)
            refresh_button = Gtk.Button(label="Refresh")
            refresh_button.connect("clicked", lambda *_: self.refresh())
            header.append(refresh_button)

            if midi.available:
                header.append(Gtk.Label(label="MIDI Input:"))
                self.midi_ports = Gtk.DropDown.new_from_strings(midi.get_ports())
                self.midi_ports.connect("notify::selected", self._on_midi_selected)
                header.append(self.midi_ports)
            else:
                header.append(Gtk.Label(label="MIDI support requires python-mido", xalign=0.0))

            self.append(header)

            # ``Gtk.FlowBox`` automatically wraps faders, keeping the UI usable
            # even when dozens of sinks are present.
            self.flow = Gtk.FlowBox()
            self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
            self.flow.set_valign(Gtk.Align.START)
            self.append(self.flow)

            self.refresh()

        # ------------------------------------------------------------------
        def refresh(self) -> None:
            """Recreate faders for every discovered audio sink."""

            self.backend.refresh()
            # Removing stale faders prevents memory leaks when the PipeWire
            # graph changes (e.g., when USB devices are unplugged).
            for child in list(self.flow.get_children()):
                self.flow.remove(child)
            sinks = self.backend.get_audio_sinks()
            if not sinks:
                placeholder = Gtk.Label(label="No audio sinks detected. Is PipeWire running?", xalign=0.5)
                self.flow.append(placeholder)
                return
            for node in sinks:
                row = FaderRow(self.backend, self.midi, node)
                self.flow.append(row)

        def _on_midi_selected(self, dropdown: Gtk.DropDown, *_: object) -> None:
            if not self.midi.available:
                return
            index = dropdown.get_selected()
            ports = self.midi.get_ports()
            # ``Gtk.DropDown`` returns ``-1`` when nothing is selected; the
            # guard avoids ``IndexError`` when toggling between ports quickly.
            name = ports[index] if 0 <= index < len(ports) else None
            self.midi.open(name)


__all__ = ["MixView"]
