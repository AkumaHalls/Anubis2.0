import asyncio
import os
import sys
import traceback as _tb
from contextlib import asynccontextmanager
from pathlib import Path

import aiohttp
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from aiohttp.client_exceptions import ClientConnectorError, ClientError

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import load_config

config = load_config()
BOT_API_URL = os.environ.get("BOT_API_URL", "http://localhost:8080")
PROXY_TIMEOUT = int(os.environ.get("PROXY_TIMEOUT", "30"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Web Dashboard - API do bot (backend): {BOT_API_URL}")
    async with aiohttp.ClientSession() as session:
        app.state.http_session = session
        await _wait_for_backend(session)
        yield


async def _wait_for_backend(session: aiohttp.ClientSession):
    url = f"{BOT_API_URL}/api/stats"
    for attempt in range(30):
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    print(f"Bot API online apos {attempt} tentativa(s)")
                    return
        except Exception:
            pass
        if attempt == 0:
            print(f"Aguardando bot API em {BOT_API_URL}...")
        await asyncio.sleep(2)
    print(f"AVISO: Bot API nao respondeu em {BOT_API_URL} apos 60s. Painel pode mostrar Offline.")

app = FastAPI(title="Anubis Dashboard", description="Painel de Controle do Anubis Music Bot", version="2.0.0", lifespan=lifespan)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE} | Anubis</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link href="/static/css/style.css" rel="stylesheet">
<script>var API='';</script>
</head>
<body class="bg-[#0d1117] text-gray-200 min-h-screen">
<div class="flex h-screen overflow-hidden">
<aside class="w-64 bg-[#161b22] border-r border-gray-800 flex-shrink-0 hidden md:flex flex-col">
<div class="p-5 border-b border-gray-800">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg">A</div>
<div><h1 class="text-lg font-bold text-white">Anubis</h1><p class="text-xs text-gray-500">Music Bot v2.0</p></div>
</div></div>
<nav class="flex-1 p-4 space-y-1 overflow-y-auto">{NAV}</nav>
<div class="p-4 border-t border-gray-800">
<div class="flex items-center gap-2 text-xs text-gray-500">
<div class="w-2 h-2 rounded-full bg-green-500 animate-pulse" id="statusDot"></div>
<span id="statusText">Conectando...</span></div></div>
</aside>
<div class="md:hidden fixed top-0 left-0 right-0 bg-[#161b22] border-b border-gray-800 z-50 px-4 py-3 flex items-center justify-between">
<div class="flex items-center gap-2">
<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm">A</div>
<span class="font-bold text-white">Anubis</span></div>
<button id="mobileMenuBtn" class="text-gray-400 text-2xl"><i class="fas fa-bars"></i></button>
</div>
<div id="mobileMenu" class="md:hidden fixed inset-0 bg-black/60 z-40 hidden" style="margin-top:56px">
<div class="bg-[#161b22] w-64 h-full p-4 space-y-1 overflow-y-auto">
<button id="closeMenuBtn" class="text-gray-400 hover:text-white mb-4 text-xl"><i class="fas fa-times"></i></button>
            {NAV}
</div></div>
<main class="flex-1 overflow-y-auto md:pt-0 pt-16"><div class="p-6">{BODY}</div></main>
</div>
<script src="/static/js/dashboard.js"></script>
</body></html>"""

def render(title, body, page="dashboard"):
    items = []
    links = [("/","dashboard","Dashboard","chart-pie"),("/players","players","Players","music"),("/servers","servers","Servidores","server"),("/logs","logs","Logs","list"),("/settings","settings","Config","cog")]
    for href, p, label, icon in links:
        active = "bg-purple-600/20 text-purple-400 border border-purple-500/30" if p == page else "text-gray-400 hover:text-white hover:bg-gray-800/50"
        items.append(f'<a href="{href}" class="flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 {active}"><i class="fas fa-{icon} w-5 text-center"></i><span class="font-medium">{label}</span></a>')
    nav = "\n".join(items)
    return PAGE.replace("{TITLE}", title).replace("{NAV}", nav).replace("{BODY}", body)

@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return HTMLResponse(render("Dashboard", """<div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-8">
        <div><h2 class="text-3xl font-bold text-white">Dashboard</h2><p class="text-gray-500 mt-1">Visao geral do Anubis</p></div>
        <div id="statusBadge" class="flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 px-4 py-2 rounded-lg text-sm">
            <div class="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></div><span>Carregando...</span></div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-[#161b22] border border-gray-800 rounded-xl p-6 hover:border-purple-500/30 transition-all duration-300 group">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center group-hover:bg-purple-500/20 transition"><i class="fas fa-robot text-purple-400 text-xl"></i></div>
                <span class="text-xs text-gray-600">Total</span></div>
            <p class="text-3xl font-bold text-white" id="statBots">-</p>
            <p class="text-sm text-gray-500 mt-1">Bots Online</p></div>
        <div class="bg-[#161b22] border border-gray-800 rounded-xl p-6 hover:border-blue-500/30 transition-all duration-300 group">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition"><i class="fas fa-server text-blue-400 text-xl"></i></div>
                <span class="text-xs text-gray-600">Total</span></div>
            <p class="text-3xl font-bold text-white" id="statServers">-</p>
            <p class="text-sm text-gray-500 mt-1">Servidores</p></div>
        <div class="bg-[#161b22] border border-gray-800 rounded-xl p-6 hover:border-green-500/30 transition-all duration-300 group">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center group-hover:bg-green-500/20 transition"><i class="fas fa-users text-green-400 text-xl"></i></div>
                <span class="text-xs text-gray-600">Total</span></div>
            <p class="text-3xl font-bold text-white" id="statUsers">-</p>
            <p class="text-sm text-gray-500 mt-1">Usuarios</p></div>
        <div class="bg-[#161b22] border border-gray-800 rounded-xl p-6 hover:border-pink-500/30 transition-all duration-300 group">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 rounded-lg bg-pink-500/10 flex items-center justify-center group-hover:bg-pink-500/20 transition"><i class="fas fa-headphones text-pink-400 text-xl"></i></div>
                <span class="text-xs text-gray-600">Agora</span></div>
            <p class="text-3xl font-bold text-white" id="statPlayers">-</p>
            <p class="text-sm text-gray-500 mt-1">Players Ativos</p></div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="bg-[#161b22] border border-gray-800 rounded-xl p-6">
            <h3 class="text-lg font-semibold text-white mb-4">Atividade dos Players</h3>
            <canvas id="playerChart" height="200"></canvas></div>
        <div class="bg-[#161b22] border border-gray-800 rounded-xl p-6">
            <h3 class="text-lg font-semibold text-white mb-4">Distribuicao por Bot</h3>
            <canvas id="botChart" height="200"></canvas></div>
    </div>
    <div class="bg-[#161b22] border border-gray-800 rounded-xl overflow-hidden">
        <div class="p-6 border-b border-gray-800"><h3 class="text-lg font-semibold text-white">Status dos Bots</h3></div>
        <div class="overflow-x-auto"><table class="w-full">
            <thead><tr class="bg-gray-800/50 text-gray-400 text-sm uppercase tracking-wider">
                <th class="text-left px-6 py-4">Bot</th><th class="text-left px-6 py-4">ID</th>
                <th class="text-center px-6 py-4">Servidores</th><th class="text-center px-6 py-4">Usuarios</th>
                <th class="text-center px-6 py-4">Players</th><th class="text-center px-6 py-4">Uptime</th>
                <th class="text-center px-6 py-4">Status</th>
            </tr></thead>
            <tbody id="botTableBody"></tbody>
        </table></div>
    </div>
    <div id="failedBots"></div>
</div>
<script>
var _dashRetry = 0;
async function loadDashboard() {
    try {
        var r = await fetch(API+'/api/stats'), d = await r.json();
        _dashRetry = 0;
        if (d.error) { document.getElementById('statusBadge').innerHTML='<div class="w-2 h-2 rounded-full bg-red-500"></div><span>'+d.error+'</span>'; return; }
        document.getElementById('statBots').textContent = d.bots ? d.bots.length : 0;
        document.getElementById('statServers').textContent = d.total_servers || 0;
        document.getElementById('statUsers').textContent = d.total_users || 0;
        document.getElementById('statPlayers').textContent = d.active_players || 0;
        var badge = document.getElementById('statusBadge');
        var online = d.bots && d.bots.length > 0;
        badge.className = 'flex items-center gap-2 px-4 py-2 rounded-lg text-sm ' + (online ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-red-500/10 border border-red-500/30 text-red-400');
        badge.innerHTML = '<div class="w-2 h-2 rounded-full ' + (online ? 'bg-green-500 animate-pulse' : 'bg-red-500') + '"></div><span>' + (online ? 'Online' : 'Offline') + '</span>';
        var tbody = document.getElementById('botTableBody');
        if (!d.bots || !d.bots.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-12 text-center text-gray-500"><i class="fas fa-robot text-4xl mb-3 block opacity-30"></i><p>Nenhum bot conectado</p><p class="text-xs mt-1">Inicie o bot principal primeiro</p></td></tr>';
        } else {
            tbody.innerHTML = d.bots.map(function(b) { return '<tr class="border-t border-gray-800/50 hover:bg-gray-800/30 transition">' +
                '<td class="px-6 py-4"><div class="flex items-center gap-3"><img src="' + b.avatar + '" class="w-10 h-10 rounded-full"><span class="font-medium text-white">' + b.name + '</span></div></td>' +
                '<td class="px-6 py-4 text-gray-400 text-sm">' + b.id + '</td>' +
                '<td class="px-6 py-4 text-center text-white">' + b.guilds + '</td>' +
                '<td class="px-6 py-4 text-center text-white">' + b.users + '</td>' +
                '<td class="px-6 py-4 text-center text-white">' + b.players + '</td>' +
                '<td class="px-6 py-4 text-center text-gray-400">' + (b.uptime || 'N/A') + '</td>' +
                '<td class="px-6 py-4 text-center"><span class="inline-flex items-center gap-1.5 bg-green-500/10 text-green-400 text-xs font-medium px-3 py-1.5 rounded-full"><div class="w-1.5 h-1.5 rounded-full bg-green-500"></div>Online</span></td></tr>'; }).join('');
        }
        var fb = document.getElementById('failedBots');
        if (d.failed_bots && d.failed_bots.length) {
            fb.innerHTML = '<div class="bg-red-500/5 border border-red-500/20 rounded-xl overflow-hidden mt-6"><div class="p-4 border-b border-red-500/20 flex items-center gap-2"><i class="fas fa-exclamation-triangle text-red-400"></i><h3 class="font-semibold text-red-400">Falhas</h3></div><div class="p-4">' + d.failed_bots.map(function(f){return '<div class="text-sm text-red-300 mb-2"><strong>'+f.name+':</strong> '+f.error+'</div>';}).join('') + '</div></div>';
        } else { fb.innerHTML = ''; }
        try {
            new Chart(document.getElementById('playerChart'), { type: 'doughnut', data: { labels: ['Ativos', 'Inativos'], datasets: [{ data: [d.active_players||0, Math.max(0,(d.total_servers||0)-(d.active_players||0))], backgroundColor: ['#a855f7', '#1f2937'], borderWidth: 0 }] }, options: { responsive: true, plugins: { legend: { labels: { color: '#9ca3af' } } } } });
            var names = d.bots ? d.bots.map(function(b){return b.name;}) : [];
            var guilds = d.bots ? d.bots.map(function(b){return b.guilds;}) : [];
            var players = d.bots ? d.bots.map(function(b){return b.players;}) : [];
            new Chart(document.getElementById('botChart'), { type: 'bar', data: { labels: names.length ? names : ['Nenhum'], datasets: [{ label: 'Servidores', data: guilds.length ? guilds : [0], backgroundColor: '#3b82f6' },{ label: 'Players', data: players.length ? players : [0], backgroundColor: '#a855f7' }] }, options: { responsive: true, plugins: { legend: { labels: { color: '#9ca3af' } } }, scales: { y: { ticks: { color: '#6b7280' }, grid: { color: '#1f2937' } }, x: { ticks: { color: '#9ca3af' } } } } });
        } catch(e) {}
    } catch(e) {
        document.getElementById('statusBadge').innerHTML = '<div class="w-2 h-2 rounded-full bg-red-500"></div><span>API Offline</span>';
        if (_dashRetry < 3) { _dashRetry++; setTimeout(loadDashboard, 3000); }
    }
}
document.addEventListener('DOMContentLoaded', loadDashboard);
setInterval(loadDashboard, 15000);
</script>"""))

@app.get("/players", response_class=HTMLResponse)
async def players_page(request: Request):
    return HTMLResponse(render("Players", """<div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-8">
        <div><h2 class="text-3xl font-bold text-white">Players Ativos</h2><p class="text-gray-500 mt-1">Musicas tocando agora</p></div>
        <button onclick="refreshPlayers()" class="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg transition text-sm"><i class="fas fa-sync-alt"></i> Atualizar</button>
    </div>
    <div id="playersContainer" class="space-y-4">
        <div class="text-center py-12 text-gray-500"><i class="fas fa-headphones text-5xl mb-4 opacity-30"></i><p>Carregando players...</p></div>
    </div>
</div>
<script>
async function refreshPlayers() {
    var c = document.getElementById('playersContainer');
    c.innerHTML = '<div class="text-center py-12 text-gray-500"><i class="fas fa-spinner fa-spin text-3xl mb-4"></i><p>Atualizando...</p></div>';
    try {
        var r = await fetch(API+'/api/players'), d = await r.json();
        if (d.error || !d.players || !d.players.length) { c.innerHTML = '<div class="text-center py-16 text-gray-500"><i class="fas fa-headphones text-6xl mb-4 opacity-20"></i><p class="text-xl font-medium text-gray-400">Nenhum player ativo</p></div>'; return; }
        c.innerHTML = d.players.map(function(p) {
            var t = p.track, pct = t ? (t.progress_pct||0) : 0;
            var fmt = function(s) { var m = Math.floor(s/60); var sec = Math.floor(s%60); return m + ':' + (sec < 10 ? '0' : '') + sec; };
            var controls = t ? '<div class="flex items-center gap-2 flex-shrink-0">' +
                '<button onclick="controlPlayer(\\'' + p.guild_id + '\\',\\'pause\\')" class="w-10 h-10 rounded-lg bg-gray-700 hover:bg-gray-600 flex items-center justify-center text-white transition"><i class="fas ' + (p.is_paused ? 'fa-play' : 'fa-pause') + '"></i></button>' +
                '<button onclick="controlPlayer(\\'' + p.guild_id + '\\',\\'skip\\')" class="w-10 h-10 rounded-lg bg-gray-700 hover:bg-gray-600 flex items-center justify-center text-white transition"><i class="fas fa-forward-step"></i></button>' +
                '<button onclick="controlPlayer(\\'' + p.guild_id + '\\',\\'stop\\')" class="w-10 h-10 rounded-lg bg-gray-700 hover:bg-red-600 flex items-center justify-center text-white transition"><i class="fas fa-stop"></i></button></div>' : '';
            var nowPlaying = t ? '<div class="bg-gray-800/30 rounded-lg p-4 mb-4"><div class="flex items-center gap-4">' +
                (t.thumbnail ? '<img src="' + t.thumbnail + '" class="w-16 h-16 rounded-lg object-cover flex-shrink-0">' : '<div class="w-16 h-16 rounded-lg bg-gray-700 flex items-center justify-center flex-shrink-0"><i class="fas fa-music text-2xl text-gray-500"></i></div>') +
                '<div class="flex-1 min-w-0"><p class="font-medium text-white truncate">' + t.title + '</p><p class="text-sm text-gray-400 truncate">' + t.author + '</p>' +
                '<div class="mt-2"><div class="w-full bg-gray-700 rounded-full h-2"><div class="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-1000" style="width:' + pct + '%"></div></div>' +
                '<div class="flex justify-between text-xs text-gray-500 mt-1"><span>' + fmt(t.position) + '</span><span>' + fmt(t.duration) + '</span></div></div></div>' + controls + '</div>' +
                '<div class="flex items-center gap-4"><span class="text-sm text-gray-500"><i class="fas fa-list mr-1"></i>Fila: ' + p.queue_size + ' musicas</span>' +
                (t.uri ? '<a href="' + t.uri + '" target="_blank" class="text-sm text-purple-400 hover:text-purple-300"><i class="fas fa-external-link-alt mr-1"></i>Abrir</a>' : '') + '</div>' : '<div class="text-center py-8 text-gray-500"><i class="fas fa-pause-circle text-3xl mb-2"></i><p>Player conectado sem musica</p></div>';
            return '<div class="bg-[#161b22] border border-gray-800 rounded-xl p-6 hover:border-purple-500/30 transition-all">' +
                '<div class="flex items-start justify-between mb-4"><div class="flex items-center gap-4"><div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-white"><i class="fas fa-music"></i></div>' +
                '<div><h3 class="font-semibold text-white text-lg">' + p.guild_name + '</h3><p class="text-sm text-gray-500">#' + p.channel + ' &middot; ' + p.bot_name + '</p></div></div>' +
                '<div class="flex items-center gap-2"><span class="text-sm text-gray-400"><i class="fas fa-volume-up mr-1"></i>' + p.volume + '%</span>' +
                '<span class="px-3 py-1 rounded-full text-xs font-medium ' + (p.is_paused ? 'bg-yellow-500/10 text-yellow-400' : 'bg-green-500/10 text-green-400') + '">' + (p.is_paused ? '<i class="fas fa-pause mr-1"></i>Pausado' : '<i class="fas fa-play mr-1"></i>Tocando') + '</span></div></div>' + nowPlaying + '</div>';
        }).join('');
    } catch(e) { c.innerHTML = '<div class="text-center py-12 text-red-400"><i class="fas fa-exclamation-circle text-3xl mb-4"></i><p>Erro: ' + e.message + '</p></div>'; }
}
async function controlPlayer(g, a) {
    try { await fetch(API+'/api/player/'+g+'/control?action='+a); setTimeout(refreshPlayers, 500); } catch(e) {}
}
document.addEventListener('DOMContentLoaded', refreshPlayers);
setInterval(refreshPlayers, 10000);
</script>""", "players"))

@app.get("/servers", response_class=HTMLResponse)
async def servers_page(request: Request):
    return HTMLResponse(render("Servidores", """<div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-8">
        <div><h2 class="text-3xl font-bold text-white">Servidores</h2><p class="text-gray-500 mt-1">Onde o Anubis esta presente</p></div>
        <input id="searchInput" type="text" placeholder="Buscar..." class="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none">
    </div>
    <div id="serversContainer" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="text-center py-16 text-gray-500 col-span-full"><i class="fas fa-spinner fa-spin text-3xl mb-4"></i><p>Carregando...</p></div>
    </div>
</div>
<script>
async function loadServers() {
    var c = document.getElementById('serversContainer');
    try {
        var r = await fetch(API+'/api/servers'), d = await r.json();
        if (d.error || !d.servers || !d.servers.length) { c.innerHTML = '<div class="text-center py-16 text-gray-500 col-span-full"><i class="fas fa-server text-6xl mb-4 opacity-20"></i><p class="text-xl font-medium text-gray-400">Nenhum servidor</p></div>'; return; }
        c.innerHTML = d.servers.map(function(s) {
            var icon = s.icon ? '<img src="' + s.icon + '" class="w-12 h-12 rounded-full">' : '<div class="w-12 h-12 rounded-full bg-gray-700 flex items-center justify-center text-xl font-bold text-gray-400">' + s.name[0] + '</div>';
            var playerInfo = s.has_player ? '<div class="mt-3 pt-3 border-t border-gray-800"><div class="flex items-center justify-between"><span class="text-xs text-purple-400"><i class="fas fa-music mr-1"></i>' + (s.current_track ? s.current_track.substring(0,40)+'...' : 'Conectado') + '</span><span class="w-2 h-2 rounded-full ' + (s.is_playing ? 'bg-green-500' : 'bg-yellow-500') + '"></span></div></div>' : '';
            return '<div class="bg-[#161b22] border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-all relative">' +
                '<div class="flex items-center gap-4 mb-4">' + icon + '<div class="min-w-0"><h3 class="font-semibold text-white truncate">' + s.name + '</h3><p class="text-xs text-gray-500">ID: ' + s.id + '</p></div></div>' +
                '<div class="flex items-center justify-between text-sm"><div class="flex items-center gap-4 text-gray-400"><span><i class="fas fa-users mr-1"></i>' + s.members + '</span><span><i class="fas fa-hashtag mr-1"></i>' + s.channels + '</span></div>' +
                '<span class="text-xs"><i class="fas fa-robot mr-1"></i>' + s.bot_name + '</span></div>' + playerInfo +
                '<button onclick="leaveServer(\\'' + s.id + '\\',\\'' + s.name.replace(/'/g,"") + '\\')" class="mt-3 w-full bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg px-3 py-2 text-sm transition flex items-center justify-center gap-2"><i class="fas fa-sign-out-alt"></i> Sair do Servidor</button></div>';
        }).join('');
    } catch(e) { c.innerHTML = '<div class="text-center py-12 text-red-400 col-span-full"><i class="fas fa-exclamation-circle text-3xl mb-4"></i><p>Erro: ' + e.message + '</p></div>'; }
}
async function leaveServer(gid, name) {
    if (!confirm('Tem certeza que deseja que o Anubis saia do servidor "' + name + '"?')) return;
    var btn = event.target;
    if (btn.tagName != 'BUTTON') btn = btn.closest('button');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saindo...';
    btn.disabled = true;
    try {
        var r = await fetch(API+'/api/server/'+gid+'/leave', {method:'POST'}), d = await r.json();
        if (d.success) { btn.innerHTML = '<i class="fas fa-check"></i> Saiu!'; setTimeout(loadServers, 2000); }
        else { btn.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + (d.error||'Erro'); btn.disabled = false; }
    } catch(e) { btn.innerHTML = '<i class="fas fa-exclamation-circle"></i> Erro'; btn.disabled = false; }
}
document.addEventListener('DOMContentLoaded', loadServers);
document.getElementById('searchInput').addEventListener('input', function() {
    var q = this.value.toLowerCase();
    var cards = document.querySelectorAll('#serversContainer > div:not(.text-center)');
    for (var i = 0; i < cards.length; i++) {
        var name = (cards[i].querySelector('h3')?.textContent || '').toLowerCase();
        cards[i].style.display = name.includes(q) ? '' : 'none';
    }
});
</script>""", "servers"))

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    return HTMLResponse(render("Logs", """<div class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-8">
        <div><h2 class="text-3xl font-bold text-white">Logs</h2><p class="text-gray-500 mt-1">Atividades do sistema</p></div>
        <button onclick="refreshLogs()" class="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg transition text-sm"><i class="fas fa-sync-alt"></i> Atualizar</button>
    </div>
    <div class="bg-[#0d1117] border border-gray-800 rounded-xl overflow-hidden">
        <div class="bg-gray-900/50 px-6 py-3 border-b border-gray-800 flex items-center gap-2 text-sm text-gray-400">
            <i class="fas fa-terminal text-green-400"></i><span>disnake.log</span><span class="ml-auto text-xs" id="logCount">0</span>
        </div>
        <div id="logContainer" class="p-4 font-mono text-xs leading-relaxed overflow-y-auto max-h-[70vh]" style="background:#0a0e14;">
            <div class="text-center py-8 text-gray-600"><i class="fas fa-spinner fa-spin text-2xl mb-2"></i><p>Carregando...</p></div>
        </div>
    </div>
