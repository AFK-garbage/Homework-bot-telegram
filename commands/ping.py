
import time
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("ping"))
async def ping_cmd(message: Message):
    start = time.time()
    await message.answer("🏓 Понг!")
    ms = (time.time() - start) * 1000
    speed = "⚡ ОТЛИЧНО" if ms < 1000 else "✅ НОРМАЛЬНО" if ms < 3000 else "🐌 МЕДЛЕННО"
    await message.answer(f"📊 Ответ за {ms:.0f} мс — {speed}")
