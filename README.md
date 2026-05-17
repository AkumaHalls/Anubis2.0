<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=Anubis%20Music%20Bot%20v2.0&fontSize=40&fontAlignY=35&animation=fadeIn" width="100%"/>

<div align="center">

# 🎵 **Anubis Music Bot** — A Melodia que seu Servidor Merece!

<img src="https://img.shields.io/badge/Python-3.14+-blue?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/disnake-2.12+-purple?style=for-the-badge&logo=discord&logoColor=white"/>
<img src="https://img.shields.io/badge/Wavelink-3.5+-brightgreen?style=for-the-badge&logo=discord&logoColor=white"/>
<img src="https://img.shields.io/badge/Lavalink-4.0-red?style=for-the-badge&logo=discord&logoColor=white"/>
<img src="https://img.shields.io/badge/FastAPI-⚡-green?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/license-GPL--2.0-orange?style=for-the-badge"/>

<br/>

> **Transforme seu Discord em uma potência musical!** Suporte a múltiplas fontes, cluster multi-bot, dashboard web elegante e muito mais.

<br/>

[🌟 Recursos](#-recursos) • [🎮 Comandos](#-comandos) • [⚙️ Configuração](#%EF%B8%8F-configuração) • [🌐 Dashboard](#-dashboard-web) • [🚀 Começando](#-começando) • [📦 Dependências](#-dependências)

<br/>

</div>

---

## 🌟 **Recursos**

### 🎶 **Reprodução Multifonte**
Toque músicas do **YouTube**, **SoundCloud**, **Spotify**, **Deezer**, **Apple Music**, **Twitch**, **Bandcamp**, **Vimeo**, **Mixcloud**, **TikTok**, **JioSaavn**, **Tidal** e mais — direto no seu servidor!

### 🧠 **Sistema Multi-Bot**
Execute **vários bots** simultaneamente sob um mesmo pool. Distribua carga entre servidores, atribua bots específicos por servidor, escale horizontalmente.

### 🔥 **Cluster Lavalink Automatizado**
- Servidor Lavalink **local** auto-gerenciado (download automático do `.jar`)
- Suporte a **múltiplos nodes remotos** via `lavalink.ini`
- Lista pública de servidores **atualizada automaticamente**
- Plugins inclusos: **YouTube OAuth**, **Spotify/Apple Music/Deezer** (lavasrc), **Lyrics**

### 🌐 **Dashboard Web Poderoso**
Painel completo em **FastAPI + Tailwind CSS + Chart.js**:
- 📊 **Visão geral** com estatísticas em tempo real
- 🎧 **Players ativos** com controles (play, pause, skip, stop)
- 🖥️ **Servidores** — veja todos os servidores, saia de qualquer um
- 📋 **Logs do sistema** com filtro por nível
- ⚙️ **Configurações** — edite o `.env` pelo navegador

### 🎨 **Sistema de Skins Personalizáveis**
Escolha entre dezenas de **skins animadas e estáticas** para o player. Crie suas próprias skins em JSON. Configure skin global ou por servidor.

### 🔄 **Resumo de Sessões**
O bot **salva e restaura** filas e estados do player automaticamente. Reinicie sem perder nada!

### 🎤 **Letras das Músicas**
Integração com o plugin Lavalink Lyrics — exiba letras em tempo real com `/lyrics`.

### 📡 **RPC / Rich Presence**
Compartilhe o que está ouvindo com amigos via **listen-along**. Suporte a aplicativo desktop para Rich Presence.

### 🎵 **Last.fm Scrobbling**
Conecte sua conta do Last.fm e registre automaticamente todas as músicas tocadas.

### 👑 **Sistema DJ + Permissões**
Controle fino de quem pode fazer o quê. Adicione cargos DJ, modo restrito por canal.

---

## 🎮 **Comandos**

### ▶️ **Reprodução**
| Comando | Descrição |
|---------|-----------|
| `/play` | Toque uma música por nome ou link |
| `/search` | Pesquise e selecione manualmente |
| `/connect` | Conecte a um canal de voz |
| `/stop` | Pare a reprodução e saia do canal |
| `/pause` / `/resume` | Pause ou continue a música |
| `/skip` | Pule para a próxima faixa |
| `/back` | Volte para a faixa anterior |
| `/seek` | Avance para uma posição específica |
| `/volume` | Ajuste o volume (0-100%) |
| `/nowplaying` | Veja o que está tocando agora |

### 📋 **Fila**
| Comando | Descrição |
|---------|-----------|
| `/queue` | Exiba a fila de músicas |
| `/remove` | Remova uma música da fila |
| `/clear` | Limpe toda a fila |
| `/move` | Mova uma música na fila |
| `/shuffle` | Embaralhe a fila |
| `/reverse` | Inverta a ordem da fila |
| `/loop` | Ative o loop (faixa/fila/desligado) |
| `/readd` | Re-adicione músicas tocadas |
| `/rotate` | Rotacione as posições da fila |
| `/save_queue` | Salve a fila para depois |

### 🎛️ **Modos de Reprodução**
| Comando | Descrição |
|---------|-----------|
| `/nightcore` | Ative o efeito nightcore |
| `/autoplay` | Recomendações automáticas ao fim da fila |
| `/247` | Modo 24/7 — não sai mesmo sozinho |
| `/restrictmode` | Restringe músicas a um canal |
| `/controller` | Envie o player interativo |
| `/songrequestthread` | Crie um thread de pedidos |

### ❤️ **Favoritos**
| Comando | Descrição |
|---------|-----------|
| `/fav_manager` | Gerencie favoritos e integrações |
| `/addposition` | Adicione música em posição específica |

### ⚙️ **Configuração**
| Comando | Descrição |
|---------|-----------|
| `/setup` | Assistente de configuração interativo |
| `/player_settings` | Selecione skins do player |
| `/add_dj` / `/remove_dj` | Gerencie cargos DJ |
| `/set_voice_status` | Status automático do canal |
| `/listen_along` | Convide outros para ouvir |

### ℹ️ **Informações**
| Comando | Descrição |
|---------|-----------|
| `/help` | Menu de ajuda interativo |
| `/about` | Informações do bot |
| `/invite` | Link de convite |
| `/avatar` | Veja o avatar de alguém |
| `/lyrics` | Veja a letra da música atual |

---

## ⚙️ **Configuração**

O bot é configurado via arquivo `.env` na raiz. Veja as principais opções:

### 🔐 **Essenciais**
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `TOKEN` | — | Token do seu bot Discord |
| `OWNER_IDS` | — | IDs dos donos (separados por pipe) |
| `DEFAULT_PREFIX` | `!!` | Prefixo para comandos de texto |

### 🎵 **Música**
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SEARCH_PROVIDERS` | `ytsearch scsearch` | Fontes de pesquisa (ordem = prioridade) |
| `PREFER_YOUTUBE_NATIVE_PLAYBACK` | `True` | Usar YouTube nativo quando possível |
| `IDLE_TIMEOUT` | `180` | Tempo até desconectar (segundos) |
| `QUEUE_MAX_ENTRIES` | `0` | Limite da fila (0 = ilimitado) |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | — | API do Spotify |

### 🌋 **Lavalink**
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `RUN_LOCAL_LAVALINK` | `True` | Rodar servidor Lavalink local |
| `CONNECT_LOCAL_LAVALINK` | `True` | Conectar ao servidor local |
| `AUTO_DOWNLOAD_LAVALINK_SERVERLIST` | `True` | Baixar servidores públicos |
| `LAVALINK_RAM_LIMIT` | `120` | RAM máxima para Lavalink (MB) |
| `LAVALINK_RECONNECT_RETRIES` | `30` | Tentativas de reconexão |

### 🌐 **Dashboard Web**
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `RUN_RPC_SERVER` | `True` | Ativar servidor web/RPC |
| `PORT` | `8080` | Porta do servidor web |

### 🎨 **Presença**
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LISTENING_PRESENCES` | — | Status "Ouvindo" (placeholders: `{players_count}`, `{guild_count}`) |
| `PLAYING_PRESENCES` | — | Status "Jogando" |
| `WATCHING_PRESENCES` | — | Status "Assistindo" |
| `PRESENCE_INTERVAL` | `900` | Intervalo de rotação (segundos) |

> 💡 **Dica**: Use placeholders como `{players_count}`, `{guild_count}`, `{users_count}`, `{owner}` nas presenças!

---

## 🌐 **Dashboard Web**

O dashboard web rodando em **FastAPI + Chart.js** oferece:

| Rota | Descrição |
|------|-----------|
| `/` | Visão geral com stats cards, gráficos e tabela de bots |
| `/players` | Players ativos com controles e barra de progresso |
| `/servers` | Todos os servidores com busca e botão "Sair" |
| `/logs` | Visualizador de logs com cores por nível |
| `/settings` | Editor de configuração (.env) pelo navegador |

**Endpoints JSON**: `/api/stats`, `/api/players`, `/api/servers`, `/api/config`, `/api/logs`, `/api/player/:id/control`, `/api/server/:id/leave`

> Inicie com: `start_dashboard.bat` ou `uvicorn dashboard.main:app --host 0.0.0.0 --port 3000`

---

## 🚀 **Começando**

### 📋 **Pré-requisitos**
- **Python 3.14+**
- **Java 17+** (para Lavalink local — instalado automaticamente)
- Discord Bot Token ([Portal do Desenvolvedor](https://discord.com/developers/applications))

### ⚡ **Instalação Rápida (Windows)**

```batch
git clone https://github.com/seu-repo/anubis-bot
cd anubis-bot
setup.bat
```

O `setup.bat` cria o venv, instala dependências, baixa Java e prepara tudo.

### 📝 **Configuração Manual**

```bash
# 1. Crie o ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o .env
copy .env.example .env
# Edite o TOKEN no .env

# 4. Inicie o bot
start.bat

# 5. (opcional) Inicie o dashboard em outro terminal
start_dashboard.bat
```

### 🐧 **Linux / Docker**
Adapte os paths e use `source .venv/bin/activate`. O Lavalink requer Java 17+.

---

## 📦 **Dependências**

| Pacote | Uso |
|--------|-----|
| **disnake** 2.12+ | API do Discord |
| **wavelink** 3.5+ | Cliente Lavalink |
| **FastAPI** + **uvicorn** | Dashboard web |
| **Tornado** | Servidor RPC legado |
| **aiohttp** | Requisições assíncronas |
| **yt-dlp** | Fontes adicionais de áudio |
| **motor** / **tinymongo** | Banco de dados (MongoDB / local) |
| **Chart.js** (CDN) | Gráficos do dashboard |
| **Tailwind CSS** (CDN) | Estilo do dashboard |
| **psutil** | Monitoramento do sistema |
| **cachetools** | Cache de banco de dados |
| **python-Levenshtein** | Busca por similaridade |

---

## 🛠️ **Estrutura do Projeto**

```
anubis-bot/
├── main.py                 # Ponto de entrada do bot
├── app.py                  # Atalho para main
├── config_loader.py        # Carregador de configuração
├── modules/                # Cogs do bot
│   ├── music.py            # Comandos de música (~7300 linhas!)
│   ├── music_settings.py   # Skins e configurações
│   ├── misc.py             # Comandos utilitários
│   ├── help_cog.py         # Sistema de ajuda
│   ├── error_handler.py    # Tratamento de erros
│   ├── lastfm.py           # Integração Last.fm
│   ├── legacy_cmds.py      # Comandos de owner
│   ├── player_resume.py    # Persistência de sessão
│   └── server_manager.py   # Gerenciamento de servidores
├── utils/
│   ├── client.py           # BotPool e BotCore
│   ├── db.py               # Sistema de banco de dados
│   ├── web_app.py          # Servidor web Tornado + RPC
│   └── music/              # Utilitários musicais
├── wavelink/               # Cliente wavelink modificado
├── dashboard/              # Dashboard web FastAPI
│   ├── main.py             # Rotas da dashboard
│   └── static/             # CSS e JS
├── plugins/                # Plugins Lavalink (.jar)
├── .env                    # Configuração do bot
├── lavalink.ini            # Nodes Lavalink remotos
├── application.yml         # Config do Lavalink local
├── requirements.txt        # Dependências Python
└── setup.bat / start.bat   # Scripts de inicialização
```

---

## 📜 **Licença**

Este projeto é licenciado sob **GPL-2.0** — veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<div align="center">

### ⚡ **Feito com 💜 pela comunidade Anubis** ⚡

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=150&section=footer&animation=twinkling" width="100%"/>

</div>
