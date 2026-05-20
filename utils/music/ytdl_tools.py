import asyncio
import logging
import os
import re
from typing import Optional

import disnake
import yt_dlp

from utils.music.errors import GenericError
from utils.music.models import PartialTrack, PartialPlaylist

logger = logging.getLogger("ytdl_tools")

YT_USER_COOKIE_FILE = os.path.join(os.getcwd(), "youtube_cookies_user.txt")

PLAYER_CLIENTS = [
    ['android', 'android_music', 'android_creator', 'web', 'web_creator', 'web_safari'],
    ['android', 'android_music', 'android_creator', 'web', 'web_safari'],
    ['android', 'android_music', 'android_creator'],
    ['android', 'android_music', 'web'],
    ['android', 'web'],
    ['android', 'android_music'],
    ['android'],
    ['android_music', 'android_creator'],
    ['web', 'web_safari'],
    ['web'],
]


def _get_ydl_opts(
    player_clients: list = None,
    extract_flat: bool = False,
    noplaylist: bool = True,
    cookiefile: str = "",
    proxy: str = "",
) -> dict:
    opts = {
        'format': 'bestaudio/best',
        'noplaylist': noplaylist,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'retries': 5,
        'extract_flat': "in_playlist" if extract_flat else False,
        'cachedir': "./.ytdl_cache",
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash', 'translated_subs'],
                'player_skip': ['js', 'configs', 'webpage'],
                'player_client': player_clients or ['android', 'android_music'],
                'max_comments': [0],
            },
        }
    }
    if cookiefile and os.path.isfile(cookiefile):
        opts['cookiefile'] = cookiefile
    if proxy:
        opts['proxy'] = proxy
    return opts


def _extract_url_from_result(raw: dict) -> Optional[str]:
    url = raw.get('url') or raw.get('webpage_url')
    if url:
        return url
    for rf in raw.get('requested_formats') or []:
        url = rf.get('url')
        if url:
            return url
    for fmt in raw.get('formats') or []:
        url = fmt.get('url')
        if url:
            return url
    return None


async def ytdl_extract_info(
    url: str,
    loop: asyncio.AbstractEventLoop,
    noplaylist: bool = True,
    cookiefile: str = "",
    proxy: str = "",
) -> dict:
    last_error = None
    for clients in PLAYER_CLIENTS:
        try:
            opts = _get_ydl_opts(
                player_clients=clients,
                noplaylist=noplaylist,
                cookiefile=cookiefile,
                proxy=proxy,
            )
            raw = await loop.run_in_executor(
                None, lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=False)
            )
            if raw:
                return raw
        except Exception as e:
            last_error = e
            logger.debug("yt-dlp clients=%s falhou: %s", clients, e)
            continue
    if last_error:
        raise last_error
    return {}


async def ytdl_extract_track(
    url: str,
    requester: int,
    loop: asyncio.AbstractEventLoop,
    cookiefile: str = "",
    proxy: str = "",
) -> list:
    raw = await ytdl_extract_info(url, loop, noplaylist=True, cookiefile=cookiefile, proxy=proxy)
    if not raw:
        raise GenericError("**Não foi possível extrair informações do vídeo.**")

    audio_url = _extract_url_from_result(raw)
    if not audio_url:
        # Last resort: try requesting just the URL directly
        opts = _get_ydl_opts(player_clients=['android'], noplaylist=False, cookiefile=cookiefile, proxy=proxy)
        opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
        raw2 = await loop.run_in_executor(
            None, lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=False)
        )
        audio_url = _extract_url_from_result(raw2)
        if not audio_url:
            raise GenericError("**Não foi possível obter URL de áudio deste vídeo.**")

    t = PartialTrack(
        uri=audio_url,
        title=raw.get('title', 'Unknown'),
        author=raw.get('uploader', 'Unknown'),
        thumb=raw.get('thumbnail', ''),
        duration=(raw.get('duration') or 0) * 1000,
        requester=requester,
        source_name="http",
    )
    t.info["isSeekable"] = True
    return [t]


