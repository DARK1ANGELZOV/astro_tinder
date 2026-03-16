from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from sqlalchemy import select, and_, or_, not_
from app.database.models import async_session, User, Like, Match
from app.database.requests import get_user_by_tg_id
from aiogram.types import InputMediaPhoto, InputMediaVideo
from app.utils.states import AnketaStates


router = Router()

class MatchState(StatesGroup):
    viewing = State()
    messaging = State()

# Кнопки под анкетой
def get_profile_keyboard(tg_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💤"),
                KeyboardButton(text="✉️"),
                KeyboardButton(text="👎"),
                KeyboardButton(text="❤️")
            ],
            [KeyboardButton(text="📷 Все фотографии")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

@router.callback_query(F.data == "next_profile")
async def handle_next_profile_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    disk_text = (
        "‼️ Обрати внимание, что в интернете люди могут представляться кем-то другим.\n\n"
        "Астро Тиндер не запрашивает и не требует личные или паспортные данные. Мы делаем всё возможное для создания безопасной среды, однако помни, что ответственность за общение лежит на тебе.\n\n"
        "Продолжая использование бота, ты соглашаешься следовать правилам общения и понимаешь возможные риски."
    )

    await call.message.answer(disk_text)
    await view_next_profile(call.message, state, user_id=call.from_user.id)

@router.message(F.text == "Следующая анкета")
async def handle_next_profile_message(message: types.Message, state: FSMContext):
    await view_next_profile(message, state, user_id=message.from_user.id)

async def view_next_profile(message: types.Message, state: FSMContext, user_id: int = None):
    tg_id = user_id or message.from_user.id

    async with async_session() as session:
        current_user = await get_user_by_tg_id(tg_id)
        if not current_user:
            await message.answer("😅 Вы ещё не зарегистрированы. Введите /start")
            return

        data = await state.get_data()
        viewed_ids = data.get("viewed_profiles", [])

        stmt = select(User).where(
            User.tg_id != tg_id,
            User.city == current_user.city,
            User.is_registered == True,
            User.age >= current_user.min_age,
            User.age <= current_user.max_age,
            User.photo1.is_not(None),
            or_(
                User.gender == current_user.seeking_gender,
                current_user.seeking_gender == 'N'
            ),
            User.tg_id.not_in(viewed_ids),
            ~User.tg_id.in_(
                select(Like.to_id).where(Like.from_id == tg_id)
            )
        ).limit(1)

        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")],
                [InlineKeyboardButton(text="👤 Моя анкета", callback_data="my_profile"), InlineKeyboardButton(text="✏️Изменить анкету", callback_data="edit_profile")]])

        if not profile:
            await message.answer("😥 Пока анкет нет, попробуйте позже", reply_markup=keyboard)
            return

        await state.update_data(current_profile=profile.tg_id)

        caption = f"<b>{profile.name}, {profile.age}, {profile.city}</b>\n"
        if profile.description:
            caption += f"{profile.description}"
        if profile.instagram:
            caption += f"\nInstagram: {profile.instagram}"
        caption += "\n\n💖 Сбалансированная совместимость."

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💤", callback_data="sleep"),
                InlineKeyboardButton(text="✉️", callback_data=f"message:{profile.tg_id}"),
                InlineKeyboardButton(text="👎", callback_data="dislike"),
                InlineKeyboardButton(text="❤️", callback_data=f"like:{profile.tg_id}")
            ],
            [
                InlineKeyboardButton(text="📷 Все фотографии", callback_data="show_all_media")
            ]
        ])

        await message.answer_photo(
            photo=profile.photo1,
            caption=caption,
            reply_markup=get_profile_keyboard(),
            parse_mode="HTML"
        )

        viewed_ids.append(profile.tg_id)
        await state.update_data(viewed_profiles=viewed_ids)

