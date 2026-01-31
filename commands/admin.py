
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import config
from loader import homework_db, CREATOR_PASSWORD
from states.admin_states import ModeratorStates

router = Router()

# --- Команды для создателя ---

@router.message(Command("get_my_password"))
async def get_password_command(message: types.Message):
    """Получить пароль создателя"""
    if message.from_user.id != config.CREATOR_ID:
        await message.answer("❌ Только для создателя")
        return
    
    await message.answer(
        f"🔑 Ваш пароль: `{CREATOR_PASSWORD}`\n\n"
        f"💡 Используйте `/login` для входа",
        parse_mode="Markdown"
    )

@router.message(Command("list_moderators"))
async def list_moderators_command(message: types.Message):
    """Показать всех модераторов"""
    if message.from_user.id != config.CREATOR_ID:
        await message.answer("❌ Эта команда только для создателя бота.")
        return

    moderators = homework_db.get_all_moderators()

    if not moderators:
        await message.answer("📋 Нет зарегистрированных модераторов.")
        return

    response = "📋 Список модераторов:\n\n"
    for mod in moderators:
        user_id, created_by, created_at, is_active = mod
        status = "✅ Активен" if is_active else "❌ Неактивен"
        response += f"👤 ID: {user_id}\n"
        response += f"📅 Создан: {created_at[:10]}\n"
        response += f"👑 Создатель: {created_by}\n"
        response += f"📊 Статус: {status}\n\n"

    await message.answer(response)

@router.message(Command("create_moderator"))
async def create_moderator_command(message: types.Message, state: FSMContext):
    """Начинаем создание нового модератора"""
    if message.from_user.id != config.CREATOR_ID:
        await message.answer("❌ Эта команда только для создателя бота.")
        return

    await message.answer(
        "👤 Введите ID пользователя для нового модератора:\n"
        "(ID можно получить через @userinfobot)",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ModeratorStates.waiting_for_new_moderator_id)

@router.message(ModeratorStates.waiting_for_new_moderator_id)
async def process_moderator_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID должен быть числом!")
        return
    
    new_user_id = int(message.text.strip())
    
    if new_user_id == config.CREATOR_ID:
        await message.answer("❌ Это ваш собственный ID!")
        return
    
    await state.update_data(new_user_id=new_user_id)
    await message.answer("🔑 Теперь введите пароль для этого модератора (минимум 4 символа):")
    await state.set_state(ModeratorStates.waiting_for_new_moderator_password)

@router.message(ModeratorStates.waiting_for_new_moderator_password)
async def process_moderator_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    
    if len(password) < 4:
        await message.answer("❌ Пароль слишком короткий! Минимум 4 символа.")
        return
    
    user_data = await state.get_data()
    new_user_id = user_data.get('new_user_id')
    
    success = homework_db.create_moderator(config.CREATOR_ID, new_user_id, password)
    
    if success:
        await message.answer(
            f"✅ Модератор создан!\n\n"
            f"• ID: {new_user_id}\n"
            f"• Пароль: `{password}`\n"
            f"• Команда для входа: `/login`",
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Не удалось создать модератора (уже существует?).")
    
    await state.clear()

# --- Команды для модераторов ---

@router.message(Command("login"))
async def login_command(message: types.Message, state: FSMContext):
    """Вход для модераторов"""
    await message.answer("🔐 Введите пароль модератора:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ModeratorStates.waiting_for_password)

@router.message(ModeratorStates.waiting_for_password)
async def process_moderator_login(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    password = message.text.strip()
    
    if homework_db.verify_moderator(user_id, password):
        await message.answer(
            "✅ Успешный вход! Теперь вы модератор.\n"
            "Можете добавлять и просматривать задания.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "❌ Неверный пароль или у вас нет прав модератора.\n"
            "Попробуйте снова: /login"
        )
    
    await state.clear()