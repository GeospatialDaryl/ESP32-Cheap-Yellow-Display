"""Interaction helpers for the PipeWire command-line tools."""
from __future__ import annotations

import json
import subprocess
from typing import Dict, List, Optional

from .models import PipewireNode, PipewirePort


class PipewireBackend:
    """Expose discovery, routing, and volume helpers for PipeWire.

    The class isolates all subprocess invocations so that the remainder of the
    codebase can focus on GUI logic.  It also caches discovery information in
    memory; recomputing the cache is cheap enough that the public methods
    simply call :meth:`refresh` when necessary instead of maintaining a
    long-lived background thread.
    """

    def __init__(self) -> None:
        # Discovery results are cached so that UI refreshes can reuse the same
        # objects without continuously shelling out to ``pw-dump``.
        self.nodes: Dict[int, PipewireNode] = {}
        self.ports: Dict[int, PipewirePort] = {}

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Refresh the internal cache using ``pw-dump``."""

        try:
            dump = subprocess.check_output(["pw-dump"], text=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # ``pw-dump`` may be unavailable inside CI environments.  The
            # method fails silently so the GUI can show an empty state instead
            # of crashing.
            return

        try:
            data = json.loads(dump)
        except json.JSONDecodeError:
            return

        nodes: Dict[int, PipewireNode] = {}
        ports: Dict[int, PipewirePort] = {}

        for obj in data:
            obj_id = obj.get("id")
            if obj_id is None:
                continue
            info = obj.get("info", {})
            props = obj.get("props", {})
            obj_type = obj.get("type")

            if obj_type == "PipeWire:Interface:Node":
                name = props.get("node.description") or props.get("node.name") or info.get("name") or f"node-{obj_id}"
                media_class = props.get("media.class", "")
                nodes[obj_id] = PipewireNode(id=obj_id, name=name, media_class=media_class)
            elif obj_type == "PipeWire:Interface:Port":
                node_id = info.get("node.id") or props.get("node.id")
                if node_id is None:
                    continue
                node_name = props.get("node.name") or props.get("port.alias") or props.get("port.name") or f"node-{node_id}"
                direction_raw = info.get("direction") or props.get("port.direction")
                direction = self._normalize_direction(direction_raw)
                port_name = props.get("port.alias") or props.get("port.name") or info.get("name") or f"port-{obj_id}"
                ports[obj_id] = PipewirePort(
                    id=obj_id,
                    name=port_name,
                    direction=direction,
                    node_id=node_id,
                    node_name=node_name,
                )

        # Attach ports to their respective nodes so the UI can avoid repeated
        # lookups and simply walk the already filtered collections.
        for port in ports.values():
            node = nodes.get(port.node_id)
            if node is None:
                continue
            if port.direction == "output":
                node.outputs.append(port)
            else:
                node.inputs.append(port)

        self.nodes = nodes
        self.ports = ports

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_direction(direction: object) -> str:
        """Translate PipeWire direction values into ``"input"`` or ``"output"``."""

        if isinstance(direction, str):
            # PipeWire occasionally returns short-hand strings; normalizing to
            # lower-case allows us to cover every variant with a tiny lookup.
            normalized = direction.lower()
            if normalized in {"in", "input"}:
                return "input"
            if normalized in {"out", "output"}:
                return "output"
        if isinstance(direction, int):
            return "input" if direction else "output"
        return "input"

    # ------------------------------------------------------------------
    def get_source_ports(self) -> List[PipewirePort]:
        """Return all output ports sorted by node and port name."""

        return sorted(
            (p for p in self.ports.values() if p.direction == "output"),
            key=lambda p: (p.node_name, p.name),
        )

    def get_sink_ports(self) -> List[PipewirePort]:
        """Return all input ports sorted by node and port name."""

        return sorted(
            (p for p in self.ports.values() if p.direction == "input"),
            key=lambda p: (p.node_name, p.name),
        )

    def get_audio_sinks(self) -> List[PipewireNode]:
        """Return nodes that act as audio sinks sorted alphabetically."""

        return sorted((n for n in self.nodes.values() if n.is_audio_sink), key=lambda n: n.name.lower())

    # ------------------------------------------------------------------
    def connect(self, src_port: PipewirePort, dst_port: PipewirePort) -> bool:
        """Link two ports using ``pw-link``."""

        try:
            subprocess.check_call(["pw-link", str(src_port.id), str(dst_port.id)])
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
        return True

    def disconnect(self, src_port: PipewirePort, dst_port: PipewirePort) -> bool:
        """Unlink two ports using ``pw-link -d``."""

        try:
            subprocess.check_call(["pw-link", "-d", str(src_port.id), str(dst_port.id)])
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
        return True

    # ------------------------------------------------------------------
    def get_volume(self, node_id: int) -> Optional[float]:
        """Return the node volume reported by ``wpctl``."""

        try:
            out = subprocess.check_output(["wpctl", "get-volume", str(node_id)], text=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None
        # ``wpctl get-volume`` returns strings such as ``"Volume: 0.75"``; we
        # therefore parse every token until we encounter a float.
        parts = out.strip().split()
        for token in parts:
            try:
                return float(token)
            except ValueError:
                continue
        return None

    def set_volume(self, node_id: int, value: float) -> bool:
        """Update the node volume using ``wpctl`` with clipping protection."""

        # Volumes above ``1.0`` boost the signal.  We allow modest boosts up to
        # ``1.5`` but clamp everything else to avoid accidental clipping from
        # MIDI inputs.
        clamped = max(0.0, min(1.5, value))
        try:
            subprocess.check_call(["wpctl", "set-volume", str(node_id), f"{clamped:.3f}"])
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
        return True


__all__ = ["PipewireBackend"]
