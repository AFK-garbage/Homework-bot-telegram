from aiogram import Bot, Dispatcher
from loader import dp, bot, init_storage  # Убрали backup_system из импорта
import loader  # Импортируем модуль целиком
from middlewares.rate_limit import UserLockMiddleware
from commands import all_routers
import asyncio

dp.message.middleware(UserLockMiddleware())

for router in all_routers:
    dp.include_router(router)

async def main():
    # Сначала инициализируем storage (там создается backup_system)
    await init_storage()
    
    # Теперь обращаемся через модуль loader, а не импортированную переменную
    if loader.backup_system:
        asyncio.create_task(loader.backup_system.start_auto_backups(days_interval=3))
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())