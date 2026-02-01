# loader.py
from database import crud
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, YOUR_USER_ID, CREATOR_PASSWORD
from storage.storage_manager import HybridStorage, BackupSystem
from storage.yandex_storage import YandexCloudStorage
from database.base import init_db, async_session  # Импортируем
from database import crud  # CRUD операции
import asyncio

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


storage = None
backup_system = None

async def init_storage():
    """Асинхронная инициализация (вызывать в on_startup)"""
    global storage, backup_system
    

    await init_db()
    

    async with async_session() as session:
        await crud.create_moderator(session, YOUR_USER_ID, YOUR_USER_ID, CREATOR_PASSWORD)
        print(f"✅ Модератор проверен/создан")
    

    from config import YANDEX_CLOUD_ENABLED, CLOUD_ACCESS_KEY, CLOUD_SECRET_KEY, CLOUD_BUCKET, YANDEX_CLOUD_REGION
    

    print("✅ Storage инициализирован")

__all__ = ['bot', 'dp', 'storage', 'backup_system', 'async_session', 'crud', 'CREATOR_PASSWORD']