async def ytdl_search(
    query: str,
    requester: int,
    loop: asyncio.AbstractEventLoop,
    max_results: int = 10,
    cookiefile: str = "",
    proxy: str = "",
) -> list:
    search_query = f"ytsearch{max_results}:{query}"
    raw = await ytdl_extract_info(search_query, loop, noplaylist=True, cookiefile=cookiefile, proxy=proxy)
    if not raw:
        raise GenericError("**Nenhum resultado encontrado para a busca.**")

    entries = raw.get('entries') or []
    if not entries:
        raise GenericError("**Nenhum resultado encontrado para a busca.**")

    tracks = []
    for entry in entries[:max_results]:
        video_url = entry.get('webpage_url') or entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id', '')}"
        tracks.append(PartialTrack(
            uri=video_url,
            title=entry.get('title', 'Unknown'),
            author=entry.get('uploader', 'Unknown'),
            thumb=entry.get('thumbnail', ''),
            duration=(entry.get('duration') or 0) * 1000,
            requester=requester,
            source_name="youtube",
            identifier=entry.get('id', ''),
        ))
    return tracks


async def ytdl_extract_playlist(
    url: str,
    requester: int,
    loop: asyncio.AbstractEventLoop,
    cookiefile: str = "",
    proxy: str = "",
):
    try:
        opts = _get_ydl_opts(
            player_clients=['android', 'android_music'],
            noplaylist=False,
            extract_flat=True,
            cookiefile=cookiefile,
            proxy=proxy,
        )
        raw = await loop.run_in_executor(
            None, lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=False)
        )
    except Exception as e:
        # Retry with different clients
        for clients in PLAYER_CLIENTS[:3]:
            try:
                opts = _get_ydl_opts(
                    player_clients=clients,
                    noplaylist=False,
                    extract_flat=True,
                    cookiefile=cookiefile,
                    proxy=proxy,
                )
                raw = await loop.run_in_executor(
                    None, lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=False)
                )
                break
            except Exception:
                continue
        else:
            raise GenericError(f"**Não foi possível carregar a playlist:** {e}")

    if not raw or raw.get('_type') != 'playlist':
        raise GenericError("**O link informado não é uma playlist válida.**")

    entries = raw.get('entries') or []
    if not entries:
        raise GenericError("**A playlist está vazia ou é privada.**")

    playlist = PartialPlaylist(
        data={"playlistInfo": {"name": raw.get('title', 'Playlist'), "selectedTrack": -1}},
        url=url,
    )

    for entry in entries:
        video_url = entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id', '')}"
        track = PartialTrack(
            uri=video_url,
            title=entry.get('title', 'Unknown'),
            author=entry.get('uploader', 'Channel') if entry.get('uploader') else 'Unknown',
            thumb=entry.get('thumbnail', ''),
            duration=(entry.get('duration') or 0) * 1000,
            requester=requester,
            source_name="youtube",
            identifier=entry.get('id', ''),
            playlist=playlist,
        )
        playlist.tracks.append(track)

    return playlist


class YTDLTools:

    extractors = [
        {
            "name": type(e).__name__.lower(),
            "ie_key": e.ie_key(),
            "regex": e._VALID_URL,
            "age_limit": e.age_limit
        } for e in yt_dlp.list_extractors() if e._VALID_URL
    ]

    def __init__(self, cookiefile: str = "", proxy: str = ""):
        self._cookiefile = cookiefile or (YT_USER_COOKIE_FILE if os.path.isfile(YT_USER_COOKIE_FILE) else "")
        self._proxy = proxy

    async def extract_youtube_track(self, url: str, requester: int, loop=None) -> list:
        if not loop:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        return await ytdl_extract_track(url, requester, loop, cookiefile=self._cookiefile, proxy=self._proxy)

    async def extract_youtube_playlist(self, url: str, requester: int, loop=None):
        if not loop:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        return await ytdl_extract_playlist(url, requester, loop, cookiefile=self._cookiefile, proxy=self._proxy)

    async def search_youtube(self, query: str, requester: int, max_results=10, loop=None) -> list:
        if not loop:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        return await ytdl_search(query, requester, loop, max_results=max_results, cookiefile=self._cookiefile, proxy=self._proxy)

    def extract_info(self, url: str):
        opts = _get_ydl_opts(player_clients=['android', 'android_music'], cookiefile=self._cookiefile, proxy=self._proxy)
        return yt_dlp.YoutubeDL(opts).extract_info(url=url, download=False)

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

    async def extract_info_async(self, url: str, loop=None) -> dict:
        if not loop:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        return await ytdl_extract_info(url, loop, noplaylist=False, cookiefile=self._cookiefile, proxy=self._proxy)