@router.callback_query(F.data == "show_all_media")
async def send_all_photos(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    profile_id = data.get("current_profile")

    if not profile_id:
        await call.answer("⚠️ Ошибка: профиль не найден.")
        return

    async with async_session() as session:
        profile = await session.scalar(select(User).where(User.tg_id == profile_id))
        if not profile:
            await call.answer("⚠️ Профиль недоступен.")
            return

    media = []
    if profile.photo2:
        media.append(InputMediaPhoto(media=profile.photo2))
    if profile.photo3:
        media.append(InputMediaPhoto(media=profile.photo3))
    if profile.video:
        media.append(InputMediaVideo(media=profile.video))

    if not media:
        await call.answer("📭 У пользователя нет дополнительных медиа.")
        return

    try:
        await call.message.answer_media_group(media)
        await call.answer()
    except Exception as e:
        await call.answer("❗️ Не удалось отправить медиа.")
        print(f"[MEDIA ERROR]: {e}")

@router.message(F.text == "❤️")
async def handle_like_button(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_profile_id = data.get("current_profile")
    if current_profile_id:
        callback = types.CallbackQuery(
            id="manual_like",
            from_user=message.from_user,
            chat_instance="",
            message=message,
            data=f"like:{current_profile_id}"
        )
        await like_handler(callback, state)

@router.message(F.text == "👎")
async def handle_dislike_button(message: types.Message, state: FSMContext):
    callback = types.CallbackQuery(
        id="manual_dislike",
        from_user=message.from_user,
        chat_instance="",
        message=message,
        data="dislike"
    )
    await dislike_handler(callback, state)

@router.message(F.text == "✉️")
async def handle_message_button(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_profile_id = data.get("current_profile")
    if current_profile_id:
        callback = types.CallbackQuery(
            id="manual_message",
            from_user=message.from_user,
            chat_instance="",
            message=message,
            data=f"message:{current_profile_id}"
        )
        await start_message(callback, state)

@router.message(F.text == "💤")
async def handle_sleep_button(message: types.Message, state: FSMContext):
    callback = types.CallbackQuery(
        id="manual_sleep",
        from_user=message.from_user,
        chat_instance="",
        message=message,
        data="sleep"
    )
    await sleep_handler(callback, state)

@router.message(F.text == "📷 Все фотографии")
async def handle_all_foto(message:types.Message, state:FSMContext):
    callback = types.CallbackQuery(
        id="manual_all_foto",
        from_user = message.from_user,
        chat_instance="",
        message=message,
        data=f"show_all_media"
    )
    await send_all_photos(callback, state)

@router.callback_query(F.data.startswith("like:"))
async def like_handler(call: types.CallbackQuery, state: FSMContext):
    from_id = call.from_user.id
    to_id = int(call.data.split(":")[1])

    async with async_session() as session:
        existing_like = await session.scalar(
            select(Like).where(Like.from_id == from_id, Like.to_id == to_id)
        )

        if existing_like:
            await call.answer("Вы уже лайкали этого пользователя!")
            await view_next_profile(call.message, state, user_id=from_id)
            return

        session.add(Like(from_id=from_id, to_id=to_id))
        await session.commit()

        mutual = await session.scalar(
            select(Like).where(Like.from_id == to_id, Like.to_id == from_id)
        )

        if mutual:
            existing_match = await session.scalar(
                select(Match).where(
                    or_(
                        and_(Match.user1 == from_id, Match.user2 == to_id),
                        and_(Match.user1 == to_id, Match.user2 == from_id)
                    )
                )
            )

            if not existing_match:
                session.add(Match(user1=from_id, user2=to_id))
                await session.commit()

            try:
                from_user_db = await session.scalar(select(User).where(User.tg_id == from_id))
                
                # ВОССТАНОВЛЕНО: Логика с username
                contact_url = f"t.me/{from_user_db.username}" if from_user_db and from_user_db.username else None
                
                if contact_url:
                    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="✉️ Написать", url=contact_url)],
                        [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")]
                    ])
                else:
                    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="✉️ Написать (через бота)", callback_data=f"message:{from_id}")],
                        [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")]
                    ])

                if from_user_db:
                    profile_text = (
                        f"<b>{from_user_db.name}, {from_user_db.age}, {from_user_db.city}</b>\n"
                        f"{from_user_db.description or ''}"
                    )
                    if from_user_db.instagram:
                        profile_text += f"\nInstagram: {from_user_db.instagram}"

                    media = []
                    if from_user_db.photo1:
                        media.append(types.InputMediaPhoto(media=from_user_db.photo1, caption=profile_text, parse_mode="HTML"))
                    if from_user_db.photo2:
                        media.append(types.InputMediaPhoto(media=from_user_db.photo2))
                    if from_user_db.photo3:
                        media.append(types.InputMediaPhoto(media=from_user_db.photo3))
                    if from_user_db.video:
                        media.append(types.InputMediaVideo(media=from_user_db.video))

                    if media:
                        await call.bot.send_media_group(to_id, media)
                        await call.bot.send_message(to_id, "💬 Хотите начать общение?", reply_markup=reply_markup)
                    else:
                        await call.bot.send_message(
                            to_id,
                            f"🎉 У вас взаимная симпатия!\n\n{profile_text}\n\n💬 Хотите начать общение?",
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                else:
                    await call.bot.send_message(
                        to_id,
                        f"🎉 У вас взаимная симпатия с пользователем {call.from_user.full_name}!",
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
            except Exception as e:
                print(f"❗ Ошибка при уведомлении второго пользователя ({to_id}): {e}")
                error_message_to_from_user = "❌ Не удалось уведомить пользователя о взаимной симпатии."
                if "bot was blocked by the user" in str(e).lower() or "chat not found" in str(e).lower():
                    error_message_to_from_user += " (Возможно, он заблокировал бота или удалил чат)."
                await call.message.answer(error_message_to_from_user)


            # Отправка анкеты первому пользователю (from_id)
            to_user_db = await session.scalar(select(User).where(User.tg_id == to_id))
            
            # ВОССТАНОВЛЕНО: Логика с username
            contact_url = f"t.me/{to_user_db.username}" if to_user_db and to_user_db.username else None

            if contact_url:
                reply_markup_to_from_user = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="✉️ Написать", url=contact_url)],
                    [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")]
                ])
            else:
                reply_markup_to_from_user = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="✉️ Написать (через бота)", callback_data=f"message:{to_id}")],
                    [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")]
                ])

            if to_user_db:
                profile_text = (
                    f"<b>{to_user_db.name}, {to_user_db.age}, {to_user_db.city}</b>\n"
                    f"{to_user_db.description or ''}"
                )
                if to_user_db.instagram:
                    profile_text += f"\nInstagram: {to_user_db.instagram}"

                media = []
                if to_user_db.photo1:
                    media.append(types.InputMediaPhoto(media=to_user_db.photo1, caption=profile_text, parse_mode="HTML"))
                if to_user_db.photo2:
                    media.append(types.InputMediaPhoto(media=to_user_db.photo2))
                if to_user_db.photo3:
                    media.append(types.InputMediaPhoto(media=to_user_db.photo3))
                if to_user_db.video:
                    media.append(types.InputMediaVideo(media=to_user_db.video))

                if media:
                    await call.message.answer_media_group(media)
                    await call.message.answer("💬 Хотите начать общение?", reply_markup=reply_markup_to_from_user)
                else:
                    await call.message.answer(
                        f"🎉 У вас взаимная симпатия!\n\n{profile_text}\n\n💬 Хотите начать общение?",
                        reply_markup=reply_markup_to_from_user,
                        parse_mode="HTML"
                    )
            else:
                await call.message.answer(
                    "🎉 Взаимная симпатия! Вы можете начать общение.",
                    reply_markup=reply_markup_to_from_user
                )

        else:
            from_user_db = await session.scalar(select(User).where(User.tg_id == from_id))

            if from_user_db:
                profile_text = (
                    f"💌 Вам поставили лайк!\n\n"
                    f"<b>{from_user_db.name}, {from_user_db.age}, {from_user_db.city}</b>\n"
                    f"{from_user_db.description or ''}"
                )
                if from_user_db.instagram:
                    profile_text += f"\nInstagram: {from_user_db.instagram}"

                media_to_send = []
                if from_user_db.photo1:
                    media_to_send.append(types.InputMediaPhoto(media=from_user_db.photo1, caption=profile_text, parse_mode="HTML"))
                if from_user_db.photo2:
                    media_to_send.append(types.InputMediaPhoto(media=from_user_db.photo2))
                if from_user_db.photo3:
                    media_to_send.append(types.InputMediaPhoto(media=from_user_db.photo3))
                if from_user_db.video:
                    media_to_send.append(types.InputMediaVideo(media=from_user_db.video))

                reply_markup_to_liked_user = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❤️ Взаимный лайк", callback_data=f"like:{from_id}")],
                    [InlineKeyboardButton(text="👎 Пропустить", callback_data="dislike")],
                    [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")]
                ])

                try:
                    if media_to_send:
                        await call.bot.send_media_group(to_id, media_to_send)
                        await call.bot.send_message(
                            to_id,
                            "Что думаете?",
                            reply_markup=reply_markup_to_liked_user,
                            parse_mode="HTML"
                        )
                    else:
                        await call.bot.send_message(
                            to_id,
                            profile_text + "\n\nЧто думаете?",
                            reply_markup=reply_markup_to_liked_user,
                            parse_mode="HTML"
                        )
                    await call.message.answer("❤️ Лайк отправлен. Ожидаем взаимность.")
                except Exception as e:
                    print(f"❗ Ошибка при уведомлении пользователя ({to_id}) о лайке: {e}")
                    error_message_to_from_user = "❌ Не удалось уведомить пользователя о вашем лайке."
                    if "bot was blocked by the user" in str(e).lower() or "chat not found" in str(e).lower():
                        error_message_to_from_user += " (Возможно, он заблокировал бота или удалил чат)."
                    await call.message.answer(error_message_to_from_user)
            else:
                await call.message.answer("❤️ Лайк отправлен. Ожидаем взаимность.")

        await call.answer()
        await view_next_profile(call.message, state, user_id=from_id)

