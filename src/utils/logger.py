# src/utils/logger.py

import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from typing import Dict

@dataclass
class LogConfig:
    """Конфигурация логирования из переменных окружения."""
    level: str
    mode: str  # development | production
    max_file_size_mb: int
    backup_count: int
    
    @classmethod
    def from_env(cls) -> 'LogConfig':
        """Загружает конфигурацию из переменных окружения."""
        return cls(
            level=os.getenv('LOG_LEVEL').upper(),
            mode=os.getenv('LOG_MODE').lower(),
            max_file_size_mb=int(os.getenv('LOG_MAX_FILE_SIZE_MB')),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT'))
        )

# Кэш для созданных логгеров (избегаем дублирования)
_loggers_cache: Dict[str, logging.Logger] = {}

def get_logger(service_name: str) -> logging.Logger:
    """
    Создает и возвращает логгер для указанного сервиса.
    
    Args:
        service_name: Имя сервиса (book_parser, gigachat_init, etc.)
    
    Returns:
        Настроенный логгер с ротацией файлов
    """
    # Если логгер уже создан, возвращаем его БЕЗ дополнительных сообщений
    if service_name in _loggers_cache:
        return _loggers_cache[service_name]
    
    # Загружаем конфигурацию
    config = LogConfig.from_env()
    
    # Создаем папку для логов
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Создаем логгер
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, config.level))
    
    # Избегаем дублирования обработчиков
    if logger.hasHandlers():
        # Если обработчики уже есть, просто кэшируем и возвращаем
        _loggers_cache[service_name] = logger
        return logger
    
    # Определяем формат в зависимости от режима
    if config.mode == 'development':
        # Подробный формат для разработки
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_level = logging.DEBUG
    else:
        # Краткий формат для продакшена
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_level = logging.WARNING
    
    # Обработчик для консоли (настраиваем уровень в зависимости от режима)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)
    
    # Обработчик для файла с ротацией
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{service_name}_{today}.log"
    
    # Ротация по размеру файла
    max_bytes = config.max_file_size_mb * 1024 * 1024  # Конвертируем MB в байты
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, config.level))
    logger.addHandler(file_handler)
    
    # Кэшируем логгер
    _loggers_cache[service_name] = logger
    
    # Лаконичное сообщение о настройке (только в development и только при первом создании)
    if config.mode == 'development':
        logger.debug(f"Logger initialized (mode: {config.mode}, level: {config.level})")
    
    return logger


def set_debug_mode():
    """Быстрое переключение в режим отладки для всех логгеров."""
    for logger in _loggers_cache.values():
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(logging.DEBUG)


def set_production_mode():
    """Быстрое переключение в производственный режим для всех логгеров."""
    for logger in _loggers_cache.values():
        logger.setLevel(logging.WARNING)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(logging.WARNING)