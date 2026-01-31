from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ReplyKeyboardRemove

def main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для основного меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Домашнее задания 📓")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def remove_keyboard() -> ReplyKeyboardRemove:
    """Удаление клавиатуры (просто возвращаем None)"""
    return ReplyKeyboardRemove()