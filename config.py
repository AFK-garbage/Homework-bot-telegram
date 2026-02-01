import os
from dotenv import load_dotenv

load_dotenv()

def load_env_without_bom(filepath='.env'):
    """Загружает .env файл, удаляя BOM если есть"""
    env_vars = {}
    try:
        # Пробуем разные кодировки
        for encoding in ['utf-8-sig', 'utf-8', 'cp1251']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                env_vars[key.strip()] = value.strip()
                break  # Если прочитали успешно
            except UnicodeDecodeError:
                continue
    except FileNotFoundError:
        print(f"Файл {filepath} не найден")
    return env_vars

env_vars = load_env_without_bom()


BOT_TOKEN = env_vars.get("TOKEN")
YOUR_USER_ID = env_vars.get("CREATOR_ID")
CREATOR_PASSWORD = env_vars.get("CREATOR_PASSWORD")
CREATOR_ID = YOUR_USER_ID 

DB_NAME = "homework.db"

YANDEX_CLOUD_ENABLED =  True 
CLOUD_ACCESS_KEY = env_vars.get("CLOUD_ACCESS_KEY")
CLOUD_SECRET_KEY = env_vars.get("CLOUD_SECRET_KEY")
CLOUD_BUCKET = env_vars.get("CLOUD_BUCKET")
YANDEX_CLOUD_REGION = "ru-central1"


MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_FILES_PER_HOMEWORK = 10
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.png', '.txt'}