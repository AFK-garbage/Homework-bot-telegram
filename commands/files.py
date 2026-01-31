
import os
from datetime import datetime
from aiogram import Router, types, F
from aiogram.types import FSInputFile, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from aiogram import Bot, Router, types, F
from loader import bot, storage, async_session  
from database import crud  
from states.homework_states import HomeworkStates
from utils.helpers import format_file_size, get_file_emoji
from keyboards.homework import (
    homework_menu_keyboard,
    file_options_keyboard,
    file_one_keyboard,
    file_two_keyboard,
    file_three_keyboard,
)

router = Router()

# === ХЕНДЛЕРЫ КОМАНД ===

@router.message(F.text.startswith("/file_"))
async def view_specific_file(message: types.Message):
    """Просмотр файла по ID"""
    try:
        file_id = int(message.text.replace("/file_", ""))
        user_id = message.from_user.id
        
        
        async with async_session() as session:
            file_info = await crud.get_file_by_id(session, file_id)
            
            if not file_info:
                await message.answer("❌ Файл не найден в базе!")
                return
            
            
            homework = await crud.get_homework_by_id(session, file_info.homework_id)
            
            if not homework:
                await message.answer("❌ Задание не найдено!")
                return
            
            # Проверка доступа (владелец или модератор)
            is_mod = await crud.is_moderator(session, user_id)
            if homework.user_id != user_id and not is_mod:
                await message.answer("❌ Нет доступа к этому файлу!")
                return
        
        # Сессия закрыта, но file_info и homework уже загружены в память
        
        # Получаем файл из хранилища
        try:
            file_content, file_meta = await storage.get_file(file_info.storage_id)
            
            temp_path = f"./temp_{file_info.file_name}"
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            # Отправляем по типу
            file_input = FSInputFile(temp_path)
            caption = f"{get_file_emoji(file_info.file_type)} {file_info.file_name} ({format_file_size(file_info.file_size)})"
            
            if file_info.file_type == "photo":
                await message.answer_photo(file_input, caption=caption)
            elif file_info.file_type == "voice":
                await message.answer_voice(file_input, caption=caption)
            elif file_info.file_type == "video":
                await message.answer_video(file_input, caption=caption)
            else:
                await message.answer_document(file_input, caption=caption)
            
            os.remove(temp_path)
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при получении файла: {str(e)[:100]}")
            
    except ValueError:
        await message.answer("❌ Неверный формат команды!")

