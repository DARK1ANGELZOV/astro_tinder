from aiogram.fsm.state import State, StatesGroup

class AnketaStates(StatesGroup):
    name = State() # Ожидание имени
    age = State() # Ожидание возраста
    description = State() # Ожидание описания
    city = State() # Ожидание города
    instagram = State() # Ожидание Instagram
    gender = State() # Ожидание пола
    preference = State() # Ожидание предпочтений по полу для поиска
    age_range = State() # Ожидание диапазона возраста для поиска
    photo_video = State() # Ожидание фотографий
    video = State() # Ожидание видео

class ProfileStates(StatesGroup):
    edit_description = State()
    edit_photo = State()


class FeedbackState(StatesGroup):
    waiting_for_feedback = State()

