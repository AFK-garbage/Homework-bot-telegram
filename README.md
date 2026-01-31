# 📚 Homework Bot | Бот для ДЗ

**RU:** CRM для управления домашними заданиями через Telegram с облачным бэкапом и ролевой моделью.  
**EN:** Telegram-based CRM for homework management with cloud backup and RBAC.

---

## 🛠 Стек | Stack

- **aiogram 3.x** — async Telegram framework
- **SQLite** (v1) → PostgreSQL (v2) | Лёгкая миграция через SQLAlchemy
- **Yandex Cloud** — S3-compatible object storage
- **Architecture:** Repository Pattern, FSM (Finite State Machine), Middleware rate-limiting

---

## 🚀 Быстрый старт | Quick Start

```bash
# 1. Clone | Клонирование
git clone https://github.com/AFK-garbage/Homework-bot-telegram.git
cd Homework-bot-telegram

# 2. Environment | Окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Config | Конфигурация
cp .env.example .env
# Edit .env with your credentials | Отредактируйте данные

# 4. Run | Запуск
python bot.py
```

---

## ✨ Фичи | Features

**RU:**
- 🔐 **RBAC**: Создатель → Модератор → Пользователь
- ☁️ **Hybrid Storage**: Локально + Yandex Cloud (mirror-режим)
- 🛡️ **Anti-DDoS**: Rate limit 30 req/min + авто-блокировка флуда
- 📎 **Файлы**: До 50МБ, автобэкап каждые 3 дня

**EN:**
- 🔐 **RBAC**: Creator → Moderator → User hierarchy  
- ☁️ **Hybrid Storage**: Local + Yandex Cloud (mirror mode)
- 🛡️ **Anti-DDoS**: Rate limiting + flood protection  
- 📎 **Files**: Up to 50MB, auto-backup every 3 days

---

## 📝 Лицензия | License

MIT — свободное использование / free to use.
Author: @AFK-garbage
Contacts: [t.me/AFKgarbage]
