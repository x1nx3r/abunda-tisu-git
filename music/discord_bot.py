"""Discord adapter: commands, voice connections and event wiring."""

from __future__ import annotations

import logging
from typing import cast

import discord
import wavelink
from discord.ext import commands

from .config import Settings
from .embeds import ping_embed, reply_embed
from .models import Outcome, Reply, Track
from .search import WavelinkSearcher
from .service import MusicService
from .spotify import SpotifyResolver

log = logging.getLogger(__name__)


class NotInVoiceChannel(commands.CommandError):
    """Raised when the caller is not connected to a voice channel."""


class WavelinkTarget:
    """Adapts ``wavelink.Player`` to the service's ``PlaybackTarget`` protocol."""

    def __init__(self, player: wavelink.Player) -> None:
        self.player = player

    @property
    def playing(self) -> bool:
        return self.player.playing

    async def play(self, track: Track) -> None:
        playable = track.reference
        if not isinstance(playable, wavelink.Playable):
            raise TypeError(f"track {track.title!r} has no wavelink playable attached")
        await self.player.play(playable)

    async def stop(self) -> None:
        if self.player.playing:
            await self.player.stop()


class DiscordMusicBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, command_prefix=settings.command_prefix)

        self.settings = settings
        self.resolver: SpotifyResolver | None = None
        self.searcher = WavelinkSearcher()
        self.services: dict[int, tuple[wavelink.Player, MusicService]] = {}
        self.announce_channels: dict[int, discord.abc.Messageable] = {}

    async def on_ready(self) -> None:
        log.info("Logged in as %s (%s)", self.user, getattr(self.user, "id", "?"))

    async def setup_hook(self) -> None:
        self.resolver = SpotifyResolver(
            self.settings.spotify_client_id,
            self.settings.spotify_client_secret,
        )
        await self.add_cog(Music(self))

        node = wavelink.Node(
            uri=self.settings.lavalink_uri,
            password=self.settings.lavalink_password,
            retries=3,
        )
        try:
            await wavelink.Pool.connect(nodes=[node], client=self)
            log.info("Connected to Lavalink at %s", self.settings.lavalink_uri)
        except Exception:
            log.exception(
                "Could not connect to Lavalink at %s; music commands will fail "
                "until it is running.",
                self.settings.lavalink_uri,
            )

    def service_for(self, guild_id: int, player: wavelink.Player) -> MusicService:
        if self.resolver is None:
            raise RuntimeError("the bot has not finished starting up")

        entry = self.services.get(guild_id)
        if entry is None or entry[0] is not player:
            entry = (
                player,
                MusicService(self.resolver, self.searcher, WavelinkTarget(player)),
            )
            self.services[guild_id] = entry
        return entry[1]

    def get_service(self, guild_id: int) -> MusicService | None:
        entry = self.services.get(guild_id)
        return entry[1] if entry else None

    def pop_service(self, guild_id: int) -> MusicService | None:
        entry = self.services.pop(guild_id, None)
        return entry[1] if entry else None


class Music(commands.Cog):
    def __init__(self, bot: DiscordMusicBot) -> None:
        self.bot = bot

    async def _player(self, ctx: commands.Context) -> wavelink.Player:
        if ctx.voice_client is not None:
            return cast(wavelink.Player, ctx.voice_client)

        voice = getattr(ctx.author, "voice", None)
        channel = getattr(voice, "channel", None)
        if channel is None:
            raise NotInVoiceChannel("Join a voice channel first, then ask me again.")

        return cast(
            wavelink.Player,
            await channel.connect(cls=wavelink.Player, self_deaf=True),
        )

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        """Show the gateway latency."""
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(embed=ping_embed(latency_ms))

    @commands.command()
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str = "") -> None:
        """Search Spotify, then play the match from YouTube."""
        try:
            player = await self._player(ctx)
        except NotInVoiceChannel as exc:
            await ctx.send(str(exc))
            return

        guild = cast(discord.Guild, ctx.guild)
        service = self.bot.service_for(guild.id, player)
        self.bot.announce_channels[guild.id] = ctx.channel

        try:
            reply = await service.play(query)
        except wavelink.WavelinkException:
            log.exception("Lavalink rejected playback")
            await ctx.send("Lavalink is not available right now. Try again shortly.")
            return

        await ctx.send(embed=reply_embed(reply))

    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx: commands.Context) -> None:
        """Play the next track in the queue."""
        guild = cast(discord.Guild, ctx.guild)
        service = self.bot.get_service(guild.id)
        if service is None:
            await ctx.send("Nothing is playing.")
            return

        try:
            reply = await service.skip()
        except wavelink.WavelinkException:
            log.exception("Lavalink rejected playback")
            await ctx.send("Lavalink is not available right now. Try again shortly.")
            return

        await ctx.send(embed=reply_embed(reply))

    @commands.command()
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        """List the queued tracks."""
        guild = cast(discord.Guild, ctx.guild)
        service = self.bot.get_service(guild.id)
        reply = (
            service.queue_reply()
            if service is not None
            else Reply(Outcome.QUEUE_INFO, "Queue", "The queue is empty.")
        )
        await ctx.send(embed=reply_embed(reply))

    @commands.command()
    @commands.guild_only()
    async def disconnect(self, ctx: commands.Context) -> None:
        """Stop playing and leave the voice channel."""
        guild = cast(discord.Guild, ctx.guild)
        player = cast(wavelink.Player | None, ctx.voice_client)
        service = self.bot.pop_service(guild.id)
        self.bot.announce_channels.pop(guild.id, None)

        if service is None and player is None:
            await ctx.send("I'm not in a voice channel.")
            return

        if service is not None:
            await service.disconnect()
        if player is not None:
            await player.disconnect()

        await ctx.send("Disconnected.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload: wavelink.TrackEndEventPayload
    ) -> None:
        player = payload.player
        if player is None or payload.reason != "finished":
            return

        guild = player.guild
        if guild is None:
            return

        service = self.bot.get_service(guild.id)
        if service is None:
            return

        try:
            reply = await service.advance()
        except wavelink.WavelinkException:
            log.exception("Lavalink rejected playback")
            return

        channel = self.bot.announce_channels.get(guild.id)
        if reply is not None and channel is not None:
            await channel.send(embed=reply_embed(reply))


__all__ = ["DiscordMusicBot", "Music", "NotInVoiceChannel", "WavelinkTarget"]
