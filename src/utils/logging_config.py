# src/utils/logging_config.py

import logging
import os
from pathlib import Path
from datetime import datetime

def setup_service_logger(service_name: str) -> logging.Logger:
    """
    Настраивает логгер для конкретного сервиса.
    Логи пишутся как в консоль, так и в файл.
    
    Args:
        service_name: Имя сервиса (book_parser, gigachat_init, etc.)
    
    Returns:
        Настроенный логгер
    """
    
    # Создаем папку для логов
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Имя файла с датой
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{service_name}_{today}.log"
    
    # Создаем логгер
    logger = logging.getLogger(service_name)
    
    # Если обработчики уже добавлены, не добавляем повторно
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # Обработчик для файла
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    logger.info(f"Логгер для {service_name} настроен. Файл: {log_file}")
    
    return logger