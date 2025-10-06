"""Application bootstrap for the PipeWire mixer."""
from __future__ import annotations

from typing import Iterable, Optional

from .backend import PipewireBackend
from .environment import Adw, Gio, Gtk
from .midi import MidiController
from .ui import MixView, RoutingView


class MixerWindow(Adw.ApplicationWindow):
    """Main application window containing the routing and mix tabs."""

    def __init__(self, app: Gtk.Application, backend: PipewireBackend, midi: MidiController):
        super().__init__(application=app)
        self.set_title("PipeWire Mixer")
        self.set_default_size(900, 600)

        notebook = Gtk.Notebook()
        # Tabs keep routing and mixing concerns separate while sharing the same
        # backend instances so selections remain in sync across the UI.
        notebook.append_page(RoutingView(backend), Gtk.Label(label="Routing"))
        notebook.append_page(MixView(backend, midi), Gtk.Label(label="Mix"))

        self.set_content(notebook)


class MixerApplication(Adw.Application):
    """GTK application entry point."""

    def __init__(self) -> None:
        super().__init__(application_id="com.example.PipewireMixer", flags=Gio.ApplicationFlags.FLAGS_NONE)
        # Singletons live on the application object so they can be reused across
        # multiple windows in the future without additional plumbing.
        self.backend = PipewireBackend()
        self.midi = MidiController()

    def do_activate(self) -> None:  # type: ignore[override]
        window = self.props.active_window
        if window is None:
            window = MixerWindow(self, self.backend, self.midi)
        window.present()


def run_application(argv: Optional[Iterable[str]] = None) -> int:
    """Run the GTK application and return its exit status."""

    app = MixerApplication()
    return app.run(list(argv or []))


__all__ = ["MixerApplication", "MixerWindow", "run_application"]
