import discord
import asyncio
from youtube import async_search_youtube
from utils import format_duration
from spotify import is_spotify_link, process_spotify_link
import yt_dlp

class Music:
    def __init__(self):
        self.queue = []
        self.last_text_channel = None
        self.last_song_title = None
        self.YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'socket_timeout': 10,
            'retries': 1,
            'extract_flat': True,
        }
        self.ytdl = yt_dlp.YoutubeDL(self.YTDL_OPTIONS)

    async def play(self, interaction, query):
        self.last_text_channel = interaction.channel
        await interaction.response.defer()

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("You must be in a voice channel to use this command.", ephemeral=True)
            return

        voice_channel = interaction.user.voice.channel

        if interaction.guild.voice_client is None:
            await voice_channel.connect()
        elif interaction.guild.voice_client.channel != voice_channel:
            await interaction.guild.voice_client.move_to(voice_channel)

        if is_spotify_link(query):
            new_query = process_spotify_link(query)
            if new_query:
                query = new_query
            else:
                await interaction.followup.send("Failed to process the Spotify link.", ephemeral=True)
                return

        results = await async_search_youtube(query)
        if not results:
            await interaction.followup.send("No results found.", ephemeral=True)
            return

        result_message = "Here are the top results:\n"
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']

        for idx, result in enumerate(results):
            duration_seconds = result.get("duration", 0)
            duration_str = format_duration(duration_seconds)
            result_message += f"{idx+1}. {result['title']} - {duration_str}\n"

        selection_message = await interaction.followup.send(result_message)

        for i in range(len(results)):
            await selection_message.add_reaction(number_emojis[i])

        def check(reaction, user):
            return (
                user == interaction.user and
                reaction.message.id == selection_message.id and
                reaction.emoji in number_emojis
            )

        try:
            reaction, user = await interaction.client.wait_for('reaction_add', timeout=30.0, check=check)
            selected_index = number_emojis.index(reaction.emoji)
            selected_result = results[selected_index]
            await selection_message.delete()
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to select a track.", ephemeral=True)
            return

        video_id = selected_result.get('id')
        if not video_id:
            await interaction.followup.send("Could not retrieve video id.", ephemeral=True)
            return
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            full_ytdl = yt_dlp.YoutubeDL({**self.YTDL_OPTIONS, 'extract_flat': False})
            full_info = await asyncio.to_thread(full_ytdl.extract_info, video_url, False)
        except Exception as e:
            await interaction.followup.send("Failed to get full video info.", ephemeral=True)
            return

        source = None
        if "url" in full_info:
            source = full_info["url"]
        elif "formats" in full_info and full_info["formats"]:
            source = full_info["formats"][0].get("url")
        if not source:
            await interaction.followup.send("Could not extract a stream URL.", ephemeral=True)
            return

        title = full_info.get("title", selected_result.get("title", "Unknown"))
        duration_seconds = full_info.get("duration", 0)
        self.queue.append({'source': source, 'title': title, 'duration': duration_seconds})

        if not interaction.guild.voice_client.is_playing():
            await self.play_next_song(interaction.guild.voice_client)

        await interaction.followup.send(f"Added to queue: **{title}** - {format_duration(duration_seconds)} 🎶")

    async def skip(self, interaction):
        vc = interaction.guild.voice_client
        if vc is None or not await self.check_connection(vc):
            await interaction.response.send_message("There is no song playing or I am disconnected.", ephemeral=True)
            return
        vc.stop()
        await interaction.response.send_message("Skipped the current song. ⏩")

    async def show_queue(self, interaction):
        if not self.queue:
            await interaction.response.send_message("The queue is empty.", ephemeral=True)
            return
        queue_list = "\n".join([f"{idx + 1}. {song['title']} - {format_duration(song['duration'])}" for idx, song in enumerate(self.queue)])
        await interaction.response.send_message(f"Current queue:\n{queue_list}")

    async def stop(self, interaction):
        vc = interaction.guild.voice_client
        if vc is None:
            await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)
            return
        vc.stop()
        self.queue.clear()
        await vc.disconnect()
        await interaction.response.send_message("Stopped playing and disconnected. 🎵")

    async def play_next_song(self, vc):
        if not self.queue:
            await asyncio.sleep(300)  # Wait 5 minutes before disconnecting.
            if not self.queue:
                await vc.disconnect()
                return
        else:
            song = self.queue.pop(0)
            self.last_song_title = song['title']  # Update last played track
            duration_str = format_duration(song['duration'])

            ffmpeg_options = {
                'options': (
                    '-vn '
                    '-reconnect 1 '
                    '-reconnect_streamed 1 '
                    '-reconnect_delay_max 5 '
                    '-af aresample=async=1 '
                    '-threads 2 '
                    '-loglevel panic'
                )
            }

            try:
                vc.play(discord.FFmpegPCMAudio(song['source'], **ffmpeg_options),
                        after=lambda e: self.handle_song_end(vc, e))
                if self.last_text_channel is not None:
                    await self.last_text_channel.send(f'Now playing "{song["title"]}" - {duration_str} 🎶')
            except Exception as e:
                print(f"Error while trying to play the song: {e}")
                await vc.disconnect()
                if self.last_text_channel is not None:
                    await self.last_text_channel.send(f"Failed to play the song due to an error: {e}", ephemeral=True)

    def handle_song_end(self, vc, e):
        asyncio.run_coroutine_threadsafe(self.play_next_song(vc), vc.loop)

    async def check_connection(self, vc):
        if vc.is_playing() or vc.is_paused():
            return True
        else:
            await vc.disconnect()
            return False