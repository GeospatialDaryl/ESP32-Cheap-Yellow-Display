# Pipewire Mixer

This directory contains a proof-of-concept GNOME/GTK application that wraps common
PipeWire command line tooling to provide a lightweight patch bay with integrated
volume faders and MIDI controller support.  The implementation is intentionally
self-contained and avoids any bespoke PipeWire bindings, making it suitable for
quick experimentation on Debian-based distributions.

The application takes inspiration from the routing workflow provided by
[`qpwgraph`](https://github.com/rncbc/qpwgraph) while adding a dedicated
"Mix" tab that exposes faders for every detected audio sink.  Each fader can be
mapped to an external MIDI channel/CC pair, allowing hardware controllers to
manipulate PipeWire volumes.

## Architecture

- `environment.py` encapsulates optional dependencies (GTK/libadwaita and MIDI)
  so the rest of the codebase can assume their presence.
- `backend.py` and `models.py` provide a thin abstraction over PipeWire's
  command-line tools and graph data.
- `ui/` hosts reusable GTK widgets for the routing and mixing tabs.
- `app.py` wires everything together using libadwaita conventions, while
  `main.py` stays responsible for dependency validation.

## Running

```bash
python3 -m Projects.PipewireMixer.main
```

Dependencies:

- Python 3.10+
- `python3-gi` / GTK 4
- PipeWire command line tools (`pw-dump`, `pw-link`, `wpctl`)
- Optional: [`mido`](https://mido.readthedocs.io/) with the `python-rtmidi` backend
  for MIDI controller integration

The program degrades gracefully if either GTK or the MIDI dependencies are
missing, providing helpful error messages when executed in such environments.
