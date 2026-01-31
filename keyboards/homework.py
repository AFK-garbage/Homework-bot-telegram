from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

homework_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Просмотреть записи 👀")],
        [KeyboardButton(text="Добавить запись ✏️"), KeyboardButton(text="↩️ Назад")]
    ],
    resize_keyboard=True
)


# Начало выбора файлов
file_one_keyboard = [
    [KeyboardButton(text="📎 Добавить файл")],
    [KeyboardButton(text="✅ Без файла")]
]

# Опции (один/несколько)
file_options_keyboard = [
    [KeyboardButton(text="📎 Один файл")],
    [KeyboardButton(text="📁 Несколько файлов")],
    [KeyboardButton(text="✅ Без файла")]
]

# Множественный режим
file_two_keyboard = [
    [KeyboardButton(text="✅ Завершить")],
    [KeyboardButton(text="❌ Без файлов")]
]

# После добавления файла (multiple)
file_three_keyboard = [
    [KeyboardButton(text="📎 Добавить еще файл")],
    [KeyboardButton(text="✅ Завершить")],
    [KeyboardButton(text="❌ Без файлов")]
]

# Ошибка в одиночном режиме
file_four_keyboard = [
    [KeyboardButton(text="❌ Пропустить файл")],
    [KeyboardButton(text="📎 Попробовать другой файл")]
]

# Ошибка в множественном режиме
file_five_keyboard = [
    [KeyboardButton(text="📎 Добавить другой файл")],
    [KeyboardButton(text="✅ Завершить")],
    [KeyboardButton(text="❌ Без файлов")]
]