import asyncio
import os
import time
from typing import Optional

YT_COOKIE_FILE = os.path.join(os.getcwd(), "youtube_cookies.txt")


def _ensure_cookie_file():
    if os.path.isfile(YT_COOKIE_FILE):
        return
    lines = [
        "# Netscape HTTP Cookie File",
        "# https://curl.haxx.se/docs/http-cookies.html",
        "# Gerado pelo Anubis Cookie Manager - fallback para yt-dlp",
        ".youtube.com\tTRUE\t/\tTRUE\t0\tCONSENT\tYES+shp.gws-20250421-0-RC2.en+FX+126",
        ".youtube.com\tTRUE\t/\tFALSE\t0\tSOCS\tCAISNQgEEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyX3Jlc3RfcG1lZDBfMjAyNTA0MjE",
        ".google.com\tTRUE\t/\tTRUE\t0\tCONSENT\tYES+shp.gws-20250421-0-RC2.en+FX+126",
    ]
    with open(YT_COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


class YouTubeCookieManager:
    def __init__(self):
        self.po_token: Optional[str] = None
        self.visitor_data: Optional[str] = None
        self.last_refresh: float = 0
        self.refresh_interval: int = 3600
        self._task: Optional[asyncio.Task] = None
        _ensure_cookie_file()

    @property
    def has_token(self) -> bool:
        return bool(self.po_token and self.visitor_data)

    def get_ytdl_extractor_args(self) -> dict:
        args: dict = {
            'player_client': ['android', 'android_music', 'android_creator', 'web', 'web_creator'],
            'max_comments': [0],
        }
        if self.po_token:
            args['po_token'] = [self.po_token]
        if self.visitor_data:
            args['visitor_data'] = [self.visitor_data]
        return {'youtube': args}

    def get_ytdl_cookiefile(self) -> str:
        if not os.path.isfile(YT_COOKIE_FILE):
            _ensure_cookie_file()
        return YT_COOKIE_FILE

    async def refresh_from_lavalink(self, rest_uri: str, password: str, session) -> bool:
        try:
            async with session.get(
                f"{rest_uri}/youtube", headers={"Authorization": password}, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.po_token = data.get("poToken") or data.get("po_token")
                    self.visitor_data = data.get("visitorData") or data.get("visitor_data")
                    self.last_refresh = time.time()
                    if self.has_token:
                        return True
        except Exception:
            pass
        return False

    async def refresh_on_all_nodes(self, pool):
        for bot in pool.get_all_bots():
            for node in bot.music.nodes.values():
                if not node.is_available:
                    continue
                ok = await self.refresh_from_lavalink(
                    node.rest_uri, node.password, node.session
                )
                if ok:
                    await self.inject_into_node(node)
                await asyncio.sleep(2)

    async def inject_into_node(self, node) -> bool:
        if not self.has_token:
            return False
        try:
            async with node.session.post(
                url=f"{node.rest_uri}/youtube",
                json={
                    "poToken": self.po_token,
                    "visitorData": self.visitor_data,
                },
                headers={"Authorization": node.password},
                timeout=15,
            ) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        return False

    async def start_periodic_refresh(self, pool, interval: int = 3600):
        self.refresh_interval = interval
        while True:
            await asyncio.sleep(self.refresh_interval)
            try:
                await self.refresh_on_all_nodes(pool)
            except Exception:
                pass


youtube_cookie_manager = YouTubeCookieManager()
