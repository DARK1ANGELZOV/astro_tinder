from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from app.utils.states import AnketaStates
from app.utils.logger import logger
from app.database.requests import add_user, get_user_by_tg_id, update_user
import app.keyboards.default as kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    intro_text = (
        "Привет! Я — бот Астро Тиндер 🌟\n\n"
        "🔮 Помогаю находить людей по интересам, знакам зодиака и астрологической совместимости.\n"
        "✨ Просто заполни анкету — и начнем искать тех, с кем звезды на одной волне!\n\n"
        "💫 А ещё у нас есть отдельный бот, где ты можешь проверить астросовместимость с любым человеком. Интересно? Тогда поехали!"
    )
    astro_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Астро Совместимость", url="t.me/AstroTinderRu_bot")],
    ])
    await message.answer(intro_text, reply_markup=astro_keyboard)

    # Сначала получаем пользователя из БД
    user = await get_user_by_tg_id(message.from_user.id)

    # Если в Telegram есть username и он отличается от сохранённого — обновляем запись
    if user and message.from_user.username and user.username != message.from_user.username:
        await update_user(user.tg_id, {'username': message.from_user.username})
    if user:
        profile_text = f"{user.name}, {user.age}\n{user.city}\n{user.description}\n\nInstagram: {user.instagram or '—'}"
        
        action_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")],
            [InlineKeyboardButton(text="👤 Моя анкета", callback_data="my_profile"), InlineKeyboardButton(text="✏️Изменить анкету", callback_data="edit_profile")]
        ])
        
        if user.photo1:
            await message.answer_photo(user.photo1, caption=profile_text, reply_markup=action_keyboard)
        else:
            await message.answer(profile_text, reply_markup=action_keyboard)
    else:
        await message.answer("Ваш возраст?")
        await state.set_state(AnketaStates.age)


@router.message(AnketaStates.age)
async def process_age(message: Message, state: FSMContext):
    if message.text.isdigit() and int(message.text) >= 18:
        await state.update_data(age=message.text)
        await state.set_state(AnketaStates.gender)
        await message.answer("Ваш пол?", reply_markup=await kb.get_gender_keyboard('ru'))
    elif message.text.isdigit() and int(message.text) < 18:
        await message.answer("Использование нашего бота позволено только совершеннолетним.")
    else:
        await message.answer("Пожалуйста, введите число.")


@router.message(AnketaStates.gender)
async def process_gender(message: Message, state: FSMContext):
    if message.text in ["Я парень", "Я девушка"]:
        await state.update_data(gender='M' if message.text == "Я парень" else "W")
        await state.set_state(AnketaStates.preference)
        await message.answer("Кто тебе интересен?", reply_markup=await kb.get_preference_keyboard('ru'))
    else:
        await message.answer("Выберите из предложенных кнопок.")


@router.message(AnketaStates.preference)
async def process_preference(message: Message, state: FSMContext):
    pref_map = {"Девушки": "W", "Парни": "M", "Всё равно": "N"}
    if message.text in pref_map:
        await state.update_data(love=pref_map[message.text])
        await state.set_state(AnketaStates.age_range)
        await message.answer("Укажи диапазон возраста в формате 18/25 (от 18 до 25)", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Выберите один из вариантов.")


@router.message(AnketaStates.age_range)
async def process_age_range(message: Message, state: FSMContext):
    try:
        min_age, max_age = map(int, message.text.split("/"))
        await state.update_data(min_age=min_age, max_age=max_age)
        await state.set_state(AnketaStates.name)
        await message.answer("Регистрация почти завершена! Введи свое имя:")
    except:
        await message.answer("Неверный формат. Попробуй снова, например: 20/30")


@router.message(AnketaStates.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AnketaStates.city)
    await message.answer("Укажи город, где ты сейчас живешь:")


@router.message(AnketaStates.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(AnketaStates.instagram)
    await message.answer("Укажи свой Instagram (или напиши 'нет'):")


@router.message(AnketaStates.instagram)
async def process_instagram(message: Message, state: FSMContext):
    insta = None if message.text.lower() == 'нет' else message.text
    await state.update_data(instagram=insta)
    await state.set_state(AnketaStates.description)
    await message.answer("Теперь расскажи немного о себе:")


@router.message(AnketaStates.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AnketaStates.photo_video)
    # Инициализируем списки для медиа
    await state.update_data(photos=[], video=None)
    await message.answer("Отправь до 3 фото и 1 видео — (только фото или только видео). После добавления медиа нажми \"Показать анкету\".",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="👀 Показать анкету", callback_data="preview_anketa")]
                         ]))