</div>
<script>
async function refreshLogs() {
    var c = document.getElementById('logContainer'), cnt = document.getElementById('logCount');
    try {
        var r = await fetch(API+'/api/logs?limit=200'), d = await r.json();
        if (d.error || !d.logs || !d.logs.length) { c.innerHTML = '<div class="text-center py-8 text-gray-600"><i class="fas fa-info-circle text-2xl mb-2"></i><p>Ative ENABLE_LOGGER=true no .env</p></div>'; cnt.textContent='0'; return; }
        cnt.textContent = d.logs.length + ' linhas';
        c.innerHTML = d.logs.map(function(l) {
            var cls = 'text-gray-300';
            if (l.text.includes('ERROR')||l.text.includes('Error')||l.text.includes('Falha')) cls = 'text-red-400';
            else if (l.text.includes('WARNING')||l.text.includes('Aten')) cls = 'text-yellow-400';
            else if (l.text.includes('Online')||l.text.includes('pronto')) cls = 'text-green-400';
            else if (l.text.includes('DEBUG')) cls = 'text-gray-600';
            return '<div class="'+cls+' hover:bg-gray-800/30 px-2 py-0.5 rounded">'+l.text+'</div>';
        }).join('');
        c.scrollTop = c.scrollHeight;
    } catch(e) { c.innerHTML = '<div class="text-center py-8 text-red-400"><p>Erro: '+e.message+'</p></div>'; }
}
document.addEventListener('DOMContentLoaded', refreshLogs);
setInterval(refreshLogs, 15000);
</script>""", "logs"))

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return HTMLResponse(render("Configuracoes", """<div class="max-w-4xl mx-auto">
    <div class="mb-8">
        <h2 class="text-3xl font-bold text-white">Configuracoes</h2>
        <p class="text-gray-500 mt-1">Edite e salve</p>
    </div>
    <div id="configMsg" class="hidden mb-4 p-4 rounded-lg text-sm"></div>
    <div class="bg-[#161b22] border border-gray-800 rounded-xl overflow-hidden">
        <div class="p-6 border-b border-gray-800 flex items-center gap-2">
            <i class="fas fa-sliders-h text-purple-400"></i>
            <h3 class="font-semibold text-white">Configuracoes Carregadas</h3>
        </div>
        <div id="configItems" class="divide-y divide-gray-800/50">
            <div class="text-center py-8 text-gray-500"><i class="fas fa-spinner fa-spin text-2xl mb-2"></i><p>Carregando...</p></div>
        </div>
    </div>
    <div class="flex justify-end mt-6">
        <button onclick="saveConfig()" class="flex items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-lg font-medium hover:opacity-90 transition"><i class="fas fa-save"></i> Salvar Alteracoes</button>
    </div>
