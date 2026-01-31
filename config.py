import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
BOT_TOKEN = str(os.getenv("TOKEN"))
YOUR_USER_ID = int(os.getenv("CREATOR_ID"))


CREATOR_ID = YOUR_USER_ID 

CREATOR_PASSWORD = str(os.getenv("CREATOR_PASSWORD"))
DB_NAME = "homework.db"

YANDEX_CLOUD_ENABLED =  True 
YANDEX_CLOUD_ACCESS_KEY = os.getenv("CLOUD_ACCESS_KEY")
YANDEX_CLOUD_SECRET_KEY = os.getenv("CLOUD_SECRET_KEY")
YANDEX_CLOUD_BUCKET = os.getenv("CLOUD_BUCKET")
YANDEX_CLOUD_REGION = "ru-central1"

# Ограничения
MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_FILES_PER_HOMEWORK = 10
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.png', '.txt'}