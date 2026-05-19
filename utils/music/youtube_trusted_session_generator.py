import asyncio
import json
import logging
import os
import random
import string
import traceback
from typing import Optional

import aiohttp

logger = logging.getLogger("youtube_session")

YOUTUBE_EMBED = "https://www.youtube.com/embed/jNQXAC9IVRw"


class YouTubeSessionGenerator:
    def __init__(self):
        self.visitor_data: Optional[str] = None
        self.po_token: Optional[str] = None
        self._success = False
        self._data: dict = {}

    async def _try_extract_from_page(self, page_source: str) -> Optional[dict]:
        import re
        for match in re.finditer(r'ytcfg\.set\s*\(\s*({.*?})\s*\)\s*;', page_source, re.DOTALL):
            try:
                cfg = json.loads(match.group(1))
                vd = cfg.get('VISITOR_DATA') or cfg.get('visitorData')
                if vd:
                    return {"visitor_data": vd, "po_token": cfg.get('PO_TOKEN', '')}
            except Exception:
                continue
            
        for match in re.finditer(r'visitorData["\']\s*:\s*["\']([^"\']+)["\']', page_source):
            vd = match.group(1)
            pt_match = re.search(r'poToken["\']\s*:\s*["\']([^"\']+)["\']', page_source)
            return {"visitor_data": vd, "po_token": pt_match.group(1) if pt_match else ""}
        return None

    async def generate_via_http(self, timeout: int = 15) -> Optional[dict]:
        headers = {
            "User-Agent": self._random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(YOUTUBE_EMBED, timeout=timeout) as resp:
                    text = await resp.text()
                    data = await self._try_extract_from_page(text)
                    if data:
                        self._data = data
                        self._success = True
                        logger.info("Sessao YouTube gerada via HTTP: visitor_data=%s...", (data.get("visitor_data") or "")[:20])
                        return data
            return None
        except Exception as e:
            logger.debug("Falha generating session via HTTP: %s", e)
            return None

    def _random_ua(self) -> str:
        chrome_versions = ["130", "131", "132", "133", "134"]
        cv = random.choice(chrome_versions)
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{cv}.0.0.0 Safari/537.36"

    async def generate_via_browser(self, headless: bool = True, timeout: int = 30) -> dict:
        try:
            import nodriver
            from nodriver import start, cdp
        except ImportError:
            logger.info("nodriver nao instalado, pulando geracao via browser")
            return {}

        browser = None
        try:
            logger.info("Iniciando Chromium (headless=%s) para gerar sessao YouTube...", headless)
            
            browser = await start(
                headless=headless,
                sandbox=False,
                browser_executable_path=None,
                window_size=(1024, 768),
            )
            
            tab = browser.main_tab
            
            captured = {"data": None}

            async def handler(event):
                if hasattr(event, 'request') and "/youtubei/v1/player" in getattr(event.request, 'url', ''):
                    try:
                        post_data = json.loads(await event.request.post_data)
                        vd = post_data.get("context", {}).get("client", {}).get("visitorData")
                        pt = post_data.get("serviceIntegrityDimensions", {}).get("poToken")
                        if vd and pt:
                            captured["data"] = {"visitor_data": vd, "po_token": pt}
                    except Exception:
                        pass
                elif hasattr(event, 'params') and "/youtubei/v1/player" in event.params.get('request', {}).get('url', ''):
                    try:
                        req = event.params['request']
                        if req.get('method') == 'POST' and req.get('postData'):
                            post_data = json.loads(req['postData'])
                            vd = post_data.get("context", {}).get("client", {}).get("visitorData")
                            pt = post_data.get("serviceIntegrityDimensions", {}).get("poToken")
                            if vd and pt:
                                captured["data"] = {"visitor_data": vd, "po_token": pt}
                    except Exception:
                        pass

            try:
                tab.add_handler(cdp.network.RequestWillBeSent, handler)
            except AttributeError:
                try:
                    tab.add_handler(cdp.network.RequestWillBeSentExtraInfo, handler)
                except Exception:
                    pass

            await tab.get(YOUTUBE_EMBED)
            await asyncio.sleep(5)

            for attempt in range(3):
                try:
                    btn = await tab.select("#movie_player, .ytp-large-play-button, video", timeout=3)
                    await btn.click()
                    logger.debug("Botao play clicado (tentativa %d)", attempt + 1)
                    break
                except Exception:
                    if attempt == 2:
                        logger.debug("Nao foi possivel clicar no play")
                        await tab.get(YOUTUBE_EMBED)
                    await asyncio.sleep(2)

            remaining = max(2, timeout - 8)
            await asyncio.sleep(remaining)

            if captured["data"]:
                self._data = captured["data"]
                self.visitor_data = captured["data"].get("visitor_data")
                self.po_token = captured["data"].get("po_token")
                self._success = True
                logger.info("Sessao YouTube gerada via browser: visitor_data=%s... po_token=%s...",
                           (self.visitor_data or "")[:20], (self.po_token or "")[:20])
                return self._data

            try:
                html = await tab.evaluate("document.documentElement.outerHTML")
                data = await self._try_extract_from_page(html)
                if data:
                    self._data = data
                    self._success = True
                    return data
            except Exception:
                pass

            logger.warning("Nao foi possivel capturar dados da sessao YouTube via browser")
            return {}

        except Exception as e:
            logger.warning("Falha ao gerar sessao YouTube via browser: %s", traceback.format_exc())
            return {}
        finally:
            if browser:
                try:
                    browser.stop()
                except Exception:
                    pass

    async def generate(self, headless: bool = True, timeout: int = 30) -> dict:
        data = await self.generate_via_http(timeout=timeout)
        if data:
            return data

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
