import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
import os
from music import Music
from utils import format_duration
from spotify import is_spotify_link, process_spotify_link
from youtube import async_search_youtube

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize music handler
music_handler = Music()

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    try:
        guild_id = 1208253308582502500  # Replace with your server's ID
        guild = discord.Object(id=guild_id)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) for guild {guild_id}.")
    except Exception as e:
        print(e)

@bot.tree.command(name="play", description="Play a song from YouTube or Spotify, or search for one")
async def play(interaction: discord.Interaction, query: str):
    await music_handler.play(interaction, query)

@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    await music_handler.skip(interaction)

@bot.tree.command(name="queue", description="Show the current song queue")
async def queue_command(interaction: discord.Interaction):
    await music_handler.show_queue(interaction)

@bot.tree.command(name="stop", description="Stop the music and disconnect")
async def stop(interaction: discord.Interaction):
    await music_handler.stop(interaction)

@bot.tree.command(name="define", description="Get the Urban Dictionary definition for a word")
async def define(interaction: discord.Interaction, word: str):
    response = requests.get(f"https://api.urbandictionary.com/v0/define?term={word}")
    data = response.json()

    if data['list']:
        definition = data['list'][0]['definition']
        await interaction.response.send_message(f"Definition of {word}: {definition}")
    else:
        await interaction.response.send_message(f"No definition found for {word}.")

# Handling disconnection errors
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is None and before.channel is not None:
        if before.channel.guild.voice_client:
            await before.channel.guild.voice_client.disconnect()
            print("Disconnected from the voice channel.")

bot.run(DISCORD_BOT_TOKEN)