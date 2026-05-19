import asyncio
import logging
import os
import time
from typing import Optional

logger = logging.getLogger("youtube_cookies")

YT_COOKIE_FILE = os.path.join(os.getcwd(), "youtube_cookies.txt")
YT_USER_COOKIE_FILE = os.path.join(os.getcwd(), "youtube_cookies_user.txt")


def _ensure_cookie_file(visitor_data: str = "", po_token: str = ""):
    if os.path.isfile(YT_USER_COOKIE_FILE):
        logger.info("Usando cookies fornecidos pelo usuario: %s", YT_USER_COOKIE_FILE)
        return
    now_ts = int(time.time())
    expiry = now_ts + 86400 * 365
    lines = [
        "# Netscape HTTP Cookie File",
        "# Gerado pelo Anubis Cookie Manager",
        ".youtube.com\tTRUE\t/\tTRUE\t{expiry}\tCONSENT\tYES+shp.gws-20250421-0-RC2.en+FX+126".format(expiry=expiry),
        ".youtube.com\tTRUE\t/\tFALSE\t{expiry}\tSOCS\tCAISNQgEEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyX3Jlc3RfcG1lZDBfMjAyNTA0MjE".format(expiry=expiry),
        ".youtube.com\tTRUE\t/\tFALSE\t{expiry}\t__Secure-3PSIDCC\t".format(expiry=expiry),
        ".youtube.com\tTRUE\t/\tFALSE\t{expiry}\t__Secure-3PAPISID\t".format(expiry=expiry),
        ".youtube.com\tTRUE\t/\tFALSE\t{expiry}\t__Secure-3PSID\t".format(expiry=expiry),
        ".google.com\tTRUE\t/\tTRUE\t{expiry}\tCONSENT\tYES+shp.gws-20250421-0-RC2.en+FX+126".format(expiry=expiry),
    ]
    if visitor_data:
        lines.append(f".youtube.com\tTRUE\t/\tFALSE\t{expiry}\tVISITOR_INFO1_LIVE\t{visitor_data}")
    with open(YT_COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    logger.debug("Arquivo de cookies atualizado: %s", YT_COOKIE_FILE)


class YouTubeCookieManager:
    def __init__(self):
        self.po_token: Optional[str] = None
        self.visitor_data: Optional[str] = None
        self.last_refresh: float = 0
        self.refresh_interval: int = 3600
        self._task: Optional[asyncio.Task] = None
        self._yt_proxy: Optional[str] = None
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
        if os.path.isfile(YT_USER_COOKIE_FILE):
            return YT_USER_COOKIE_FILE
        if not os.path.isfile(YT_COOKIE_FILE):
            _ensure_cookie_file(self.visitor_data or "", self.po_token or "")
        return YT_COOKIE_FILE

    def get_ytdl_proxy(self) -> Optional[str]:
        return self._yt_proxy

    def set_proxy(self, proxy_url: Optional[str]):
        self._yt_proxy = proxy_url
        if proxy_url:
            logger.info("Proxy YouTube configurado: %s", proxy_url)

    def load_user_cookies(self, filepath: str) -> bool:
        if not os.path.isfile(filepath):
            logger.warning("Arquivo de cookies do usuario nao encontrado: %s", filepath)
            return False
        import shutil
        shutil.copy2(filepath, YT_USER_COOKIE_FILE)
        logger.info("Cookies do usuario carregados de: %s", filepath)
        return True

    async def generate_via_browser(self, headless: bool = True, timeout: int = 30) -> bool:
        try:
            from .youtube_trusted_session_generator import YouTubeSessionGenerator
            gen = YouTubeSessionGenerator()
            data = await gen.generate(headless=headless, timeout=timeout)
            if gen.success and data:
                self.visitor_data = data.get("visitor_data") or self.visitor_data
                self.po_token = data.get("po_token") or self.po_token
                self.last_refresh = time.time()
                _ensure_cookie_file(self.visitor_data or "", self.po_token or "")
                return True
            return False
        except ImportError:
            logger.info("youtube_trusted_session_generator nao disponivel")
            return False
        except Exception as e:
            logger.warning("Falha ao gerar sessao via browser: %s", e)
            return False

    async def refresh_token_any(self, pool) -> bool:
        if self.has_token:
            return True

        try:
            from .youtube_trusted_session_generator import YouTubeSessionGenerator
            gen = YouTubeSessionGenerator()

            data = await gen.generate_via_http(timeout=15)
            if data:
                self.visitor_data = data.get("visitor_data") or self.visitor_data
                self.po_token = data.get("po_token") or self.po_token
                self.last_refresh = time.time()
                _ensure_cookie_file(self.visitor_data or "", self.po_token or "")
                logger.info("Token YouTube renovado via HTTP direto")
                await self.inject_into_all_nodes(pool)
                return True
        except Exception:
            pass

        for bot in pool.get_all_bots():
            for node in bot.music.nodes.values():
                if not node.is_available:
                    continue
                ok = await self.refresh_from_lavalink(node.rest_uri, node.password, node.session)
                if ok:
                    await self.inject_into_node(node)
                    return True
                await asyncio.sleep(1)

        return False

    async def inject_into_all_nodes(self, pool):
        for bot in pool.get_all_bots():
            for node in bot.music.nodes.values():
                if node.is_available:
                    await self.inject_into_node(node)

    async def refresh_from_lavalink(self, rest_uri: str, password: str, session) -> bool:
        try:
            async with session.get(
                f"{rest_uri}/youtube", headers={"Authorization": password}, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.po_token = data.get("poToken") or data.get("po_token") or self.po_token
                    self.visitor_data = data.get("visitorData") or data.get("visitor_data") or self.visitor_data
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
                    logger.info("PO Token injetado no node %s", node.rest_uri)
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

    def try_generate_sync(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(self.generate_via_browser())
            loop.close()
            return data
        except Exception:
            return False


youtube_cookie_manager = YouTubeCookieManager()