@router.message(F.text == "Добавить запись ✏️")
async def add_homework_start(message: Message, state: FSMContext):
    """Начало добавления ДЗ"""
    user_id = message.from_user.id
    
    
    async with async_session() as session:
        is_mod = await crud.is_moderator(session, user_id)
    
    if not is_mod:
        await message.answer("❌ У вас нет прав для добавления заданий.")
        return
    
    await state.update_data(temp_files=[])
    await message.answer("📝 Введи название предмета:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(HomeworkStates.waiting_for_subject)

# === СОСТОЯНИЯ ДЛЯ ДОБАВЛЕНИЯ ДЗ ===

@router.message(HomeworkStates.waiting_for_subject)
async def process_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer("📖 Теперь опиши задание:")
    await state.set_state(HomeworkStates.waiting_for_task)

@router.message(HomeworkStates.waiting_for_task)
async def process_task(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    await message.answer("📅 Укажи дедлайн (например: 25.12.2024 или 'завтра'):")
    await state.set_state(HomeworkStates.waiting_for_deadline)

@router.message(HomeworkStates.waiting_for_deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    """Получаем дедлайн и спрашиваем про файлы"""
    try:
        await state.update_data(deadline=message.text.strip())
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=file_one_keyboard,
            resize_keyboard=True
        )
        
        await message.answer(
            "📎 Хотите добавить файл к заданию?\n\n"
            "• Отправьте файл\n"
            "• Или нажмите '✅ Без файла'",
            reply_markup=keyboard
        )
        await state.set_state(HomeworkStates.waiting_for_files)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()

# === ОБРАБОТКА ФАЙЛОВ В СОСТОЯНИИ waiting_for_files ===

@router.message(HomeworkStates.waiting_for_files)
async def handle_files_state(message: Message, state: FSMContext):
    """Главный обработчик для состояния waiting_for_files"""
    user_data = await state.get_data()
    temp_files = user_data.get('temp_files', [])
    file_mode = user_data.get('file_mode', 'single')
    
    
    if message.text == "✅ Без файла":
        success = await save_homework_to_db(message, state, files_list=[])
        if success:
            await state.clear()
        return
    
    
    elif message.text == "📎 Добавить файл":
        keyboard = ReplyKeyboardMarkup(
            keyboard=file_options_keyboard,
            resize_keyboard=True
        )
        await message.answer("Выберите режим:", reply_markup=keyboard)
        return
    
    
    elif message.text == "📎 Один файл":
        await state.update_data(file_mode='single', temp_files=[])
        await message.answer("📎 Отправьте ОДИН файл", reply_markup=ReplyKeyboardRemove())
        return
    
    
    elif message.text == "📁 Несколько файлов":
        await state.update_data(file_mode='multiple', temp_files=[])
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=file_two_keyboard,
            resize_keyboard=True
        )
        
        await message.answer(
            "📁 Режим нескольких файлов:\n\n"
            "• Отправляйте файлы по одному\n"
            "• '✅ Завершить' - сохранить\n"
            "• '❌ Без файлов' - отмена",
            reply_markup=keyboard
        )
        return
    
    
    elif message.content_type in ('photo', 'document', 'voice', 'video', 'audio'):
        file_data = await download_file_simple(message, bot)
        
        if file_data:
            temp_files.append(file_data)
            await state.update_data(temp_files=temp_files)
            
            if file_mode == 'single':
                success = await save_homework_to_db(message, state, files_list=temp_files)
                if success:
                    await state.clear()
            else:
                keyboard = ReplyKeyboardMarkup(
                    keyboard=file_three_keyboard,
                    resize_keyboard=True
                )
                await message.answer(
                    f"✅ Файл добавлен! ({len(temp_files)} шт.)\n"
                    f"💾 {format_file_size(file_data['size'])}\n\n"
                    f"Что дальше?",
                    reply_markup=keyboard
                )
        else:
            await message.answer("❌ Ошибка при сохранении файла")
        
        return
    
    
    elif message.text == "✅ Завершить" and file_mode == 'multiple':
        success = await save_homework_to_db(message, state, files_list=temp_files)
        if success:
            await state.clear()
        return
    
    
    elif message.text == "❌ Без файлов":
        success = await save_homework_to_db(message, state, files_list=[])
        if success:
            await state.clear()
        return
    
    
    else:
        await message.answer("🤔 Отправьте файл или используйте кнопки")

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def save_homework_to_db(message: Message, state: FSMContext, files_list=None):
    """Сохраняет задание в базу данных"""
    try:
        if files_list is None:
            files_list = []
        
        user_data = await state.get_data()
        
        if 'subject' not in user_data or 'task' not in user_data or 'deadline' not in user_data:
            await message.answer("❌ Ошибка: данные задания повреждены")
            return False
        
        
        async with async_session() as session:
            homework_id = await crud.add_homework(
                session,
                user_id=message.from_user.id,
                subject=user_data['subject'],
                task=user_data['task'],
                deadline=user_data['deadline']
            )
            
            if files_list:
                await crud.add_files_to_homework(session, homework_id, files_list)
            
            
        
        response = (
            f"✅ ЗАДАНИЕ ДОБАВЛЕНО!\n\n"
            f"📚 Предмет: {user_data['subject']}\n"
            f"📖 Задание: {user_data['task']}\n"
            f"📅 Дедлайн: {user_data['deadline']}\n"
            f"🆔 ID задания: {homework_id}"
        )
        
        if files_list:
            response += f"\n📎 Файлов: {len(files_list)}"
            for i, file_data in enumerate(files_list, 1):
                size_str = format_file_size(file_data['size'])
                response += f"\n  {i}. {file_data['name']} ({size_str})"
        
        await message.answer(response, reply_markup=homework_menu_keyboard)
        print(f"✅ Пользователь {message.from_user.id} добавил задание #{homework_id}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения задания: {e}")
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")
        return False


async def download_file_simple(message: Message, bot: Bot):
    """Скачивает файл через HybridStorage"""
    try:
        
        if message.photo:
            file_obj = message.photo[-1]
            file_type = "photo"
            original_name = f"photo_{int(datetime.now().timestamp())}.jpg"
        elif message.document:
            file_obj = message.document
            file_type = "document"
            original_name = message.document.file_name or "document.bin"
        elif message.voice:
            file_obj = message.voice
            file_type = "voice"
            original_name = f"voice_{int(datetime.now().timestamp())}.ogg"
        elif message.video:
            file_obj = message.video
            file_type = "video"
            original_name = f"video_{int(datetime.now().timestamp())}.mp4"
        elif message.audio:
            file_obj = message.audio
            file_type = "audio"
            original_name = f"audio_{int(datetime.now().timestamp())}.mp3"
        else:
            await message.answer("❌ Неподдерживаемый тип файла")
            return None
        
        
        if file_obj.file_size > MAX_FILE_SIZE:
            await message.answer("❌ Файл слишком большой (макс 50MB)")
            return None
        
        
        if '.' in original_name:
            ext = os.path.splitext(original_name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                await message.answer(f"❌ Запрещенный тип файла {ext}")
                return None
        
        
        file_info = await bot.get_file(file_obj.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        file_content = downloaded.read()
        
       
        save_result = await storage.save_file(
            file_content=file_content,
            filename=original_name,
            metadata={
                'user_id': message.from_user.id,
                'file_type': file_type,
                'telegram_file_id': file_obj.file_id
            }
        )
        
        print(f"✅ Файл сохранен: {save_result['id']}")
        
        return {
            'storage_id': save_result['id'],
            'type': file_type,
            'name': original_name,
            'size': len(file_content)
        }
        
    except Exception as e:
        print(f"❌ Ошибка сохранения файла: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Ошибка при сохранении файла")
        return None