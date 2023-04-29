import discord
import wavelink
import os
import def_func
from dotenv import load_dotenv
from discord.ext import commands
from wavelink.ext import spotify

load_dotenv('tokens.env')

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

##
#A fancy ping command
##
@bot.command()
async def ping(ctx):
    if round(bot.latency * 1000) <= 50:
        embed=discord.Embed(title="PING", description=f":ping_pong: Pingpingpingpingping! The ping is **{round(bot.latency *1000)}** milliseconds!", color=0x44ff44)
    elif round(bot.latency * 1000) <= 100:
        embed=discord.Embed(title="PING", description=f":ping_pong: Pingpingpingpingping! The ping is **{round(bot.latency *1000)}** milliseconds!", color=0xffd000)
    elif round(bot.latency * 1000) <= 200:
        embed=discord.Embed(title="PING", description=f":ping_pong: Pingpingpingpingping! The ping is **{round(bot.latency *1000)}** milliseconds!", color=0xff6600)
    else:
        embed=discord.Embed(title="PING", description=f":ping_pong: Pingpingpingpingping! The ping is **{round(bot.latency *1000)}** milliseconds!", color=0x990000)
    await ctx.send(embed=embed)


##
#  this is a play command, 
# User prompts a command >> fetch spotify api track info >> get the song name and input it to play so it searches and plays from youtube.
##
@bot.command()
async def play(ctx: commands.Context, *, search: str) -> None:
    """Simple play command."""

    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    info = await def_func.get_track_info(search)

    track = await wavelink.YouTubeTrack.search(info[0], return_first=True)
    await ctx.send(f'Now playing: {info[0]} by {info[1]} from the album {info[2]}')
    await vc.play(track)


@bot.command()
async def disconnect(ctx: commands.Context) -> None:
    """Simple disconnect command.
    This command assumes there is a currently connected Player.
    """
    vc: wavelink.Player = ctx.voice_client
    await vc.disconnect()

token=os.getenv('DISCORD_TOKEN')
bot.run(token)