</div>
<script>
var configData = {};
async function loadConfig() {
    try {
        var r = await fetch(API+'/api/config'), d = await r.json();
        if (d.error) { document.getElementById('configItems').innerHTML = '<div class="text-center py-8 text-red-400"><p>API indisponivel</p></div>'; return; }
        configData = d;
        document.getElementById('configItems').innerHTML = Object.keys(d).map(function(k) {
            var v = d[k];
            if (k == 'TOKEN' || k.includes('SECRET') || k.includes('WEBHOOK')) return '';
            var input;
            if (v === true || v === false) {
                input = '<select id="cfg_'+k+'" class="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white focus:border-purple-500 focus:outline-none"><option value="true"'+(v?' selected':'')+'>true</option><option value="false"'+(v?'':' selected')+'>false</option></select>';
            } else if (typeof v === 'number') {
                input = '<input id="cfg_'+k+'" type="number" value="'+v+'" class="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white w-32 focus:border-purple-500 focus:outline-none">';
            } else {
                input = '<input id="cfg_'+k+'" type="text" value="'+((v||'')+'')+'" class="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white w-full max-w-md focus:border-purple-500 focus:outline-none">';
            }
            return '<div class="flex items-center justify-between px-6 py-3 hover:bg-gray-800/30 transition"><span class="text-sm font-mono text-gray-300">'+k+'</span>'+input+'</div>';
        }).join('');
    } catch(e) { document.getElementById('configItems').innerHTML = '<div class="text-center py-8 text-red-400"><p>Erro: '+e.message+'</p></div>'; }
}
async function saveConfig() {
    var msg = document.getElementById('configMsg');
    var updated = {};
    Object.keys(configData).forEach(function(k) {
        var el = document.getElementById('cfg_'+k);
        if (!el) return;
        var v = el.value;
        if (configData[k] === true || configData[k] === false) v = v === 'true';
        else if (typeof configData[k] === 'number') v = parseFloat(v);
        updated[k] = v;
    });
    try {
        var r = await fetch(API+'/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(updated)});
        var d = await r.json();
        msg.className = 'mb-4 p-4 rounded-lg text-sm ' + (d.success ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-red-500/10 border border-red-500/30 text-red-400');
        msg.innerHTML = d.success ? '<i class="fas fa-check-circle mr-2"></i>Config salva! Reinicie o bot para aplicar. Campos alterados: '+(d.changed||[]).join(', ') : '<i class="fas fa-exclamation-circle mr-2"></i>Erro: '+(d.error||'desconhecido');
        msg.classList.remove('hidden');
        setTimeout(function(){msg.classList.add('hidden');}, 5000);
    } catch(e) {
        msg.className = 'mb-4 p-4 rounded-lg text-sm bg-red-500/10 border border-red-500/30 text-red-400';
        msg.innerHTML = '<i class="fas fa-exclamation-circle mr-2"></i>Erro: '+e.message;
        msg.classList.remove('hidden');
    }
}
document.addEventListener('DOMContentLoaded', loadConfig);
</script>""", "settings"))

# ─── API Proxy Routes ────────────────────────────────────────────────
# Proxies requests from the frontend (same origin) to the internal
# Tornado API running on BOT_API_URL (http://localhost:8080).
# This avoids CORS issues and hardcoded public IPs.

OFFLINE = {"error": "API Offline", "detail": f"backend={BOT_API_URL}"}

async def _proxy(method: str, endpoint: str, **kwargs) -> JSONResponse:
    url = f"{BOT_API_URL}/{endpoint.lstrip('/')}"
    try:
        async with app.state.http_session.request(method, url, timeout=kwargs.pop("timeout", PROXY_TIMEOUT), **kwargs) as resp:
            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                return JSONResponse({"error": text}, status_code=resp.status)
            return JSONResponse(data)
    except ClientConnectorError as e:
        print(f"[PROXY] ClientConnectorError para {url}: {e}")
        return JSONResponse(OFFLINE, status_code=503)
    except asyncio.TimeoutError:
        print(f"[PROXY] TimeoutError para {url}")
        return JSONResponse({**OFFLINE, "error": "API Offline (timeout)"}, status_code=504)
    except ClientError as e:
        print(f"[PROXY] ClientError para {url}: {type(e).__name__}: {e}")
        return JSONResponse(OFFLINE, status_code=503)
    except Exception:
        print(f"[PROXY] Erro inesperado para {url}:")
        _tb.print_exc()
        return JSONResponse(OFFLINE, status_code=500)

@app.get("/api/stats")
async def proxy_api_stats():
    return await _proxy("GET", "/api/stats")

@app.get("/api/players")
async def proxy_api_players():
    return await _proxy("GET", "/api/players")

@app.get("/api/servers")
async def proxy_api_servers():
    return await _proxy("GET", "/api/servers")

@app.get("/api/config")
async def proxy_api_config_get():
    return await _proxy("GET", "/api/config")

@app.post("/api/config")
async def proxy_api_config_post(request: Request):
    body = await request.json()
    return await _proxy("POST", "/api/config", json=body)

@app.get("/api/logs")
async def proxy_api_logs(request: Request):
    limit = request.query_params.get("limit", 200)
    return await _proxy("GET", f"/api/logs?limit={limit}")

@app.get("/api/player/{guild_id}/control")
async def proxy_api_player_control(guild_id: str, request: Request):
    action = request.query_params.get("action", "")
    return await _proxy("GET", f"/api/player/{guild_id}/control?action={action}")

@app.post("/api/server/{guild_id}/leave")
async def proxy_api_server_leave(guild_id: str):
    return await _proxy("POST", f"/api/server/{guild_id}/leave")

@app.get("/api/ping")
async def proxy_api_ping():
    return JSONResponse({"status": "ok", "backend": BOT_API_URL, "timeout": PROXY_TIMEOUT})

@app.get("/api/{path:path}")
async def proxy_api_catch_all(path: str, request: Request):
    qs = str(request.query_params)
    endpoint = f"/api/{path}"
    if qs:
        endpoint += f"?{qs}"
    return await _proxy("GET", endpoint)

def run(host="0.0.0.0", port=3000):
    import uvicorn
    print(f"\n{'=' * 50}")
    print(f"  Anubis Web Dashboard")
    print(f"  URL: http://localhost:{port}")
    print(f"  API do Bot (backend): {BOT_API_URL}")
    print(f"{'=' * 50}\n")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run()
