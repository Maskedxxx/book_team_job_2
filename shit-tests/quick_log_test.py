# quick_log_test.py
"""
Быстрый тест системы логирования.
Демонстрирует логи разных уровней для всех сервисов.

Запуск: python quick_log_test.py
"""

import time
from src.utils.logger import get_logger

def test_logging_system():
    """
    Тестирует систему логирования для всех сервисов.
    """
    print("🔍 ТЕСТИРОВАНИЕ СИСТЕМЫ ЛОГИРОВАНИЯ")
    print("="*50)
    
    # Создаем логгеры для всех сервисов
    services = [
        "main",
        "book_parser", 
        "gigachat_init",
        "google_sheets",
        "llm_service"
    ]
    
    loggers = {}
    for service in services:
        loggers[service] = get_logger(service)
    
    print(f"\n✅ Созданы логгеры для {len(services)} сервисов")
    
    # Тестируем разные уровни логирования
    print(f"\n📝 Демонстрация разных уровней логирования:")
    
    for i, (service, logger) in enumerate(loggers.items(), 1):
        print(f"\n--- Сервис {i}/{len(services)}: {service} ---")
        
        # DEBUG уровень
        logger.debug(f"[DEBUG] Инициализация сервиса {service}")
        
        # INFO уровень  
        logger.info(f"[INFO] Сервис {service} запущен успешно")
        
        # WARNING уровень
        if service == "gigachat_init":
            logger.warning(f"[WARNING] Токен истекает через 10 минут")
        elif service == "book_parser":
            logger.warning(f"[WARNING] Большой файл книги: 15MB")
        elif service == "google_sheets":
            logger.warning(f"[WARNING] Очередь обработки: 5 форм")
        elif service == "llm_service":
            logger.warning(f"[WARNING] Высокая нагрузка на LLM сервис")
        else:
            logger.warning(f"[WARNING] Пример предупреждения для {service}")
        
        # ERROR уровень (только для демонстрации)
        if service == "llm_service":
            logger.error(f"[ERROR] Ошибка соединения с GigaChat API")
        
        # Небольшая пауза для читаемости
        time.sleep(0.5)
    
    print(f"\n🎯 Симуляция типичного workflow:")
    
    # Симулируем типичный поток обработки
    main_logger = loggers["main"]
    book_logger = loggers["book_parser"]
    gigachat_logger = loggers["gigachat_init"]
    sheets_logger = loggers["google_sheets"]
    llm_logger = loggers["llm_service"]
    
    main_logger.info("Получен запрос на обработку формы")
    
    sheets_logger.debug("Парсинг данных формы row_123")
    sheets_logger.info("Форма row_123 сохранена с 3 парами Q&A")
    
    gigachat_logger.debug("Проверка токена GigaChat")
    gigachat_logger.info("Токен действителен ещё 45 мин")
    
    llm_logger.info("Запуск LLM пайплайна")
    
    book_logger.debug("Загрузка JSON: know_map_full.json")
    book_logger.info("Получено 5 подглав")
    
    llm_logger.debug("Обработана подглава 3.11.1")
    llm_logger.debug("Обработана подглава 3.11.2") 
    llm_logger.info("LLM пайплайн завершен")
    
    sheets_logger.info("Форма row_123 полностью обработана (2/2)")
    
    main_logger.info("Запрос обработан успешно")
    
    print(f"\n🎉 Тестирование завершено!")
    print(f"📁 Логи сохранены в папку: logs/")
    print(f"🔧 Для изменения режима логирования отредактируйте .env:")
    print(f"   LOG_MODE=development (подробные логи)")
    print(f"   LOG_MODE=production (только важные)")

if __name__ == "__main__":
    test_logging_system()