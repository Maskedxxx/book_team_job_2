# src/utils/logger.py

import logging
import os
import time
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from typing import Dict, Optional, Any
from contextlib import contextmanager
from functools import wraps

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
            level=os.getenv('LOG_LEVEL', 'INFO').upper(),
            mode=os.getenv('LOG_MODE', 'development').lower(),
            max_file_size_mb=int(os.getenv('LOG_MAX_FILE_SIZE_MB', '2')),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5'))
        )

# Кэш для созданных логгеров (избегаем дублирования)
_loggers_cache: Dict[str, logging.Logger] = {}


class PipelineLogger:
    """
    Логгер для пайплайнов обработки данных.
    Обеспечивает блочное логирование с измерением времени.
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = get_logger(service_name)
        self.config = LogConfig.from_env()
        self.current_pipeline_id: Optional[str] = None
        self.pipeline_start_time: Optional[float] = None
        self.current_stage: Optional[str] = None
        self.stage_start_time: Optional[float] = None
    
    @contextmanager
    def pipeline_context(self, pipeline_id: str):
        """
        Контекстный менеджер для полного пайплайна.
        
        Args:
            pipeline_id: Уникальный идентификатор пайплайна (например, row_id)
        """
        self.start_pipeline(pipeline_id)
        try:
            yield self
        except Exception as e:
            self.pipeline_error(str(e))
            raise
        finally:
            self.finish_pipeline()
    
    def start_pipeline(self, pipeline_id: str):
        """Начинает новый пайплайн."""
        self.current_pipeline_id = pipeline_id
        self.pipeline_start_time = time.time()
        
        if self.config.mode == 'development':
            separator = "=" * 60
            self.logger.info(f"{separator}")
            self.logger.info(f"НАЧАЛО ПАЙПЛАЙНА: {pipeline_id}")
            self.logger.info(f"{separator}")
        else:
            self.logger.info(f"ПАЙПЛАЙН {pipeline_id} ▶ СТАРТ")
    
    def finish_pipeline(self):
        """Завершает текущий пайплайн."""
        if self.pipeline_start_time and self.current_pipeline_id:
            duration = time.time() - self.pipeline_start_time
            
            if self.config.mode == 'development':
                separator = "=" * 60
                self.logger.info(f"{separator}")
                self.logger.info(f"ЗАВЕРШЕНИЕ ПАЙПЛАЙНА: {self.current_pipeline_id} ({duration:.1f}с)")
                self.logger.info(f"{separator}")
            else:
                self.logger.info(f"ПАЙПЛАЙН {self.current_pipeline_id} ✅ ЗАВЕРШЕН ({duration:.1f}с)")
        
        # Сброс состояния
        self.current_pipeline_id = None
        self.pipeline_start_time = None
    
    def pipeline_error(self, error_message: str):
        """Логирует ошибку пайплайна."""
        if self.current_pipeline_id:
            if self.config.mode == 'development':
                self.logger.error(f"ОШИБКА ПАЙПЛАЙНА {self.current_pipeline_id}: {error_message}")
            else:
                self.logger.error(f"ПАЙПЛАЙН {self.current_pipeline_id} ❌ ОШИБКА")
    
    def stage_start(self, stage_name: str, stage_number: int):
        """
        Начинает новый этап пайплайна.
        
        Args:
            stage_name: Название этапа
            stage_number: Номер этапа (1-5)
        """
        self.current_stage = stage_name
        self.stage_start_time = time.time()
        
        if self.config.mode == 'development':
            self.logger.info(f"ЭТАП {stage_number}: {stage_name} ▶ НАЧАЛО")
        # В production режиме логируем только при завершении этапа
    
    def stage_finish(self, stage_number: int, details: str = ""):
        """
        Завершает текущий этап.
        
        Args:
            stage_number: Номер этапа
            details: Дополнительные детали для development режима
        """
        duration = ""
        if self.stage_start_time:
            elapsed = time.time() - self.stage_start_time
            duration = f" ({elapsed:.1f}с)"
        
        if self.config.mode == 'development':
            detail_text = f": {details}" if details else ""
            self.logger.info(f"ЭТАП {stage_number}: {self.current_stage} ✅ ЗАВЕРШЕН{detail_text}{duration}")
        else:
            self.logger.info(f"ЭТАП {stage_number}: {self.current_stage} ✅")
        
        # Сброс состояния этапа
        self.current_stage = None
        self.stage_start_time = None
    
    def step(self, step_name: str, details: str = "", level: str = "info"):
        """
        Логирует отдельный шаг в рамках этапа.
        
        Args:
            step_name: Название шага
            details: Дополнительные детали
            level: Уровень логирования (info, debug, warning, error)
        """
        if self.config.mode == 'development':
            message = f"  └─ {step_name}"
            if details:
                message += f": {details}"
            
            log_method = getattr(self.logger, level.lower())
            log_method(message)
        # В production режиме шаги не логируются отдельно
    
    def service_check(self, service_name: str, port: int, status: bool, details: str = ""):
        """
        Логирует проверку доступности сервиса.
        
        Args:
            service_name: Название сервиса
            port: Порт сервиса
            status: True если доступен, False если нет
            details: Дополнительная информация
        """
        status_icon = "✅" if status else "❌"
        
        if self.config.mode == 'development':
            detail_text = f" - {details}" if details else ""
            self.logger.info(f"  └─ {service_name} (:{port}) {status_icon}{detail_text}")
        else:
            self.logger.info(f"    {service_name} {status_icon}")
    
    def qa_pair_processed(self, pair_number: int, total_pairs: int, question_preview: str = ""):
        """
        Логирует обработку пары вопрос-ответ.
        
        Args:
            pair_number: Номер текущей пары
            total_pairs: Общее количество пар
            question_preview: Превью вопроса для development режима
        """
        if self.config.mode == 'development':
            preview = f": {question_preview[:50]}..." if question_preview else ""
            self.logger.info(f"  └─ Обработка пары {pair_number}/{total_pairs}{preview}")
        # В production режиме отдельные пары не логируются


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


def get_pipeline_logger(service_name: str) -> PipelineLogger:
    """
    Создает и возвращает PipelineLogger для указанного сервиса.
    
    Args:
        service_name: Имя сервиса
        
    Returns:
        PipelineLogger для блочного логирования
    """
    return PipelineLogger(service_name)


# Декораторы для удобного использования
def log_stage(stage_name: str, stage_number: int):
    """
    Декоратор для автоматического логирования этапа.
    
    Args:
        stage_name: Название этапа
        stage_number: Номер этапа
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Пытаемся найти pipeline_logger в аргументах
            pipeline_logger = None
            for arg in args:
                if isinstance(arg, PipelineLogger):
                    pipeline_logger = arg
                    break
            
            if pipeline_logger:
                pipeline_logger.stage_start(stage_name, stage_number)
                try:
                    result = func(*args, **kwargs)
                    pipeline_logger.stage_finish(stage_number)
                    return result
                except Exception as e:
                    pipeline_logger.stage_finish(stage_number, f"ОШИБКА: {str(e)}")
                    raise
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


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