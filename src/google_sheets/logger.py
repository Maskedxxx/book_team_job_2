# src/gigachat_init/logger.py

import logging

def get_logger(name: str) -> logging.Logger:
    """
    Создаёт и возвращает объект логирования для указанного имени.

    Аргументы:
        name: Имя логера, обычно имя модуля или класса, для которого логируем.

    Возвращает:
        logging.Logger: Объект логирования.
    """
    logger = logging.getLogger("google_sheets")
    
    # Проверяем, если логгер ещё не настроен
    if not logger.hasHandlers():
        handler = logging.StreamHandler()  # Потоковый вывод в консоль
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)  # Устанавливаем уровень логирования на INFO

    return logger
