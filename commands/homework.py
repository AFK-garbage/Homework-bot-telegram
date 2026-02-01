from aiogram import Router, types, F
from utils.helpers import format_file_size, get_file_emoji
from keyboards.homework import homework_menu_keyboard
from loader import async_session
from database import crud

router = Router()

@router.message(F.text == "Домашнее задания 📓")
async def homework_menu(message: types.Message):
    """Обработчик кнопки 'Домашние задания'"""
    await message.answer("Домашнее задания 📓:", reply_markup=homework_menu_keyboard)

@router.message(F.text == "Просмотреть записи 👀")
async def view_homework(message: types.Message):
    """Показывает ВСЕ задания от ВСЕХ модераторов (доступно всем)"""
    
    async with async_session() as session:
        homework_list = await crud.get_all_homework(session)

    if not homework_list:
        await message.answer("📝 Пока нет домашних заданий!")
        return

    response = "📚 Домашние задания:\n\n"
    for hw in homework_list:
        
        async with async_session() as session:
            files = await crud.get_homework_files(session, hw.id)
        file_count = len(files)
        
        
        async with async_session() as session:
            is_mod = await crud.is_moderator(session, hw.user_id)
        creator_role = "👑 Модератор" if is_mod else "👤 Пользователь"
        
        response += f"🔹 {hw.subject}\n"
        response += f"   📖 {hw.task}\n"
        response += f"   📅 До: {hw.deadline}\n"
        response += f"   📎 Файлов: {file_count}\n"
        response += f"   👤 Создал: {creator_role}\n"
        response += f"   👁️ /view_{hw.id}\n\n"

    await message.answer(response, reply_markup=homework_menu_keyboard)

@router.message(F.text.startswith("/delete_"))
async def delete_homework_button(message: types.Message):
    try:
        homework_id = int(message.text.replace("/delete_", ""))
        user_id = message.from_user.id
        
        
        async with async_session() as session:
            is_mod = await crud.is_moderator(session, user_id)
        
        if not is_mod:
            await message.answer("❌ Только модераторы могут удалять задания!")
            return
        
        async with async_session() as session:
            deleted_files = await crud.delete_homework(session, homework_id, user_id)
        
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
        
        async with async_session() as session:
            
            homework = await crud.get_homework_by_id(session, homework_id, user_id=None)
            
            if not homework:
                await message.answer("❌ Задание не найдено!")
                return
            
            files = await crud.get_homework_files(session, homework_id)
            
           
            is_mod = await crud.is_moderator(session, homework.user_id)
            creator_role = "👑 Модератор" if is_mod else "👤 Пользователь"
            
            response = f"📚 {homework.subject}\n\n"
            response += f"📖 {homework.task}\n\n"
            response += f"📅 Дедлайн: {homework.deadline}\n"
            created_str = homework.created_at[:10] if isinstance(homework.created_at, str) else homework.created_at.strftime('%Y-%m-%d')
            response += f"📅 Создано: {created_str}\n"
            response += f"{creator_role}\n\n"
            
            if files:
                response += "📎 Прикрепленные файлы:\n"
                for i, file in enumerate(files, 1):
                    response += f"{i}. {get_file_emoji(file.file_type)} {file.file_name}\n"
                    response += f"   💾 Размер: {format_file_size(file.file_size)}\n"
                    response += f"   👁️ /file_{file.id}\n\n"
            else:
                response += "📎 Нет прикрепленных файлов"
        
        await message.answer(response, reply_markup=homework_menu_keyboard)
        
    except ValueError:
        await message.answer("❌ Неверный формат команды!")





