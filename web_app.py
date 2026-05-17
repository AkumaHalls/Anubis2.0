# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from os import environ
from pathlib import Path
from traceback import print_exc
from typing import TYPE_CHECKING, Optional

import aiohttp
import disnake
import tornado.ioloop
import tornado.web
import tornado.websocket
from packaging import version

from config_loader import load_config

if TYPE_CHECKING:
    from utils.client import BotPool

logging.getLogger('tornado.access').disabled = True

users_ws = {}
bots_ws = []

minimal_version = version.parse("2.6.1")

class IndexHandler(tornado.web.RequestHandler):

    def initialize(self, pool: Optional[BotPool] = None, message: str = "", config: dict = None):
        self.message = message
        self.pool = pool
        self.config = config

    async def prepare(self):

        bots = [asyncio.create_task(bot.wait_until_ready()) for bot in self.pool.bots if not bot.is_ready()]

        if bots:
            self.write("")
            await self.flush()
            await asyncio.wait(bots, timeout=7)

    async def get(self):

        try:
            killing_state = self.pool.killing_state
        except:
            killing_state = False

        if killing_state is True:
            self.write('<h1 style=\"font-size:5vw\">A aplicação será reiniciada em breve...</h1>')
            return

        msg = ""

        if self.message:
            msg += self.message.replace("\n", "</br>")

        style = """<style>
        table, th, td {
            border:1px solid black;
            text-align: center;
        }
        a {
          color: blue;
          visited: blue;
        }
        </style>"""

        failed_bots = []
        pending_bots = []
        ready_bots = []

        kwargs = {}

        for identifier, exception in self.pool.failed_bots.items():
            failed_bots.append(f"<tr><td>{identifier}</td><td>{exception}</td></tr>")

        for bot in sorted(self.pool.bots, key=lambda b: b.identifier):

            if bot.is_ready():
                avatar = bot.user.display_avatar.replace(size=256, static_format="png").url
                guilds = len(bot.guilds)
                ready_bots.append(
                    f"<tr><td><img src=\"{avatar}\" width=128 weight=128></img></td>\n"
                    "<td style=\"padding-top: 10px ; padding-bottom: 10px; padding-left: 10px; padding-right: 10px\">"
                    f"Adicionar:<br><a href=\"{disnake.utils.oauth_url(bot.user.id, permissions=disnake.Permissions(bot.config['INVITE_PERMISSIONS']), scopes=('bot', 'applications.commands'), **kwargs)}\" "
                    f"rel=\"nofollow\" target=\"_blank\">{bot.user}</a>" + (f"<br>Servers: {guilds}" if guilds else "") + "</td></tr>"
                )
            else:
                pending_bots.append(f"<tr><td>{bot.identifier}</td></tr>")

        if ready_bots:
            msg += f"\n<p style=\"font-size:20px\">Bots Disponíveis:</p>" \
                   f"{style}\n<table cellpadding=\"3\">{''.join(ready_bots)}</table>"

        if pending_bots:
            msg += f"\n<p style=\"font-size:20px\">Bots em inicialização:</p>" \
                   f"{style}\n<table cellpadding=\"10\">{''.join(pending_bots)}</table>\n" \
                   f"Nota: Recarregue a página para conferir se o bot está disponível."

        if failed_bots:

            failed_table_style = """<style>
            table, th, td {
                border:1px solid black;
                text-align: left;
            }
            </style>"""

            msg += f"\n<p style=\"font-size:20px\">Os seguintes tokens configurado na ENV/SECRET/.env falharam " \
                   f"na inicialização:</p>" \
                   f"{failed_table_style}\n<table cellpadding=\"10\">{''.join(failed_bots)}</table>"

        ws_url = "<Body onLoad=\" rpcUrl()\" ><p id=\"url\" style=\"color:blue\"></p><script>function rpcUrl(){document." \
                     "getElementById(\"url\").innerHTML = window.location.href.replace(\".replit.dev\", \".replit.dev:443\").replace(\"http\", \"ws\")" \
                     ".replace(\"https\", \"wss\") + \"ws\"}</script></body>"

        msg += f"<p><a href=\"https://github.com/zRitsu/DC-MusicBot-RPC" \
              f"/releases\" target=\"_blank\">Baixe o app de rich presence aqui.</a></p>Link para adicionar no app " \
              f"de RPC: {ws_url}"

        if self.config["ENABLE_RPC_AUTH"]:
            msg += f"\nNão esqueça de obter o token para configurar no app, use o comando /rich_presence para obter um.\n<br><br>"

        msg += f"\nPrefixo padrão: {self.pool.config['DEFAULT_PREFIX']}<br><br>"

        if self.pool.commit:
            msg += f"\nCommit Atual: <a href=\"{self.pool.remote_git_url}/commit/{self.pool.commit}\" target=\"_blank\">{self.pool.commit[:7]}</a>"

        self.write(msg)


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_ids: list = []
        self.bot_ids: list = []
        self.token = ""
        self.blocked = False
        self.auth_enabled = False

    def on_message(self, message):

        data = json.loads(message)

        ws_id = data.get("user_ids")
        bot_id = data.get("bot_id")
        token = data.pop("token", "") or ""
        app_version = version.parse(data.get("version", "0"))
        self.auth_enabled = data.pop("auth_enabled", False)

        if not ws_id:

            if not bot_id:
                print(f"desconectando: por falta de id de usuario {self.request.remote_ip}\nDados: {data}")
                self.write_message(json.dumps({"op": "disconnect", "reason": "Desconectando por falta de ids de usuario"}))
                self.close(code=4200)
                return

            try:

                if self.auth_enabled:

                    if users_ws[data["user"]].token != token:

                        if users_ws[data["user"]].blocked:
                            return

                        data.update(
                            {
                                "op": "exception",
                                "message": "token inválido! Por via das dúvidas gere um novo token usando o comando no "
                                           "bot: /rich_presence."
                            }
                        )

                        for d in ("token", "track", "info"):
                            data.pop(d, None)

                        users_ws[data["user"]].blocked = True

                    else:
                        users_ws[data["user"]].blocked = False

                users_ws[data["user"]].write_message(json.dumps(data))

            except KeyError:
                pass
            except Exception as e:
                print(f"Erro ao processar dados do rpc para o user [{data['user']}]: {repr(e)}")

            return

        is_bot = data.pop("bot", False)

        if is_bot:
            print(f"🤖 - Nova conexão - Bot: {ws_id} {self.request.remote_ip}")
            self.bot_ids = ws_id
            bots_ws.append(self)
            return

        if app_version < minimal_version:
            self.write_message(json.dumps({"op": "disconnect", "reason": "Versão do app não suportado! Certifique-se de que está usando "
                                         f"a versão mais recente do app ({minimal_version} ou superior)."}))
            self.close(code=4200)
            return

        if len(ws_id) > 3:
            self.write_message(json.dumps({"op": "disconnect", "reason": "Você está tentando conectar mais de 3 usuários consecutivamente..."}))
            self.close(code=4200)
            return

        if len(token) not in (0, 50):
            self.write_message(
                json.dumps({"op": "disconnect", "reason": f"O token precisa ter 50 caracteres..."}))
            self.close(code=4200)
            return

        self.user_ids = ws_id

        print("\n".join(f"👤 - Nova conexão - User: {u}" for u in self.user_ids))

        for u_id in ws_id:
            try:
                users_ws[u_id].write_message(json.dumps({"op": "disconnect",
                                               "reason": "Nova sessão iniciada em outro local..."}))
                users_ws[u_id].close(code=4200)
            except:
                pass
            users_ws[u_id] = self

        self.token = token

        for w in bots_ws:

            try:
                w.write_message(json.dumps(data))
            except Exception as e:
                print(f"🤖 - Erro ao processar dados do rpc para os bot's {w.bot_ids}: {repr(e)}")

    def check_origin(self, origin: str):
        return True

    def on_close(self):

        if self.user_ids:
            print("\n".join(f"👤 - Conexão Finalizada - User: {u}" for u in self.user_ids))
            for u_id in self.user_ids:
                try:
                    del users_ws[u_id]
                except KeyError:
                    continue
            return

        if not self.bot_ids:
            print(f"Conexão Finalizada - IP: {self.request.remote_ip}")

        else:

            print(f"🌐 - Conexão Finalizada - Bot ID's: {self.bot_ids}")

            data = {"op": "close", "bot_id": self.bot_ids}

            for w in users_ws.values():

                if w.blocked:
                    continue

                try:
                    w.write_message(data)
                except Exception as e:
                    print(
                        f"👤 - Erro ao processar dados do rpc para os usuários: [{', '.join(str(i) for i in w.user_ids)}]: {repr(e)}")

        bots_ws.remove(self)


