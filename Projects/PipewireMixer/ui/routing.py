"""Routing tab mirroring the qpwgraph workflow."""
from __future__ import annotations

from typing import Optional, Tuple

from ..backend import PipewireBackend
from ..environment import Gtk
from ..models import PipewirePort


if Gtk is None:  # pragma: no cover - import guard for environments without GTK

    class RoutingView:  # type: ignore[too-many-ancestors]
        """Placeholder used when GTK is not available."""

        def __init__(self, *_: object, **__: object) -> None:
            raise RuntimeError("GTK is required for RoutingView")

else:

    class RoutingView(Gtk.Box):
        """Display routing controls similar to ``qpwgraph``."""

        def __init__(self, backend: PipewireBackend):
            super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            self.backend = backend

            # The header provides quick access to a refresh action and
            # connection status details, mirroring ``qpwgraph``'s immediate
            # feedback model.
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            refresh_button = Gtk.Button(label="Refresh")
            refresh_button.connect("clicked", lambda *_: self.refresh())
            self.status_label = Gtk.Label(xalign=0.0)
            header.append(refresh_button)
            header.append(self.status_label)

            self.append(header)

            paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
            self.append(paned)

            # Drop-downs are backed by ``Gtk.StringList`` to keep the widgets
            # lightweight.  We rebuild the model on every refresh so we can rely
            # on indices lining up with ``backend.get_*`` results.
            self.source_store = Gtk.StringList.new([])
            self.source_dropdown = Gtk.DropDown()
            self.source_dropdown.set_model(self.source_store)
            self.source_dropdown.set_expression(Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
            source_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            source_box.set_margin_top(6)
            source_box.set_margin_bottom(6)
            source_box.set_margin_start(6)
            source_box.set_margin_end(6)
            source_box.append(Gtk.Label(label="Outputs", xalign=0.0))
            source_box.append(self.source_dropdown)

            self.sink_store = Gtk.StringList.new([])
            self.sink_dropdown = Gtk.DropDown()
            self.sink_dropdown.set_model(self.sink_store)
            self.sink_dropdown.set_expression(Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
            sink_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            sink_box.set_margin_top(6)
            sink_box.set_margin_bottom(6)
            sink_box.set_margin_start(6)
            sink_box.set_margin_end(6)
            sink_box.append(Gtk.Label(label="Inputs", xalign=0.0))
            sink_box.append(self.sink_dropdown)

            # Connection actions live in a dedicated column to keep the
            # workflow clear: pick output/input, then press connect or
            # disconnect.
            button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            button_box.set_margin_top(6)
            button_box.set_margin_bottom(6)
            connect_button = Gtk.Button(label="Connect")
            connect_button.connect("clicked", self._handle_connect)
            disconnect_button = Gtk.Button(label="Disconnect")
            disconnect_button.connect("clicked", self._handle_disconnect)
            button_box.append(connect_button)
            button_box.append(disconnect_button)

            paned.set_start_child(source_box)
            right_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
            right_box.append(button_box)
            right_box.append(sink_box)
            paned.set_end_child(right_box)

            self.refresh()

        # ------------------------------------------------------------------
        def refresh(self) -> None:
            """Refresh the backend cache and rebuild the drop-down models."""

            self.backend.refresh()
            # We request fresh lists to avoid stale references should the graph
            # change between the selection and the button press.
            sources = self.backend.get_source_ports()
            sinks = self.backend.get_sink_ports()

            self.source_store.splice(0, self.source_store.get_n_items(), [])
            for port in sources:
                self.source_store.append(port.display_name)
            self.sink_store.splice(0, self.sink_store.get_n_items(), [])
            for port in sinks:
                self.sink_store.append(port.display_name)
            if sources or sinks:
                self.status_label.set_text(f"Outputs: {len(sources)} · Inputs: {len(sinks)}")
            else:
                self.status_label.set_text("No PipeWire ports discovered. Ensure pw-dump is available.")

        # ------------------------------------------------------------------
        def _selected_ports(self) -> Optional[Tuple[PipewirePort, PipewirePort]]:
            """Return the ports referenced by the currently selected rows."""

            src_index = self.source_dropdown.get_selected()
            sink_index = self.sink_dropdown.get_selected()
            if src_index < 0 or sink_index < 0:
                return None
            sources = self.backend.get_source_ports()
            sinks = self.backend.get_sink_ports()
            if src_index >= len(sources) or sink_index >= len(sinks):
                return None
            return sources[src_index], sinks[sink_index]

        def _handle_connect(self, *_: object) -> None:
            ports = self._selected_ports()
            if not ports:
                return
            src, sink = ports
            # Success/failure feedback goes into the header label so the user
            # has a single place to look for state updates.
            success = self.backend.connect(src, sink)
            if not success:
                self.status_label.set_text("Failed to connect ports")
            else:
                self.status_label.set_text(f"Linked {src.id} → {sink.id}")

        def _handle_disconnect(self, *_: object) -> None:
            ports = self._selected_ports()
            if not ports:
                return
            src, sink = ports
            success = self.backend.disconnect(src, sink)
            if not success:
                self.status_label.set_text("Failed to disconnect ports")
            else:
                self.status_label.set_text(f"Unlinked {src.id} → {sink.id}")


__all__ = ["RoutingView"]