@router.callback_query(F.data == "dislike")
async def dislike_handler(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await view_next_profile(call.message, state, user_id=call.from_user.id)

@router.callback_query(F.data.startswith("message:"))
async def start_message(call: types.CallbackQuery, state: FSMContext):
    to_id = int(call.data.split(":")[1])
    await state.update_data(message_to=to_id)
    await state.set_state(MatchState.messaging)
    await call.answer()
    await call.message.answer("✉️ Напишите сообщение, и мы передадим его.")

@router.message(MatchState.messaging)
async def handle_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    to_id = data.get("message_to")
    from_user = message.from_user

    if not to_id:
        await message.answer("❌ Ошибка: получатель не найден.")
        await state.clear()
        return

    await message.answer("📨 Сообщение отправлено!\nОжидайте ответ.")

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == from_user.id))

    if not user:
        await message.answer("❌ Не удалось получить ваш профиль.")
        await state.clear()
        return

    caption = (
        "💌 Кому-то понравилась твоя анкета!\n\n"
        f"<b>{user.name}, {user.age}, {user.city}</b>\n"
        f"{user.description or ''}\n"
    )

    if user.instagram:
        caption += f"Instagram: {user.instagram}\n"

    caption += f"\n💌 Сообщение: {message.text}"

    # get_profile_keyboard уже использует message:{tg_id}, что корректно.
    kb = get_profile_keyboard(from_user.id)

    try:
        if user.photo1:
            await message.bot.send_photo(
                to_id,
                photo=user.photo1,
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb
            )
        else:
            await message.bot.send_message(to_id, caption, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        await message.answer("❗️ Не удалось доставить сообщение. Возможно, пользователь заблокировал бота.")
        print(f"Ошибка при отправке первого сообщения: {e}")
        await state.clear()
        return

    media = []
    if user.photo2:
        media.append(InputMediaPhoto(media=user.photo2))
    if user.photo3:
        media.append(InputMediaPhoto(media=user.photo3))
    if user.video:
        media.append(InputMediaVideo(media=user.video))

    if media:
        try:
            await message.bot.send_media_group(to_id, media)
        except Exception as e:
            print(f"Ошибка при отправке дополнительного медиа: {e}")

    await state.clear()
    await view_next_profile(message, state, user_id=message.from_user.id)

@router.callback_query(F.data == "sleep")
async def sleep_handler(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Продолжить поиск", callback_data="next_profile")],
        [InlineKeyboardButton(text="👤 Моя анкета", callback_data="my_profile")]
    ])
    await call.answer()
    await call.message.answer("Подождем пока кто-то увидит твою анкету.", reply_markup=kb)

