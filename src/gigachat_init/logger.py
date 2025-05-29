# src/gigachat_init/logger.py

import logging
from pathlib import Path
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """
    Создаёт и возвращает объект логирования для GigaChat сервиса.
    Логи сохраняются как в консоль, так и в файл.
    """
    
    # Создаем папку для логов
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Имя файла с датой
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"gigachat_init_{today}.log"
    
    logger = logging.getLogger("gigachat_init")
    
    # Проверяем, если логгер ещё не настроен
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        
        # Формат логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Обработчик для файла
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"GigaChat логгер настроен. Файл: {log_file}")

    return logger