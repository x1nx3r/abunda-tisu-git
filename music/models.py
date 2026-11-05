"""Transport-free values shared by the service, the adapter and the fakes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Outcome(str, Enum):
    PLAYING = "playing"
    QUEUED = "queued"
    NO_RESULTS = "no-results"
    SKIPPED = "skipped"
    QUEUE_INFO = "queue-info"
    QUEUE_EMPTY = "queue-empty"
    DISCONNECTED = "disconnected"


@dataclass(frozen=True, slots=True)
class TrackRequest:
    """What the metadata provider knows about the song the user asked for."""

    title: str
    artist: str
    album: str


@dataclass(frozen=True, slots=True)
class Track:
    """A playable result.

    ``reference`` holds the backend's own object (a ``wavelink.Playable`` in
    production); the service never looks inside it.
    """

    title: str
    author: str
    uri: str
    reference: object | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class Reply:
    outcome: Outcome
    title: str
    description: str
