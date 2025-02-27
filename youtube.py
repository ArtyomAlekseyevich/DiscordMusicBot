import yt_dlp
import asyncio

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'socket_timeout': 10,
    'retries': 1,
    'extract_flat': True,
}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

async def async_search_youtube(query: str):
    try:
        info_dict = await asyncio.to_thread(ytdl.extract_info, f"ytsearch5:{query}", False)
        if "entries" in info_dict and info_dict["entries"]:
            return info_dict["entries"][:5]
        else:
            return None
    except Exception as e:
        print(f"Error during YouTube search: {e}")
        return None