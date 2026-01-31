from aiogram import Bot, Dispatcher
from loader import dp, bot, backup_system
from middlewares.rate_limit import UserLockMiddleware
from commands import all_routers
import asyncio


dp.message.middleware(UserLockMiddleware())

for router in all_routers:
    dp.include_router(router)

async def main():
    
    asyncio.create_task(backup_system.start_auto_backups(days_interval=3))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())