# commands/homework.py
from aiogram import Router, types, F
from utils.helpers import format_file_size, get_file_emoji
from keyboards.homework import homework_menu_keyboard
from database.models import HomeworkDB


router = Router()
homework_db = HomeworkDB()


storage = None

@router.message(F.text == "Домашнее задания 📓")
async def homework_menu(message: types.Message):
    """Обработчик кнопки 'Домашние задания'"""
    await message.answer("Домашнее задания 📓:", reply_markup=homework_menu_keyboard)



@router.message(F.text == "Просмотреть записи 👀")
async def view_homework(message: types.Message):
    """Показывает ВСЕ задания от ВСЕХ модераторов (доступно всем)"""
    
    # Получаем ВСЕ задания (не только свои!)
    homework_list = homework_db.get_all_homework()

    if not homework_list:
        await message.answer("📝 Пока нет домашних заданий!")
        return

    response = "📚 Домашние задания:\n\n"
    for hw in homework_list:
        hw_id, hw_user_id, subject, task, deadline, created_at, creator_role = hw
        
        # Получаем количество файлов
        files = homework_db.get_homework_files(hw_id)
        file_count = len(files)
        
        response += f"🔹 {subject}\n"
        response += f"   📖 {task}\n"
        response += f"   📅 До: {deadline}\n"
        response += f"   📎 Файлов: {file_count}\n"
        response += f"   👤 Создал: {creator_role}\n"
        response += f"   👁️ /view_{hw_id}\n\n"

    await message.answer(response, reply_markup=homework_menu_keyboard)

@router.message(F.text.startswith("/delete_"))
async def delete_homework_button(message: types.Message):
    try:
        homework_id = int(message.text.replace("/delete_", ""))
        user_id = message.from_user.id
        
        # Проверяем, модератор ли пользователь
        if not homework_db.is_moderator(user_id):
            await message.answer("❌ Только модераторы могут удалять задания!")
            return
        
        deleted_files = homework_db.delete_homework(homework_id, user_id)
        
        if deleted_files >= 0:
            await message.answer(f"🗑️ Задание удалено! Удалено файлов: {deleted_files}")
        else:
            await message.answer("❌ Задание не найдено!")
            
    except ValueError:
        await message.answer("❌ Неверный формат команды!")

@router.message(F.text.startswith("/view_"))
async def view_specific_homework(message: types.Message):
    """Просмотр конкретного задания (доступно ВСЕМ)"""
    try:
        homework_id = int(message.text.replace("/view_", ""))
        
        # Важно: user_id=None = не проверяем владельца
        homework = homework_db.get_homework_by_id(homework_id, user_id=None)
        
        if not homework:
            await message.answer("❌ Задание не найдено!")
            return
        
        files = homework_db.get_homework_files(homework_id)
        hw_id, hw_user_id, subject, task, deadline, created_at = homework
        
        # Проверяем, кто создал (для информации)
        creator_role = "👑 Модератор" if homework_db.is_moderator(hw_user_id) else "👤 Пользователь"
        
        response = f"📚 {subject}\n\n"
        response += f"📖 {task}\n\n"
        response += f"📅 Дедлайн: {deadline}\n"
        response += f"📅 Создано: {created_at[:10]}\n"
        response += f"{creator_role}\n\n"
        
        if files:
            response += "📎 Прикрепленные файлы:\n"
            for i, file in enumerate(files, 1):
                file_id, _, storage_id, file_type, file_name, file_size, _ = file
                response += f"{i}. {get_file_emoji(file_type)} {file_name}\n"
                response += f"   💾 Размер: {format_file_size(file_size)}\n"
                response += f"   👁️ /file_{file_id}\n\n"
        else:
            response += "📎 Нет прикрепленных файлов"
        
        await message.answer(response, reply_markup=homework_menu_keyboard)
        
    except ValueError:
        await message.answer("❌ Неверный формат команды!")







