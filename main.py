# main.py
import subprocess
import sys

def run_services():
    """
    Запускает три Uvicorn-процесса для наших микросервисов.
    Каждое приложение работает в своём процессе.
    """
    services = [
        ("src.gigachat_init.main:app", 8000),
        ("src.book_parser.main:app", 8001),
        ("src.llm_search_and_answer.main:app", 8100),
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
                "--reload"
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