class APIHandler:
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def options(self):
        self.set_status(204)
        self.finish()


class APIStatsHandler(APIHandler, tornado.web.RequestHandler):
    def initialize(self, pool=None, config=None):
        self.pool = pool
        self.config = config

    async def get(self):
        try:
            if not self.pool:
                self.write({"error": "Pool not available"})
                return
            data = {
                "bots": [],
                "failed_bots": [],
                "total_servers": 0,
                "total_users": 0,
                "active_players": 0,
            }
            for bot in self.pool.bots:
                if bot.is_ready():
                    guilds = bot.guilds or []
                    bot_info = {
                        "id": str(bot.user.id),
                        "name": bot.user.name,
                        "discriminator": bot.user.discriminator,
                        "avatar": bot.user.display_avatar.replace(size=256, static_format="png").url,
                        "guilds": len(guilds),
                        "users": sum(g.member_count for g in guilds if g.member_count),
                        "players": len(bot.music.players) if bot.music else 0,
                        "uptime": str(datetime.now(timezone.utc) - bot.uptime).split(".")[0] if hasattr(bot, "uptime") and bot.uptime else "N/A",
                    }
                    data["bots"].append(bot_info)
                    data["total_servers"] += bot_info["guilds"]
                    data["total_users"] += bot_info["users"]
                    data["active_players"] += bot_info["players"]
            for name, err in self.pool.failed_bots.items():
                data["failed_bots"].append({"name": name, "error": str(err)[:200]})
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(data))
        except Exception as e:
            self.set_header("Content-Type", "application/json")
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))


