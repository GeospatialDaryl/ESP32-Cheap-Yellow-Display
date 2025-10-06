"""Executable entry point for the PipeWire mixer."""
from __future__ import annotations

import sys
from typing import Iterable, Optional

from .environment import Adw, Gio, Gtk


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Validate dependencies and dispatch to the GTK application."""

    # Dependency validation happens here to keep :mod:`app` lean and focused on
    # UI composition.
    if Gtk is None or Adw is None or Gio is None:
        sys.stderr.write("GTK/libadwaita not available. Install python3-gi and libadwaita bindings.\n")
        return 1
    # Importing here prevents ``Gtk`` dependent modules from loading before we
    # validate the environment.
    from .app import run_application

    return run_application(argv or sys.argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
