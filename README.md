
```markdown
# 📚 Homework Bot v2.0 | Бот для ДЗ

**RU:** Telegram CRM для управления домашними заданиями. Переписано на SQLAlchemy ORM + Alembic.  
**EN:** Telegram CRM for homework management. Rewritten with SQLAlchemy 2.0 ORM + Alembic.

---

## 🆕 Что нового в v2.0 | What's new

- **SQLAlchemy 2.0** — async ORM вместо сырого SQL
- **Alembic** — миграции базы данных (версионирование схемы)
- **Repository Pattern** — чистое разделение моделей и логики  - - **Docker** — контейнеризация для легкого деплоя

---

## 🛠 Стек | Stack

**Core:** `aiogram 3.x` `SQLAlchemy 2.0` `Alembic` `SQLite`  
**Cloud:** `Yandex Object Storage` (S3)  
**Architecture:** `Repository Pattern` `FSM` `Middleware Rate-limiting` `Unit of Work`
---

## 🚀 Быстрый старт | Quick Start

### Вариант 1: Python (локально) | Local Python

```bash
# 1. Clone
git clone https://github.com/AFK-garbage/Homework-bot-telegram.git 
cd Homework-bot-telegram

# 2. Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Database migrations (Alembic)
alembic upgrade head

# 4. Config
cp .env.example .env
# Edit .env with your TOKEN, CREATOR_ID

# 5. Run
python bot.py
```

### Вариант 2: Docker | Container

```bash
# 1. Clone & Config
git clone https://github.com/AFK-garbage/Homework-bot-telegram.git
cd Homework-bot-telegram
cp .env.example .env
# Edit .env

# 2. Run (_one command_)
docker-compose up -d
```

---


## ✨ Фичи | Features

**RU:**
- 🔐 **RBAC**: Создатель → Модератор → Пользователь  
- ☁️ **Hybrid Storage**: Локально + Yandex Cloud  
- 🛡️ **Anti-DDoS**: Rate limit 30 req/min  
- 📎 **Файлы**: До 50МБ, автобэкап каждые 3 дня  
- 🗃️ **Миграции**: Версионирование схемы БД (Alembic)

**EN:**
- 🔐 **RBAC**: Creator → Moderator → User hierarchy
- ☁️ **Hybrid Storage**: Local + Yandex Cloud
- 🛡️ **Anti-DDoS**: Rate limiting 30 req/min
- 📎 **Files**: Up to 50MB, auto-backup every 3 days
- 🗃️ **Migrations**: Database schema versioning (Alembic)

---

## ⚙️ Переменные окружения | Environment

```env
TOKEN=your_bot_token
CREATOR_ID=your_telegram_id
CREATOR_PASSWORD=admin_password

# Optional | Опционально:
YANDEX_CLOUD_ENABLED=false
CLOUD_ACCESS_KEY=
CLOUD_SECRET_KEY=
CLOUD_BUCKET=
```

---

## 📝 Лицензия | License

MIT — свободное использование / free to use.  
**Author:** @AFK-garbage  
**Contacts:** [t.me/AFKgarbage]