@router.callback_query(F.data == "next_profile")
async def resume_from_sleep(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await view_next_profile(call.message, state, user_id=call.from_user.id)

@router.callback_query(F.data == "my_profile")
async def show_my_profile(call: types.CallbackQuery):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == call.from_user.id))
        if not user:
            await call.answer()
            await call.message.answer("🙁 Вы еще не зарегистрировались.\nЧтобы зарегистрироваться, напишите /start")
            return

        caption = f"{user.name}, {user.age}, г.{user.city}\n"
        if user.description:
            caption += f"{user.description}\n"
        if user.instagram:
            caption += f"Instagram: {user.instagram}"

        media = []
        if user.photo1:
            media.append(InputMediaPhoto(media=user.photo1, caption=caption, parse_mode="HTML"))
        if user.photo2:
            media.append(InputMediaPhoto(media=user.photo2))
        if user.photo3:
            media.append(InputMediaPhoto(media=user.photo3))
        if user.video:
            media.append(InputMediaVideo(media=user.video))

        if media:
            await call.message.answer_media_group(media)
        else:
            await call.message.answer(caption, parse_mode="HTML")

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile"),
                 InlineKeyboardButton(text="🔄 Продолжить поиск", callback_data="next_profile")]
            ]
        )
        await call.answer()
        await call.message.answer("Что хотите сделать?", reply_markup=kb)

