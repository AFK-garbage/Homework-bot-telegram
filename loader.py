# loader.py

import os
from aiogram import Bot, Dispatcher
from database.models import HomeworkDB
from storage.storage_manager import HybridStorage, BackupSystem
from storage.yandex_storage import YandexCloudStorage
from config import (
    BOT_TOKEN, YOUR_USER_ID, CREATOR_PASSWORD, 
    YANDEX_CLOUD_ENABLED, YANDEX_CLOUD_ACCESS_KEY, 
    YANDEX_CLOUD_SECRET_KEY, YANDEX_CLOUD_BUCKET, YANDEX_CLOUD_REGION
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

homework_db = HomeworkDB()
files_directory = homework_db.files_dir
print(f"✅ Папка для файлов: {files_directory}")

# === НАСТРОЙКА ОБЛАЧНОГО ХРАНИЛИЩА ===
cloud_config = {
    'enabled': YANDEX_CLOUD_ENABLED,
}

if YANDEX_CLOUD_ENABLED:
 
    yandex_storage = YandexCloudStorage(
        access_key=YANDEX_CLOUD_ACCESS_KEY,
        secret_key=YANDEX_CLOUD_SECRET_KEY,
        bucket=YANDEX_CLOUD_BUCKET,
        region=YANDEX_CLOUD_REGION
    )
    cloud_config['provider'] = yandex_storage
    print("☁️ Облачное хранилище: Yandex Cloud (АКТИВНО)")
else:
    cloud_config['provider'] = 'simulated'
    print("☁️ Облачное хранилище: Симуляция (ОТКЛЮЧЕНО)")

# === ИНИЦИАЛИЗАЦИЯ ХРАНИЛИЩА ===
storage = HybridStorage(
    local_config={'base_path': files_directory},
    cloud_config=cloud_config
)

backup_system = BackupSystem(storage, backup_dir=os.path.join(files_directory, 'backups'))

# Создание модератора
homework_db.create_moderator(YOUR_USER_ID, YOUR_USER_ID, CREATOR_PASSWORD)

__all__ = ['bot', 'dp', 'homework_db', 'storage', 'backup_system']