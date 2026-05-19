"""
Gerador de cookies para YouTube - Anubis Music Bot
====================================================

USO:
  1. Abra o Chrome/Firefox e va ate youtube.com, faca login se quiser
  2. Instale a extensao "Get cookies.txt LOCALLY":
       Chrome:  https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
       Firefox: https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/
  3. Clique no icone da extensao e baixe os cookies
  4. Coloque o arquivo na raiz do projeto com o nome: youtube_cookies_user.txt
  5. Pronto! O bot usara automaticamente esse arquivo.

   Alternativamente, execute este script com --browser para tentar
   gerar cookies automaticamente via Chromium.

EXECUCAO:
    python generate_cookies.py --browser    (tenta gerar via Chromium)
    python generate_cookies.py              (exibe instrucoes)
"""

import argparse
import asyncio
import os
import sys


def copy_cookie_file(source_path: str) -> bool:
    import shutil
    dest = os.path.join(os.getcwd(), "youtube_cookies_user.txt")
    if not os.path.isfile(source_path):
        print(f"ERRO: Arquivo nao encontrado: {source_path}")
        return False

    # Validate it looks like a cookies file
    with open(source_path) as f:
        content = f.read(500)
        if "youtube" not in content.lower() and ".youtube.com" not in content:
            print(f"AVISO: O arquivo nao parece conter cookies do YouTube.")
            print(f"       Certifique-se de exportar de youtube.com")

    shutil.copy2(source_path, dest)
    print(f"OK: Cookies copiados para {dest}")
    return True


async def try_browser_generate():
    print("Tentando gerar cookies via Chromium...")
    sys.path.insert(0, os.getcwd())

    try:
        from utils.music.youtube_trusted_session_generator import YouTubeSessionGenerator
        gen = YouTubeSessionGenerator()
        data = await gen.generate(headless=False, timeout=45)
        if data:
            from utils.music.youtube_cookie_manager import youtube_cookie_manager
            youtube_cookie_manager.visitor_data = data.get("visitor_data")
            youtube_cookie_manager.po_token = data.get("po_token")
            from utils.music.youtube_cookie_manager import _ensure_cookie_file
            _ensure_cookie_file(
                data.get("visitor_data", ""),
                data.get("po_token", "")
            )
            print(f"OK: Cookies gerados!")
            print(f"    visitor_data: {data.get('visitor_data', '')[:30]}...")
            print(f"    po_token: {data.get('po_token', '')[:30]}...")
            return True
    except Exception as e:
        print(f"Falha ao gerar via browser: {e}")

    print("Nao foi possivel gerar cookies automaticamente.")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de cookies YouTube para Anubis")
    parser.add_argument("--browser", action="store_true", help="Tenta gerar cookies via Chromium")
    parser.add_argument("--from-file", type=str, help="Caminho para arquivo cookies.txt exportado do navegador")
    args = parser.parse_args()

    if args.from_file:
        copy_cookie_file(args.from_file)
        sys.exit(0)

    if args.browser:
        asyncio.run(try_browser_generate())
        sys.exit(0)

    print(__doc__)