class EditProfileState(StatesGroup):
    waiting_for_description = State()
    full_update = State()
    confirm = State()

@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить описание", callback_data="edit_description"),
         InlineKeyboardButton(text="♻️ Обновить всю анкету", callback_data="full_update")],
        [InlineKeyboardButton(text="🔄 Продолжить поиск", callback_data="next_profile")]
    ])
    await call.answer()
    await call.message.answer("Что вы хотите изменить?", reply_markup=kb)

@router.callback_query(F.data == "edit_description")
async def edit_description_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(EditProfileState.waiting_for_description)
    await call.answer()
    await call.message.answer("✍️ Введите новое описание для вашей анкеты:")

@router.message(EditProfileState.waiting_for_description)
async def edit_description_save(message: types.Message, state: FSMContext):
    new_desc = message.text
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if user:
            user.description = new_desc
            await session.commit()
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👀 Смотреть анкеты", callback_data="next_profile")],
                [InlineKeyboardButton(text="👤 Моя анкета", callback_data="my_profile"), InlineKeyboardButton(text="✏️Изменить анкету", callback_data="edit_profile")]
            ])
            await message.answer("✅ Описание обновлено!", reply_markup=keyboard)
        else:
            await message.answer("❌ Вы не зарегистрированы. Введите /start")
    await state.clear()

@router.callback_query(F.data == "full_update")
async def full_update_start(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AnketaStates.age)
    await call.answer()
    await call.message.answer("♻️ Хорошо, давайте обновим вашу анкету полностью. Введите ваш возраст:")