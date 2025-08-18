import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import settings
from bot.middleware import DBSessionMiddleware
from bot.handlers import router
from bot.db import init_db

# ВКЛЮЧАЕМ ЛОГИ
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

async def main():
    await init_db()
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(DBSessionMiddleware())
    bot = Bot(settings.bot_token)

    # важно: отключаем вебхук перед polling
    await bot.delete_webhook(drop_pending_updates=True)

    dp.include_router(router)
    logger.info("Starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .config import settings
from .db import init_db
from .middleware import DBSessionMiddleware
from .handlers import router

async def main():
    await init_db()
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(DBSessionMiddleware())
    bot = Bot(settings.bot_token)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    # bot/bot.py
import asyncio, logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import settings
from bot.middleware import DBSessionMiddleware
from bot.handlers import router
from bot.db import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

async def main():
    await init_db()
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(DBSessionMiddleware())
    bot = Bot(settings.bot_token)
    await bot.delete_webhook(drop_pending_updates=True)

    dp.include_router(router)
    # ⬇️ Критично: разрешаем все виды апдейтов, которые реально используются
    allowed = dp.resolve_used_update_types()
    logging.info("Allowed updates: %s", allowed)
    await dp.start_polling(bot, allowed_updates=allowed)

if __name__ == "__main__":
    asyncio.run(main())

