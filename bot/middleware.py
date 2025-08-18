from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from .db import SessionLocal

class DBSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        async with SessionLocal() as session:
            data["session"] = session
            return await handler(event, data)