class APIPlayersHandler(APIHandler, tornado.web.RequestHandler):
    def initialize(self, pool=None, config=None):
        self.pool = pool
        self.config = config

    async def get(self):
        try:
            players = []
            if self.pool and self.pool.bots:
                for bot in self.pool.bots:
                    if not bot.is_ready():
                        continue
                    if not bot.music:
                        continue
                    for guild_id, player in bot.music.players.items():
                        guild = bot.get_guild(guild_id)
                        if not guild:
                            continue
                        track = player.current
                        player_info = {
                            "guild_id": str(guild_id),
                            "guild_name": guild.name,
                            "guild_icon": guild.icon.url if guild.icon else None,
                            "channel": player.channel.name if hasattr(player, "channel") and player.channel else "N/A",
                            "is_playing": player.is_playing if hasattr(player, "is_playing") else False,
                            "is_paused": player.paused if hasattr(player, "paused") else False,
                            "volume": player.volume if hasattr(player, "volume") else 100,
                            "queue_size": len(player.queue) if hasattr(player, "queue") else 0,
                            "bot_name": bot.user.name,
                        }
                        if track:
                            player_info["track"] = {
                                "title": track.title if hasattr(track, "title") else "Unknown",
                                "author": track.author if hasattr(track, "author") else "Unknown",
                                "uri": track.uri if hasattr(track, "uri") else "",
                                "duration": track.duration if hasattr(track, "duration") else 0,
                                "position": player.position if hasattr(player, "position") else 0,
                                "thumbnail": track.thumbnail if hasattr(track, "thumbnail") else "",
                            }
                            if player_info["track"]["duration"] > 0:
                                player_info["track"]["progress_pct"] = round(
                                    (player_info["track"]["position"] / player_info["track"]["duration"]) * 100, 1
                                )
                            else:
                                player_info["track"]["progress_pct"] = 0
                        players.append(player_info)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"players": players}))
        except Exception as e:
            self.set_header("Content-Type", "application/json")
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))


class APIServersHandler(APIHandler, tornado.web.RequestHandler):
    def initialize(self, pool=None, config=None):
        self.pool = pool
        self.config = config

    async def get(self):
        try:
            servers = []
            if self.pool and self.pool.bots:
                for bot in self.pool.bots:
                    if not bot.is_ready():
                        continue
                    if not bot.music:
                        continue
                    for guild in bot.guilds:
                        player = bot.music.players.get(guild.id)
                        servers.append({
                            "id": str(guild.id),
                            "name": guild.name,
                            "icon": guild.icon.url if guild.icon else None,
                            "members": guild.member_count,
                            "channels": len(guild.channels),
                            "bot_name": bot.user.name,
                            "has_player": player is not None,
                            "is_playing": player.is_playing if player and hasattr(player, "is_playing") else False,
                            "current_track": getattr(player.current, "title", None) if player and player.current else None,
                        })
            servers.sort(key=lambda s: s["members"], reverse=True)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"servers": servers}))
        except Exception as e:
            self.set_header("Content-Type", "application/json")
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))


