
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.main import main_keyboard
from database.models import HomeworkDB


router = Router()


homework_db = HomeworkDB()

@router.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    if homework_db.is_moderator(user_id):
        await message.answer(
            "👑 Добро пожаловать, модератор!\n"
            "Вы можете добавлять и просматривать задания.",
            reply_markup=main_keyboard()
        )
    else:
        await message.answer(
            "👋 Добро пожаловать!\n"
            "Вы можете просматривать задания.\n"
            "Для добавления нужны права модератора.",
            reply_markup=main_keyboard()
        )

@router.message(Command("help"))
async def help_command(message: types.Message):
    """Обработчик команды /help"""
    help_text = """📚 Помощь по боту:

🚀 ОСНОВНЫЕ КОМАНДЫ:
• /start - Начать работу
• /login - Вход для модераторов  
• /ping - Проверить скорость бота
• /help - Эта справка

👑 КОМАНДЫ СОЗДАТЕЛЯ (только создатель):
• /get_my_password - Получить пароль
• /create_moderator - Создать модератора
• /list_moderators - Список модераторов

💾 УПРАВЛЕНИЕ ХРАНИЛИЩЕМ (только создатель):
• /storage_mode - Текущий режим хранения
• /cloud_status - Статус облачного хранилища

🔄 РЕЖИМЫ ХРАНЕНИЯ (только создатель):
• /mode_local - Только локальное хранение
• /mode_cloud - Только облачное хранение
• /mode_both - Локальное + облачное (по умолчанию)
• /mode_mirror - Зеркалирование (в обоих местах)

📦 БЭКАПЫ (только создатель):
• /create_backup - Создать резервную копию
• /backup_status - Статус бэкапов

📝 УПРАВЛЕНИЕ ЗАДАНИЯМИ:
• Кнопки в меню для заданий
• Просмотр: /view_[ID] (например: /view_123)
• Удаление: /delete [ID] (например: /delete 123)
• Просмотр файла: /file_[ID] (например: /file_456)"""
    
    await message.answer(help_text)


# Обработчики кнопок из главного меню
@router.message(F.text == "ℹ️ Помощь")
async def help_button(message: types.Message):
    """Обработчик кнопки 'Помощь'"""
    await help_command(message)

@router.message(F.text == "↩️ Назад")
async def back_button(message: types.Message):
    """Обработчик кнопки 'Назад'"""
    await message.answer("Главное меню:", reply_markup=main_keyboard())