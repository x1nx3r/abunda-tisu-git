"""Discord embed rendering."""

from __future__ import annotations

import discord

from .models import Outcome, Reply

GREEN = 0x44FF44
YELLOW = 0xFFD000
ORANGE = 0xFF6600
RED = 0x990000
BLURPLE = 0x5865F2
GREY = 0x99AAB5

_PING_TIERS = ((50, GREEN), (100, YELLOW), (200, ORANGE))

_OUTCOME_COLORS = {
    Outcome.PLAYING: GREEN,
    Outcome.SKIPPED: BLURPLE,
    Outcome.QUEUED: BLURPLE,
    Outcome.QUEUE_INFO: BLURPLE,
    Outcome.NO_RESULTS: RED,
    Outcome.QUEUE_EMPTY: RED,
    Outcome.DISCONNECTED: GREY,
}


def ping_color(latency_ms: int) -> int:
    for threshold, color in _PING_TIERS:
        if latency_ms <= threshold:
            return color
    return RED


def ping_embed(latency_ms: int) -> discord.Embed:
    return discord.Embed(
        title="PING",
        description=(
            ":ping_pong: Pingpingpingpingping! "
            f"The ping is **{latency_ms}** milliseconds!"
        ),
        color=ping_color(latency_ms),
    )


def reply_embed(reply: Reply) -> discord.Embed:
    return discord.Embed(
        title=reply.title,
        description=reply.description,
        color=_OUTCOME_COLORS.get(reply.outcome, BLURPLE),
    )