class APIConfigHandler(APIHandler, tornado.web.RequestHandler):
    def initialize(self, pool=None, config=None):
        self.pool = pool
        self.config = config

    async def get(self):
        try:
            safe_config = {}
            for k, v in self.config.items():
                if not any(x in str(k).upper() for x in ["TOKEN", "SECRET", "WEBHOOK"]):
                    safe_config[k] = v
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(safe_config))
        except Exception as e:
            self.set_header("Content-Type", "application/json")
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))

    async def post(self):
        try:
            body = json.loads(self.request.body)
        except Exception:
            self.set_status(400)
            self.write({"error": "Invalid JSON"})
            return

        env_path = Path(".env")
        if not env_path.exists():
            self.set_status(404)
            self.write({"error": ".env not found"})
            return

        lines = env_path.read_text(encoding="utf-8").splitlines()
        updated = []
        changed = []
        for line in lines:
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                key = stripped.split("=", 1)[0].strip()
                if key in body:
                    val = str(body[key])
                    updated.append(f"{key}='{val}'")
                    changed.append(key)
                    continue
            updated.append(line)

        env_path.write_text("\n".join(updated), encoding="utf-8")
        self.write({"success": True, "changed": changed})


class APIPlayerControlHandler(APIHandler, tornado.web.RequestHandler):
    def initialize(self, pool=None, config=None):
        self.pool = pool
        self.config = config

    async def get(self, guild_id):
        await self._handle_control(guild_id)

    async def post(self, guild_id):
        await self._handle_control(guild_id)

    async def _handle_control(self, guild_id):
        try:
            self.set_header("Content-Type", "application/json")
            action = self.get_argument("action", None)
            if not action:
                self.write(json.dumps({"success": False, "error": "action required"}))
                return
            if not self.pool or not self.pool.bots:
                self.write(json.dumps({"success": False, "error": "Bot not available"}))
                return
            for bot in self.pool.bots:
                if not bot.is_ready():
                    continue
                if not bot.music:
                    continue
                player = bot.music.players.get(int(guild_id))
                if not player:
                    continue
                try:
                    if action == "pause":
                        await player.set_pause(not player.paused)
                        self.write(json.dumps({"success": True, "action": "pause", "state": player.paused}))
                    elif action == "skip":
                        await player.stop()
                        self.write(json.dumps({"success": True, "action": "skip"}))
                    elif action == "stop":
                        await player.stop()
                        await player.disconnect()
                        self.write(json.dumps({"success": True, "action": "stop"}))
                    elif action.startswith("volume="):
                        vol = max(0, min(100, int(action.split("=")[1])))
                        await player.set_volume(vol)
                        self.write(json.dumps({"success": True, "action": "volume", "volume": vol}))
                    else:
                        self.write(json.dumps({"success": False, "error": f"Unknown action: {action}"}))
                    return
                except Exception as e:
                    self.write(json.dumps({"success": False, "error": str(e)}))
                    return
            self.write(json.dumps({"success": False, "error": "Player not found"}))
        except Exception as e:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"success": False, "error": str(e)}))


class APILogsHandler(APIHandler, tornado.web.RequestHandler):
    def initialize(self, pool=None, config=None):
        self.pool = pool
        self.config = config

    async def get(self):
        limit = int(self.get_argument("limit", 50))
        log_file = Path(".logs") / "disnake.log"
        if not log_file.exists():
            self.write({"logs": []})
            return
        try:
            text = log_file.read_text(encoding="utf-8", errors="ignore")
            lines = text.strip().split("\n")[-limit:]
            result = [{"line": i + 1, "text": l} for i, l in enumerate(lines)]
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"logs": result}))
        except Exception:
            self.write({"logs": []})


class APIServerLeaveHandler(APIHandler, tornado.web.RequestHandler):
    def initialize(self, pool=None, config=None):
        self.pool = pool
        self.config = config

    async def post(self, guild_id):
        if not self.pool or not self.pool.bots:
            self.write({"success": False, "error": "Bot not available"})
            return
        for bot in self.pool.bots:
            if not bot.is_ready():
                continue
            guild = bot.get_guild(int(guild_id))
            if not guild:
                continue
            try:
                await guild.leave()
                self.write({"success": True, "guild_id": int(guild_id), "guild_name": guild.name})
                return
            except Exception as e:
                self.write({"success": False, "error": str(e)})
                return
        self.write({"success": False, "error": "Guild not found"})