@router.message(AnketaStates.photo_video, F.content_type.in_({"photo", "video"}))
async def process_media(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    video = data.get("video")
    preview_shown = data.get("preview_shown", False)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 Показать анкету", callback_data="preview_anketa")]
    ])

    # 📸 Фото
    if message.photo:
        if video:
            await message.answer("Вы уже добавили видео. Фото и видео вместе нельзя.")
            return
        if len(photos) >= 3:
            await message.answer("Можно добавить не более 3 фотографий.")
            return

        photo_id = message.photo[-1].file_id
        photos.append(photo_id)
        await state.update_data(photos=photos)
        await message.answer(f"Фото {len(photos)} сохранено! Всего фото: {len(photos)}/3")

    # 🎥 Видео
    elif message.video:
        if photos:
            await message.answer("Вы уже добавили фото. Фото и видео вместе нельзя.")
            return
        if video:
            await message.answer("Можно добавить только одно видео.")
            return

        await state.update_data(video=message.video.file_id)
        await message.answer("🎥 Видео сохранено!")

    # ✅ Показываем кнопку ОДИН РАЗ после любого медиа
    if not preview_shown:
        await message.answer("Хотите посмотреть, как выглядит ваша анкета?", reply_markup=keyboard)
        await state.update_data(preview_shown=True)


@router.callback_query(F.data == "preview_anketa")
async def preview_anketa(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    await _show_profile_preview(callback.message, data)


async def _show_profile_preview(message: Message, data: dict):
    # Берем данные из состояния, а не из вложенного объекта "user"
    name = data.get("name")
    age = data.get("age")
    city = data.get("city")
    description = data.get("description")
    instagram = data.get("instagram", "")

    photos = data.get("photos", [])
    video = data.get("video")

    text = f"{name}, {age}\n{city}\n{description}"
    if instagram:
        text += f"\nInstagram: {instagram}"

    if photos:
        media_group = [InputMediaPhoto(media=p) for p in photos]
        media_group[0].caption = text
        await message.answer_media_group(media_group)
    elif video:
        await message.answer_video(video=video, caption=text, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode='HTML')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Завершить регистрацию", callback_data="complete_registration")],
        [InlineKeyboardButton(text="✏️ Изменить данные", callback_data="edit_registration")]
    ])
    await message.answer("Вы можете сохранить анкету или вернуться и внести изменения:", reply_markup=keyboard)


@router.callback_query(F.data == "complete_registration")
async def on_complete_registration(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает завершение регистрации пользователя, сохраняя данные в БД.
    """
    await callback.answer() # Отвечаем на callback-запрос, чтобы убрать "часики" с кнопки
    
    tg_id = callback.from_user.id
    data = await state.get_data() # Получаем все данные из FSM-состояния

    photos = data.get("photos", []) # Получаем список ID фото
    
    # Формируем словарь с данными пользователя для сохранения в БД
    user_data = {
        "tg_id": tg_id,
        "name": data.get("name"),
        "age": int(data.get("age")) if data.get("age") else None,
        "description": data.get("description"),
        "city": data.get("city"),
        "instagram": data.get("instagram"),
        "gender": data.get("gender"),  
        "seeking_gender": data.get("love"), # Поле 'love' из FSM-состояния соответствует 'seeking_gender' в БД
        "min_age": int(data.get("min_age")) if data.get("min_age") else None,
        "max_age": int(data.get("max_age")) if data.get("max_age") else None,
        "is_registered": True, # Пользователь завершил регистрацию, поэтому True
        "lang_code": callback.from_user.language_code,
        "username": callback.from_user.username, # <--- ГЛАВНОЕ ИЗМЕНЕНИЕ: Сохраняем username
        
        # Раскладываем фото по отдельным полям (до 3 фото)
        "photo1": photos[0] if len(photos) > 0 else None,
        "photo2": photos[1] if len(photos) > 1 else None,
        "photo3": photos[2] if len(photos) > 2 else None,
        "video": data.get("video"), # ID видео
        
        # Поля, которые могут быть не заполнены в процессе регистрации, но есть в модели
        "longitude": None, 
        "latitude": None,
        "phone": None,
        "is_search": True, # По умолчанию пользователь активен для поиска
        "index_field": None # Если у вас есть это поле, оно может быть заполнено позже
    }
    user = await get_user_by_tg_id(tg_id)
    try:
        if not user:
            await add_user(tg_id, user_data)
            logger.info(f"Пользователь зарегистрирован: tg_id={tg_id}, username={user_data['username']}, данные сохранены в БД.")
        else:
            await add_user(tg_id, user_data, recreate=True)
            logger.info(f"Пользователь обновлён: tg_id={tg_id}, username={user_data['username']}, данные сохранены в БД.")

        # Клавиатура после успешной регистрации
        post_reg_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")],
            [InlineKeyboardButton(text="👤 Моя анкета", callback_data="my_profile"), 
             InlineKeyboardButton(text="✏️ Изменить анкету", callback_data="edit_profile")]
        ])

        await callback.message.answer("🎉 Регистрация завершена! Добро пожаловать!", reply_markup=post_reg_keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных пользователя {tg_id}: {e}")
        await callback.message.answer("❌ Произошла ошибка при сохранении вашей анкеты. Пожалуйста, попробуйте еще раз или свяжитесь с администратором.")
    
    finally:
        await state.clear() # Очищаем FSM-состояние независимо от исхода


@router.callback_query(F.data == "edit_registration")
async def on_edit_registration(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Хорошо, начнем заново!")
    await state.clear()
    await callback.message.answer("Ваш возраст?")
    await state.set_state(AnketaStates.age)