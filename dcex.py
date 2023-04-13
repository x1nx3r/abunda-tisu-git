import discord
import wavelink
from discord.ext import commands
from wavelink.ext import spotify


class Bot(commands.Bot):

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents, command_prefix='?')

    async def on_ready(self) -> None:
        print(f'Logged in {self.user} | {self.user.id}')

    async def setup_hook(self) -> None:
        # Wavelink 2.0 has made connecting Nodes easier... Simply create each Node
        # and pass it to NodePool.connect with the client/bot.
        # Fill your Spotify API details and pass it to connect.
        sc = spotify.SpotifyClient(
            client_id='ID_CLIENT',
            client_secret='SECRET_CLIENT'
        )
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='youshallnot')
        await wavelink.NodePool.connect(client=self, nodes=[node], spotify=sc)
        print('Connected to Node')
        print('---------')

bot = Bot()


@bot.command()
async def play(ctx: commands.Context, *, search: str) -> None:
    """Simple play command that accepts a Spotify song URL.
    This command enables AutoPlay. AutoPlay finds songs automatically when used with Spotify.
    Tracks added to the Queue will be played in front (Before) of those added by AutoPlay.
    """

    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    # Check the search to see if it matches a valid Spotify URL...
    decoded = spotify.decode_url(search)
    if not decoded or decoded['type'] is not spotify.SpotifySearchType.track:
        await ctx.send('Only Spotify Track URLs are valid.')
        return

    # Set autoplay to True. This can be disabled at anytime...
    vc.autoplay = True
    track = await spotify.SpotifyTrack.search(search)

    # IF the player is not playing immediately play the song...
    # otherwise put it in the queue...
    if not vc.is_playing():
        await vc.play(track, populate=True)
    else:
        await vc.queue.put_wait(track)

@bot.command()
async def playyt(ctx: commands.Context, *, search: str) -> None:
    """Simple play command."""

    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    track = await wavelink.YouTubeTrack.search(search, return_first=True)
    await vc.play(track)


@bot.command()
async def disconnect(ctx: commands.Context) -> None:
    """Simple disconnect command.
    This command assumes there is a currently connected Player.
    """
    vc: wavelink.Player = ctx.voice_client
    await vc.disconnect()


bot.run('TOKEN')