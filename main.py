# main.py
import subprocess
import sys
from src.config import settings

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
        for service, port in services:
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
        
        # Дожидаемся завершения всех процессов
        for proc in processes:
            proc.wait()
            
    except KeyboardInterrupt:
        # При Ctrl+C аккуратно завершим все запущенные процессы
        for proc in processes:
            proc.terminate()
        print("Сервисы остановлены пользователем.")

if __name__ == "__main__":
    run_services()
