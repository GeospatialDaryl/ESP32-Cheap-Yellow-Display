"""Individual mixer fader component."""
from __future__ import annotations

from ..backend import PipewireBackend
from ..environment import Gtk
from ..midi import MidiController
from ..models import PipewireNode


if Gtk is None:  # pragma: no cover - import guard for environments without GTK

    class FaderRow:  # type: ignore[too-many-ancestors]
        """Placeholder used when GTK is not available."""

        def __init__(self, *_: object, **__: object) -> None:
            raise RuntimeError("GTK is required for FaderRow")

else:

    class FaderRow(Gtk.Box):
        """Single mixer fader with optional MIDI bindings."""

        def __init__(self, backend: PipewireBackend, midi: MidiController, node: PipewireNode):
            super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            self.set_margin_top(6)
            self.set_margin_bottom(6)
            self.set_margin_start(6)
            self.set_margin_end(6)
            self.backend = backend
            self.midi = midi
            self.node = node

            # The header surfaces the node name and wraps it to avoid overly
            # wide tiles when descriptive names are used.
            header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            header.append(Gtk.Label(label=node.name, wrap=True, justify=Gtk.Justification.CENTER))

            self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, 0.0, 1.5, 0.01)
            self.scale.set_vexpand(True)
            self.scale.set_value_pos(Gtk.PositionType.BOTTOM)
            self.scale.connect("value-changed", self._on_value_changed)

            # MIDI controls live underneath the slider so each tile remains a
            # self-contained unit during layout changes.
            controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            self.channel_spin = Gtk.SpinButton.new_with_range(1, 16, 1)
            self.channel_spin.set_value(1)
            self.channel_spin.connect("value-changed", self._update_binding)
            controls.append(Gtk.Label(label="MIDI Ch."))
            controls.append(self.channel_spin)

            self.cc_spin = Gtk.SpinButton.new_with_range(0, 127, 1)
            self.cc_spin.set_value(7)
            self.cc_spin.connect("value-changed", self._update_binding)
            controls.append(Gtk.Label(label="CC"))
            controls.append(self.cc_spin)

            # ``Sync`` allows the user to restore GTK state after external
            # volume changes (e.g., via ``wpctl set-volume`` in another
            # terminal).
            refresh_button = Gtk.Button(label="Sync")
            refresh_button.connect("clicked", lambda *_: self.sync_from_backend())
            controls.append(refresh_button)

            self.append(header)
            self.append(self.scale)
            self.append(controls)

            self.sync_from_backend()
            self._update_binding()

        # ------------------------------------------------------------------
        def sync_from_backend(self) -> None:
            """Synchronize the slider position with the backend volume."""

            volume = self.backend.get_volume(self.node.id)
            if volume is not None:
                self.scale.set_value(volume)

        def _on_value_changed(self, scale: Gtk.Scale) -> None:
            value = scale.get_value()
            success = self.backend.set_volume(self.node.id, value)
            if not success:
                # Tooltips double as lightweight status messages without
                # bloating the UI with extra labels.
                scale.set_tooltip_text("Failed to set volume via wpctl.")
            else:
                scale.set_tooltip_text(None)

        def _update_binding(self, *_: object) -> None:
            if not self.midi.available:
                return
            # Rebinding clears the previous assignment before applying the new
            # channel/CC pair entered by the user.
            self.midi.unbind_slider(self.scale)
            channel = int(self.channel_spin.get_value())
            control = int(self.cc_spin.get_value())
            self.midi.bind(channel, control, self.scale)


__all__ = ["FaderRow"]
