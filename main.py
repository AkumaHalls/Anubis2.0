# -*- coding: utf-8 -*-
import asyncio
import warnings
from platform import python_version

warnings.filterwarnings("ignore", message="dm_permission is deprecated")

from utils.client import BotPool

print(f"🐍 - Versão do python: {python_version()}")

pool = BotPool()

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

pool.setup()
