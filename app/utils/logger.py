from loguru import logger
import sys
import os

# Создаём папку logs/ при необходимости
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Удаляем все предыдущие хендлеры
logger.remove()

# Добавляем хендлер для консоли
logger.add(sys.stdout, level="INFO", colorize=True,
           format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

# Добавляем хендлер для файла с ротацией и архивированием
logger.add(
    os.path.join(LOG_DIR, "davinvcik.log"),
    rotation="5 MB",          # Ротация по 5 MB
    retention="30 days",      # Храним не более 10 дней
    compression="zip",        # Архивируем старые логи
    enqueue=True,             # потокобезопасность
    encoding="utf-8",
    level="INFO",
    backtrace=True, diagnose=True  # трассировка при ошибках
)
