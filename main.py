# main.py
import subprocess
import sys
from src.config import settings
from src.utils.logger import get_logger

# Используем основной логгер для координатора
logger = get_logger("main")

def run_services():
    """
    Запускает три Uvicorn-процесса для наших микросервисов.
    Каждое приложение работает в своём процессе.
    """
    services = [
        ("src.gigachat_init.main:app", settings.gigachat_init_port),
        ("src.book_parser.main:app", settings.book_parser_port),
        ("src.llm_search_and_answer.main:app", settings.llm_service_port),
        ("src.google_sheets.main:app", settings.google_sheets_port),
    ]
    processes = []
    
    try:
        logger.info("Запуск микросервисов")
        for service, port in services:
            service_name = service.split('.')[1]  # Извлекаем имя сервиса
            logger.debug(f"Запуск сервиса {service_name} на порту {port}")
            
            # Формируем команду запуска Uvicorn
            cmd = [
                sys.executable,   # Текущий Python-интерпретатор
                "-m", "uvicorn",  # Запускаем Uvicorn как модуль
                service,
                "--host", "0.0.0.0",
                f"--port={port}",
                # "--reload"
            ]
            proc = subprocess.Popen(cmd)
            processes.append(proc)
        
        logger.info(f"Запущено {len(processes)} сервисов")
        
        # Дожидаемся завершения всех процессов
        for proc in processes:
            proc.wait()
            
    except KeyboardInterrupt:
        # При Ctrl+C аккуратно завершим все запущенные процессы
        logger.info("Получен сигнал остановки (Ctrl+C)")
        for proc in processes:
            proc.terminate()
        logger.info("Все сервисы остановлены")

if __name__ == "__main__":
    run_services()