class WSClient:

    def __init__(self, url: str, pool: BotPool):
        self.url: str = url
        self.pool = pool
        self.all_bots = None
        self.connection = None
        self.backoff: int = 7
        self.data: dict = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.connect_task = []

    async def connect(self):

        if not self.session:
            self.session = aiohttp.ClientSession()

        self.connection = await self.session.ws_connect(self.url, heartbeat=30)

        self.backoff = 7

        print("🌐 - RPC client conectado, sincronizando rpc dos bots...")

        if not self.all_bots:
            self.all_bots = self.pool.get_all_bots()

        self.connect_task = [asyncio.create_task(self.connect_bot_rpc())]

    @property
    def is_connected(self):
        return self.connection and not self.connection.closed

    async def connect_bot_rpc(self):

        bot_ids = set()

        for bot in self.all_bots:
            await bot.wait_until_ready()
            bot_ids.add(bot.user.id)

        if not bot_ids:
            print("🌐 - Conexão com servidor RPC ignorado: Lista de bots vazia...")
            return

        await self.send({"user_ids": list(bot_ids), "bot": True, "auth_enabled": self.pool.config["ENABLE_RPC_AUTH"]})

        await asyncio.sleep(1)

        for bot in self.all_bots:
            for player in bot.music.players.values():

                if not player.guild.me.voice:
                    continue

                if player.guild.me.voice.channel.voice_states:
                    bot.loop.create_task(player.process_rpc(player.last_channel))

        print(f"🌐 - [RPC client] - Os dados de rpc foram sincronizados com sucesso.")

    async def send(self, data: dict):

        if not self.is_connected:
            return

        try:
            await self.connection.send_json(data)
        except:
            print_exc()

    def clear_tasks(self):

        for t in self.connect_task:
            try:
                t.cancel()
            except:
                continue

        self.connect_task.clear()

    async def ws_loop(self):

        while True:

            try:

                if not self.is_connected:
                    self.clear_tasks()
                    await self.connect()

            except Exception as e:
                if isinstance(e, aiohttp.WSServerHandshakeError):
                    print(f"🌐 - Falha ao conectar no servidor RPC, tentando novamente em {(b:=int(self.backoff))} segundo{'s'[:b^1]}.")
                else:
                    print(f"🌐 - Conexão com servidor RPC perdida - Reconectando em {(b:=int(self.backoff))} segundo{'s'[:b^1]}.")

                await asyncio.sleep(self.backoff)
                self.backoff *= 2.5
                continue

            message = await self.connection.receive()

            if message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                print(f"🌐 - RPC Websocket Closed: {message.extra}\nReconnecting in {self.backoff}s")
                await asyncio.sleep(self.backoff)
                continue

            elif message.type in (aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
                print(f"🌐 - RPC Websocket Finalizado: {message.extra}")
                return

            data = json.loads(message.data)

            users: list = data.get("user_ids")

            if not users:
                continue

            op = data.get("op")

            if op == "rpc_update":

                for bot in self.all_bots:
                    for player in bot.music.players.values():
                        if not player.guild.me.voice:
                            continue
                        vc = player.guild.me.voice.channel
                        vc_user_ids = [i for i in vc.voice_states if i in users]
                        if vc_user_ids:
                            bot.loop.create_task(player.process_rpc(vc))
                            for i in vc_user_ids:
                                users.remove(i)


def run_app(pool: BotPool, message: str = "", config: dict = None):

    if not config:
        try:
            config = pool.config
        except IndexError:
            pass

    app = tornado.web.Application([
        (r'/', IndexHandler, {'pool': pool, 'message': message, 'config': config}),
        (r'/ws', WebSocketHandler),
        (r'/api/stats', APIStatsHandler, {'pool': pool, 'config': config}),
        (r'/api/players', APIPlayersHandler, {'pool': pool, 'config': config}),
        (r'/api/servers', APIServersHandler, {'pool': pool, 'config': config}),
        (r'/api/config', APIConfigHandler, {'pool': pool, 'config': config}),
        (r'/api/logs', APILogsHandler, {'pool': pool, 'config': config}),
        (r'/api/player/(\d+)/control', APIPlayerControlHandler, {'pool': pool, 'config': config}),
        (r'/api/server/(\d+)/leave', APIServerLeaveHandler, {'pool': pool, 'config': config}),
    ])

    app.listen(port=config.get("PORT") or environ.get("PORT", 80))


def start(pool: BotPool, message="", config: dict = None):
    if not config:
        config = load_config()
    run_app(pool, message, config)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    start(BotPool())
