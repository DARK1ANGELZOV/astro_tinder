from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.utils.states import ProfileStates
from app.database.requests import get_user_field, get_user_by_tg_id, update_user_field
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove

router = Router()


@router.message(F.text == "Моя анкета")
async def show_my_profile(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    # Получаем все поля
    name = await get_user_field(tg_id, "name")
    age = await get_user_field(tg_id, "age")
    city = await get_user_field(tg_id, "city")
    desc = await get_user_field(tg_id, "description")
    instagram = await get_user_field(tg_id, "instagram")
    photo1 = await get_user_field(tg_id, "photo1")
    photo2 = await get_user_field(tg_id, "photo2")
    photo3 = await get_user_field(tg_id, "photo3")
    video = await get_user_field(tg_id, "video")

    photos = [p for p in [photo1, photo2, photo3] if p]

    # Текст анкеты
    profile_text = f"{name}, {age}, {city}\n{desc}"
    if instagram:
        profile_text += f"\nInstagram: {instagram}"

    # 🎥 Сначала видео, если есть
    if video:
        await message.answer_video(video=video, caption=profile_text, parse_mode='HTML')

    # 📸 Потом фото, если есть
    elif photos:
        from aiogram.types import InputMediaPhoto

        media = [InputMediaPhoto(media=p) for p in photos]
        media[0].caption = profile_text  # Только первое фото с подписью
        await message.answer_media_group(media)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")],
                [InlineKeyboardButton(text="👤 Моя анкета", callback_data="my_profile"), InlineKeyboardButton(text="✏️Изменить анкету", callback_data="edit_profile")]
            ])

    # 📄 Если нет медиа — просто текст
    if not video and not photos:
        await message.answer(profile_text, parse_mode='HTML', reply_markup=keyboard)


@router.message(F.text.lower() == "Редактирование описания")
async def edit_description(message: Message, state: FSMContext):
    await message.answer("Введите новое описание:")
    await state.set_state(ProfileStates.edit_description)


@router.message(ProfileStates.edit_description)
async def save_new_description(message: Message, state: FSMContext):
    await update_user_field(message.from_user.id, "description", message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")],
                [InlineKeyboardButton(text="👤 Моя анкета", callback_data="my_profile"), InlineKeyboardButton(text="✏️Изменить анкету", callback_data="edit_profile")]
            ])
    await message.answer("Описание обновлено.", reply_markup=keyboard)
    await state.clear()
