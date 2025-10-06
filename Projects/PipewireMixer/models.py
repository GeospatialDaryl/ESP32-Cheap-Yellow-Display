"""Lightweight data structures describing PipeWire topology."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class PipewirePort:
    """Represents a single PipeWire port."""

    id: int
    name: str
    direction: str
    node_id: int
    node_name: str

    @property
    def display_name(self) -> str:
        """Return a human readable port label used in drop-down widgets."""

        return f"{self.node_name} · {self.name} ({self.id})"


@dataclass(slots=True)
class PipewireNode:
    """Represents a PipeWire node with its associated ports."""

    id: int
    name: str
    media_class: str
    inputs: List[PipewirePort] = field(default_factory=list)
    outputs: List[PipewirePort] = field(default_factory=list)

    @property
    def is_audio_sink(self) -> bool:
        """Return ``True`` when the node represents an audio sink."""

        return self.media_class.startswith("Audio/Sink") or self.media_class.startswith("Stream/Output")


__all__ = ["PipewirePort", "PipewireNode"]
