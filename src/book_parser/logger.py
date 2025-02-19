# src/book_parser/logger.py

import logging
from logging import Logger

def get_logger(name: str) -> Logger:
    """
    Создаёт и возвращает объект логирования для указанного имени.

    Args:
        name (str): Имя логгера, обычно имя модуля или класса, для которого ведется логирование.

    Returns:
        Logger: Объект логирования.
    """
    logger = logging.getLogger("book_parser")
    
    # Если обработчики ещё не добавлены, добавляем их
    if not logger.hasHandlers():
        handler = logging.StreamHandler()  # Вывод в консоль
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)  # Устанавливаем уровень логирования на INFO

    return logger
