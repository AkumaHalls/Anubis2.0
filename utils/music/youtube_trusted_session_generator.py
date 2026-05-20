import asyncio
import json
import logging
import os
import random
import re
import traceback
from typing import Optional

import aiohttp

logger = logging.getLogger("youtube_session")

YOUTUBE_URLS = [
    "https://www.youtube.com/embed/jNQXAC9IVRw",
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    "https://www.youtube.com/",
]

CHROME_VERSIONS = ["130", "131", "132", "133", "134", "135"]


class YouTubeSessionGenerator:
    def __init__(self):
        self.visitor_data: Optional[str] = None
        self.po_token: Optional[str] = None
        self._success = False
        self._data: dict = {}

    async def _try_extract_from_page(self, page_source: str) -> Optional[dict]:
        # 1) Try ytcfg.set() pattern
        for match in re.finditer(r'ytcfg\.set\s*\(\s*(\{.*?\})\s*\)\s*;', page_source, re.DOTALL):
            try:
                cfg = json.loads(match.group(1))
                vd = cfg.get('VISITOR_DATA') or cfg.get('visitorData')
                if vd:
                    return {"visitor_data": vd, "po_token": cfg.get('PO_TOKEN', '')}
            except Exception:
                continue

        # 2) Try ytcfg.data_.data_ = pattern
        ytcfg_match = re.search(r'ytcfg\.data_\.data_\s*=\s*(\{.*?\})\s*;', page_source, re.DOTALL)
        if ytcfg_match:
            try:
                cfg = json.loads(ytcfg_match.group(1))
                vd = cfg.get('VISITOR_DATA') or cfg.get('visitorData')
                if vd:
                    return {"visitor_data": vd, "po_token": cfg.get('PO_TOKEN', '')}
            except Exception:
                pass

        # 3) Try searching inside ytInitialData or ytInitialPlayerResponse
        for key in ("ytInitialData", "ytInitialPlayerResponse"):
            pattern = rf'{re.escape(key)}\s*=\s*(\{{.*?\}})\s*;'
            for match in re.finditer(pattern, page_source, re.DOTALL):
                try:
                    data = json.loads(match.group(1))
                    # Try to find visitorData nested in responseContext
                    rc = data.get("responseContext", {})
                    vd = rc.get("visitorData") or rc.get("serviceTrackingParams", [{}])[0].get("params", [{}])[0].get("value")
                    if vd:
                        return {"visitor_data": vd, "po_token": ""}
                except Exception:
                    continue

        # 4) Try direct visitorData in page source
        for match in re.finditer(r'"visitorData"\s*:\s*"([^"]+)"', page_source):
            return {"visitor_data": match.group(1), "po_token": ""}

        # 5) Try legacy inline pattern
        for match in re.finditer(r'visitorData["\']\s*:\s*["\']([^"\']+)["\']', page_source):
            return {"visitor_data": match.group(1), "po_token": ""}

        return None

    async def generate_via_http(self, timeout: int = 15) -> Optional[dict]:
        headers = {
            "User-Agent": self._random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        urls_to_try = list(YOUTUBE_URLS)
        random.shuffle(urls_to_try)
        last_error = None
        for url in urls_to_try:
            try:
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
                        text = await resp.text()
                        if len(text) < 500:
                            continue
                        data = await self._try_extract_from_page(text)
                        if data and data.get("visitor_data"):
                            self._data = data
                            self.visitor_data = data.get("visitor_data")
                            self.po_token = data.get("po_token", "")
                            if self.visitor_data:
                                self._success = True
                                logger.info(
                                    "Sessao YouTube gerada via HTTP: visitor_data=%s... po_token=%s...",
                                    (self.visitor_data or "")[:20],
                                    (self.po_token or "")[:20],
                                )
                            return data
            except Exception as e:
                last_error = e
                logger.debug("Falha HTTP com URL %s: %s", url, e)
                continue
        if last_error:
            logger.debug("Todas as tentativas HTTP falharam: %s", last_error)
        return None

    def _random_ua(self) -> str:
        cv = random.choice(CHROME_VERSIONS)
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{cv}.0.0.0 Safari/537.36"

    async def _patch_nodriver_prepare_headless(self):
        try:
            import nodriver.core.connection as conn_mod
            original = getattr(conn_mod.Connection, '_prepare_headless', None)
            if original is None:
                return
            async def patched_prepare_headless(self_conn):
                try:
                    return await original(self_conn)
                except TypeError as e:
                    if "cannot unpack non-iterable" in str(e):
                        logger.debug("Contornado bug nodriver _prepare_headless (NoneType unpack)")
                        return
                    raise
            conn_mod.Connection._prepare_headless = patched_prepare_headless
        except Exception as e:
            logger.debug("Nao foi possivel aplicar patch nodriver _prepare_headless: %s", e)

    async def _ensure_browser_executable(self) -> Optional[str]:
        machine = os.uname().machine if hasattr(os, 'uname') else ""
        is_arm = machine in ("aarch64", "armv8l", "armv7l")
        is_windows = os.name == "nt"
        candidates = [
            os.environ.get("CHROME_PATH"),
            os.environ.get("CHROMIUM_PATH"),
            "/bin/chromium",
            "/bin/chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/chrome",
            "/usr/lib/chromium-browser/chromium-browser",
            "/usr/bin/google-chrome-stable",
            "/snap/bin/chromium",
        ]
        if is_windows:
            candidates = [
                os.environ.get("CHROME_PATH"),
                os.environ.get("CHROMIUM_PATH"),
                os.path.expandvars(R"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(R"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(R"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(R"%USERPROFILE%\AppData\Local\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(R"%PROGRAMFILES%\Chromium\Application\chrome.exe"),
                os.path.expandvars(R"%LOCALAPPDATA%\Chromium\Application\chrome.exe"),
                os.path.expandvars(R"%USERPROFILE%\AppData\Local\Chromium\Application\chrome.exe"),
                R"C:\Program Files\Google\Chrome\Application\chrome.exe",
                R"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                R"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe",
            ]
        if is_arm:
            candidates.insert(0, "/usr/bin/chromium-browser")
            candidates.insert(0, "/usr/lib/chromium-browser/chromium-browser")
        for path in candidates:
            if path and os.path.isfile(path) and os.access(path, os.X_OK):
                logger.debug("Browser executavel encontrado: %s", path)
                return path
        return None

    async def generate_via_browser(self, headless: bool = True, timeout: int = 30) -> dict:
        try:
            import nodriver
            from nodriver import start
        except ImportError:
            logger.info("nodriver nao instalado, pulando geracao via browser")
            return {}

        for attempt in range(2):
            browser = None
            try:
                await self._patch_nodriver_prepare_headless()
                browser_path = await self._ensure_browser_executable()
                logger.info(
                    "Iniciando Chromium (headless=%s, attempt=%d/2) para gerar sessao YouTube...",
                    headless, attempt + 1,
                )
                browser = await start(
                    headless=headless,
                    sandbox=False,
                    browser_executable_path=browser_path,
                    window_size=(1024, 768),
                )
                tab = browser.main_tab
                captured = {"data": None}

                async def handler(event):
                    try:
                        params = getattr(event, 'params', None)
                        if params is None:
                            return
                        req = params.get('request', {})
                        if '/youtubei/v1/player' not in req.get('url', ''):
                            return
                        if req.get('method') != 'POST':
                            return
                        post_data = req.get('postData')
                        if not post_data:
                            return
                        payload = json.loads(post_data)
                        vd = payload.get("context", {}).get("client", {}).get("visitorData")
                        pt = payload.get("serviceIntegrityDimensions", {}).get("poToken")
                        if vd and pt:
                            captured["data"] = {"visitor_data": vd, "po_token": pt}
                    except Exception:
                        pass

                try:
                    tab.add_handler(nodriver.cdp.network.RequestWillBeSent, handler)
                except Exception:
                    pass

                await tab.get(YOUTUBE_URLS[0])
                await asyncio.sleep(5)

                for click_attempt in range(3):
                    try:
                        btn = await tab.select("#movie_player, .ytp-large-play-button, video", timeout=3)
                        await btn.click()
                        logger.debug("Botao play clicado (tentativa %d)", click_attempt + 1)
                        break
                    except Exception:
                        if click_attempt == 2:
                            logger.debug("Nao foi possivel clicar no play")
                        else:
                            await asyncio.sleep(2)

                remaining = max(2, timeout - 10)
                await asyncio.sleep(remaining)

                if captured["data"]:
                    self._data = captured["data"]
                    self.visitor_data = captured["data"].get("visitor_data")
                    self.po_token = captured["data"].get("po_token")
                    self._success = True
                    logger.info(
                        "Sessao YouTube gerada via browser: visitor_data=%s... po_token=%s...",
                        (self.visitor_data or "")[:20],
                        (self.po_token or "")[:20],
                    )
                    return self._data

                try:
                    html = await tab.evaluate("document.documentElement.outerHTML")
                    data = await self._try_extract_from_page(html)
                    if data:
                        self._data = data
                        self.visitor_data = data.get("visitor_data")
                        self.po_token = data.get("po_token", "")
                        self._success = bool(data.get("visitor_data"))
                        return data
                except Exception:
                    pass

                logger.warning("Nao foi possivel capturar dados da sessao YouTube via browser (attempt %d/2)", attempt + 1)
                if attempt == 0:
                    headless = not headless
                    logger.debug("Tentando novamente com headless=%s", headless)
                continue

            except Exception as e:
                err_msg = str(e)
                logger.warning(
                    "Falha ao gerar sessao YouTube via browser (attempt %d/2): %s",
                    attempt + 1, err_msg[:200],
                )
                if attempt == 0:
                    headless = not headless
                    logger.debug("Tentando novamente com headless=%s", headless)
                continue
            finally:
                if browser:
                    try:
                        browser.stop()
                    except Exception:
                        pass

        return {}

    async def generate_via_ytdlp(self, timeout: int = 20) -> dict:
        try:
            import yt_dlp
        except ImportError:
            logger.debug("yt-dlp nao disponivel para extracao de sessao")
            return {}

        _user_cookie = os.path.join(os.getcwd(), "youtube_cookies_user.txt")
        if not os.path.isfile(_user_cookie):
            _env_cookies = os.environ.get("YT_USER_COOKIES", "").strip()
            if _env_cookies:
                try:
                    with open(_user_cookie, "w", encoding="utf-8") as _f:
                        _f.write(_env_cookies)
                    logger.info("Cookies restaurados de YT_USER_COOKIES em generate_via_ytdlp")
                except Exception:
                    pass

        # Try multiple player client combinations
        client_combos = [
            ["android", "android_music", "android_creator", "web", "web_creator", "web_safari"],
            ["android", "android_music", "android_creator", "web"],
            ["android", "android_music", "web"],
            ["android", "web"],
            ["android"],
        ]

        for clients in client_combos:
            try:
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": True,
                    "skip_download": True,
                    "socket_timeout": timeout,
                    "extractor_args": {
                        "youtube": {
                            "player_client": clients,
                            "max_comments": ["0"],
                        }
                    },
                }

                if os.path.isfile(_user_cookie):
                    ydl_opts["cookiefile"] = _user_cookie

                try:
                    from utils.music.youtube_cookie_manager import youtube_cookie_manager
                    if youtube_cookie_manager.po_token:
                        ydl_opts["extractor_args"]["youtube"].setdefault("po_token", [youtube_cookie_manager.po_token])
                    if youtube_cookie_manager.visitor_data:
                        ydl_opts["extractor_args"]["youtube"].setdefault("visitor_data", [youtube_cookie_manager.visitor_data])
                except Exception:
                    pass

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(
                        "https://www.youtube.com/watch?v=jNQXAC9IVRw",
                        download=False,
                    )
                    if info and isinstance(info, dict):
                        extractor = ydl.get_info_extractor("Youtube")
                        if hasattr(extractor, '_extract_session_data'):
                            session_data = extractor._extract_session_data()
                            if session_data:
                                vd = session_data.get("visitor_data") or session_data.get("visitorData")
                                pt = session_data.get("po_token") or session_data.get("poToken")
                                if vd:
                                    data = {"visitor_data": vd, "po_token": pt or ""}
                                    self._data = data
                                    self.visitor_data = vd
                                    self.po_token = pt or ""
                                    self._success = True
                                    logger.info(
                                        "Sessao YouTube gerada via yt-dlp (clients=%s): visitor_data=%s... po_token=%s...",
                                        clients, vd[:20], (pt or "")[:20],
                                    )
                                    return data
            except Exception as e:
                logger.debug("Falha yt-dlp com clients %s: %s", clients, e)
                continue

        return {}

    async def generate(self, headless: bool = True, timeout: int = 30) -> dict:
        # 1) yt-dlp is most reliable -> try first
        data = await self.generate_via_ytdlp(timeout=timeout)
        if data and data.get("visitor_data"):
            return data

        # 2) HTTP extraction as light fallback
        data = await self.generate_via_http(timeout=timeout)
        if data and data.get("visitor_data"):
            return data

        # 3) browser as last resort
        data = await self.generate_via_browser(headless=headless, timeout=timeout)
        return data

    @property
    def success(self) -> bool:
        return self._success


async def generate_session(headless: bool = True, timeout: int = 30) -> dict:
    gen = YouTubeSessionGenerator()
    return await gen.generate(headless=headless, timeout=timeout)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    async def main():
        data = await generate_session(headless=False, timeout=30)
        print("Dados gerados:", json.dumps(data, indent=2))
    asyncio.run(main())
