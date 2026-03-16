import os
from dotenv import load_dotenv
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendMessage
from aiogram.types import Message

from app.utils.states import FeedbackState

load_dotenv()
MODERATOR_ID = os.getenv('MODERATOR_ID')

router = Router()


@router.message(Command('feedback'))
async def process_feedback(message: Message, state: FSMContext, bot: Bot):
    await message.answer("Введите сообщение для обратной связи с модераторами.")
    await state.set_state(FeedbackState.waiting_for_feedback)


@router.message(FeedbackState.waiting_for_feedback)
async def process_feedback(message: Message, state: FSMContext, bot: Bot):
    feedback_text = message.text
    await bot(SendMessage(chat_id=MODERATOR_ID, text=f"Обратная связь от {message.from_user.username}:\n{feedback_text}"))
    await message.reply("Сообщение отправлено. Спасибо, мы рассмотрим его.")
    await state.clear()

