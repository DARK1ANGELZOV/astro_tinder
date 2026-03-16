from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Следующая анкета')],
    [KeyboardButton(text='Моя анкета')],
    [KeyboardButton(text='Редактирование описания'), KeyboardButton(text='Обратная связь')]],
                            resize_keyboard=True)


async def get_gender_keyboard(lang):
    options = {
        "ru": ["Я девушка", "Я парень"],
        "uk": ["Я дівчина", "Я хлопець"],
        "en": ["I'm Female", "I'm Male"],
        "id": ["Aku gadis", "Aku lelaki"]
    }
    keyboard = ReplyKeyboardBuilder()
    for button in options[lang]:
        keyboard.add(KeyboardButton(text=button))
    return keyboard.as_markup(resize_keyboard=True)


async def get_preference_keyboard(lang):
    options = {
        "ru": ["Девушки", "Парни", "Всё равно"],
        "uk": ["Дівчата", "Хлопці", "Все одно"],
        "en": ["Women", "Men", "No matter"],
        "id": ["Gadis", "Lekaki", "Tak peduli"]
    }
    keyboard = ReplyKeyboardBuilder()
    for button in options[lang]:
        keyboard.add(KeyboardButton(text=button))
    return keyboard.as_markup(resize_keyboard=True)



async def get_location_keyboard(lang, include_current=False):  #???
    options = {
        "ru": ["Поделиться местоположением", "Оставить текущее"],
        "uk": ["Поділитися місцем розташування", "Лишити так, як є"],
        "en": ["Share Location", "Leave current"],
        "id": ["Berbagi Lokasi", "Simpan semasa"]
    }
    buttons = [KeyboardButton(options[lang][0], request_location=True)]
    if include_current:
        buttons.append(KeyboardButton(options[lang][1]))
    return ReplyKeyboardMarkup(keyboard=[buttons],
                               resize_keyboard=True).as_markup()


async def get_address_confirm_keyboard(lang):
    options = {
        "ru": ["Продолжить", "Изменить адрес"],
        "uk": ["Продовжити", "змінити адресу"],
        "en": ["Continue", "Change Address"],
        "id": ["Lanjutkan", "Ubah Alamat"]
    }
    keyboard = ReplyKeyboardBuilder()
    for button in options[lang]:
        keyboard.add(KeyboardButton(text=button))
    return keyboard.as_markup(resize_keyboard=True)


async def get_address_confirm_keyboard(lang):
    options = {
        "ru": ["Продолжить", "Изменить адрес"],
        "uk": ["Продовжити", "змінити адресу"],
        "en": ["Continue", "Change Address"],
        "id": ["Lanjutkan", "Ubah Alamat"]
    }
    keyboard = ReplyKeyboardBuilder()
    for button in options[lang]:
        keyboard.add(KeyboardButton(text=button))
    return keyboard.as_markup(resize_keyboard=True)


