from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from app.database.requests import update_user_field

router = Router()

LANGS = {
    "🇷🇺 Русский": "ru",
    "🇬🇧 English": "en",
    "🇺🇦 Українська": "uk",
    "🇮🇩 Indonesia": "id"
}


@router.message(F.text == "/language")
async def choose_language(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text) for text in LANGS.keys()]],
        resize_keyboard=True
    )
    await message.answer("Выберите язык:", reply_markup=keyboard)


@router.message(F.text.in_(LANGS.keys()))
async def save_language(message: Message):
    lang_code = LANGS[message.text]
    await update_user_field(message.from_user.id, "lang", lang_code)
    await message.answer(f"Язык установлен: {message.text}")