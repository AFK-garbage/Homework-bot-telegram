from aiogram import Bot, Dispatcher
from loader import dp, bot, backup_system
from middlewares.rate_limit import UserLockMiddleware
from commands import all_routers
import asyncio

# Регистрация middleware
dp.message.middleware(UserLockMiddleware())

# Регистрация роутеров
for router in all_routers:
    dp.include_router(router)

async def main():
    # Запуск авто-бэкапов
    asyncio.create_task(backup_system.start_auto_backups(days_interval=3))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())