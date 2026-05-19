import asyncio
import os
import re

import disnake
import yt_dlp

from utils.music.errors import GenericError
from utils.music.models import PartialTrack

YT_COOKIE_FILE = os.path.join(os.getcwd(), "youtube_cookies.txt")


def _build_ydl_opts(cookie_file: str = "", po_token: str = "", visitor_data: str = "", proxy: str = "") -> dict:
    opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'retries': 5,
        'extract_flat': "in_playlist",
        'cachedir': "./.ytdl_cache",
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash', 'translated_subs'],
                'player_skip': ['js', 'configs', 'webpage'],
                'player_client': ['android', 'android_music', 'android_creator', 'web'],
                'max_comments': [0],
            },
            'youtubetab': {
                "skip": ["webpage"]
            }
        }
    }
    if cookie_file and os.path.isfile(cookie_file):
        opts['cookiefile'] = cookie_file
    if po_token:
        opts['extractor_args']['youtube']['po_token'] = [po_token]
    if visitor_data:
        opts['extractor_args']['youtube']['visitor_data'] = [visitor_data]
    if proxy:
        opts['proxy'] = proxy
    return opts


class YTDLTools:

    extractors = [
        {
            "name": type(e).__name__.lower(),
            "ie_key": e.ie_key(),
            "regex": e._VALID_URL,
            "age_limit": e.age_limit
        } for e in yt_dlp.list_extractors() if e._VALID_URL
    ]

    def __init__(self, cookie_file: str = "", po_token: str = "", visitor_data: str = "", proxy: str = ""):
        self._opts = _build_ydl_opts(cookie_file, po_token, visitor_data, proxy)

    def update_auth(self, cookie_file: str = "", po_token: str = "", visitor_data: str = "", proxy: str = ""):
        self._opts = _build_ydl_opts(cookie_file, po_token, visitor_data, proxy)

    def extract_info(self, url: str):
        return yt_dlp.YoutubeDL(self._opts).extract_info(url=url, download=False)

    async def get_track_info(self, url: str, user: disnake.Member = None, loop=None):

        for e in self.extractors:
            if not (matches := re.compile(e['regex']).match(url)) or not matches.groups():
                continue

            if any(ee in e["name"] for ee in ["youtube", "soundcloud"]):
                continue

            if e["age_limit"] > 17 and e["ie_key"] != "Twitter":
                raise GenericError("**Este link contém conteúdo para maiores de 18 anos!**")

            if not loop:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

            data = await loop.run_in_executor(None, self.extract_info, url)

            try:
                if data["_type"] == "playlist":
                    raise GenericError("**No momento não há suporte para playlists com o link fornecido...**")
            except KeyError:
                pass

            try:
                entrie = data["entries"][0]
            except KeyError:
                entrie = data

            try:
                if entrie["age_limit"] > 17:
                    raise GenericError("**Este link contém conteúdo para maiores de 18 anos!**")
            except KeyError:
                pass

            t = PartialTrack(
                uri=entrie.get("webpage_url") or url,
                title=entrie["title"],
                author=entrie["uploader"],
                thumb=entrie["thumbnail"],
                duration=entrie["duration"] * 1000,
                requester=user.id,
                source_name=entrie["extractor"],
            )

            t.info.update({
                "search_uri": entrie["url"],
                "authors": entrie["uploader"]
            })

            return [t]


if __name__ == "__main__":
    ydl = YTDLTools()
    url = "https://www.youtube.com/channel/UC9AiU8Srqw7iPu3UcR9IJ8g"
    for e in ydl.extractors:
        if e['ie_key'] == "Generic":
            continue
        a = re.compile(e['regex']).match(url)
        if a:
            print(e['ie_key'], e['name'])
