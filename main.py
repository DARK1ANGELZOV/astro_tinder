import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from app.database.models import async_main
from app.handlers import all_routers
from app.utils.logger import logger

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Ошибка: Токен бота не найден! Проверьте .env файл.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

for router in all_routers:
    dp.include_router(router)

async def main():
    await async_main()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("Бот запущен!")
        loop.run_until_complete(main())  # Безопасный запуск event loop
    except KeyboardInterrupt:
        logger.warning("Бот остановлен пользователем. Завершение работы...")
    finally:
        logger.info("Очистка ресурсов...")
