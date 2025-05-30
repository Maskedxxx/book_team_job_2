# simulate_pipeline.py
"""
Скрипт для симуляции полного пайплайна обработки данных.
Демонстрирует все логи от получения данных формы до финального ответа LLM.

Запуск: python simulate_pipeline.py
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any

# Конфигурация портов (должны совпадать с вашими настройками)
PORTS = {
    "google_sheets": 8200,
    "book_parser": 8001, 
    "gigachat_init": 8010,
    "llm_service": 8110
}

BASE_URL = "http://127.0.0.1"

def print_step(step_number: int, description: str):
    """Красиво выводит номер шага."""
    print(f"\n{'='*60}")
    print(f"ШАГ {step_number}: {description}")
    print(f"{'='*60}")

def print_substep(description: str):
    """Выводит подшаг."""
    print(f"\n--- {description} ---")

async def simulate_google_sheets_data_receive():
    """
    Симулирует получение данных из Google Sheets.
    Отправляет POST запрос с тестовыми данными формы.
    """
    print_step(1, "ПОЛУЧЕНИЕ ДАННЫХ ИЗ GOOGLE SHEETS")
    
    # Тестовые данные формы (как будто пришли из Google Sheets)
    test_form_data = {
        "row_id": "test_row_123",
        "Отметка времени": "2025-05-29 11:50:00",
        "Рабочая почта для получения результатов": "test@example.com",
        "Вопрос 1: Что такое лидерство?": "Лидерство - это способность влиять на других",
        "Вопрос 2: Почему отслеживание работает - назовите 4 урока?": "Урок 1: не каждый реагирует на обучение. Урок 2: между пониманием и действием большая дистанция. Урок 3: люди не становятся лучше без отслеживания. Урок 4: отслеживание создает ответственность.",
        "Вопрос 3: Как мотивировать команду?": "Нужно понимать потребности каждого сотрудника",
        "Отправка ответов": "Отправлено"
    }
    
    print(f"📤 Отправляем данные формы (row_id: {test_form_data['row_id']})")
    print(f"   Количество вопросов: {len([k for k in test_form_data.keys() if k.startswith('Вопрос')])}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}:{PORTS['google_sheets']}/sheets/receive-data",
                json=test_form_data,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Данные успешно получены и сохранены")
            print(f"   Entry ID: {result.get('entry_id')}")
            print(f"   QA пар: {result.get('qa_pairs_count')}")
            
            return test_form_data["row_id"]
            
        except Exception as e:
            print(f"❌ Ошибка при отправке данных: {e}")
            return None

async def simulate_llm_processing_start(row_id: str):
    """
    Симулирует запуск LLM обработки формы.
    """
    print_step(2, "ЗАПУСК LLM ОБРАБОТКИ")
    
    print(f"🚀 Запускаем LLM обработку для формы {row_id}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}:{PORTS['google_sheets']}/sheets/process-form/{row_id}",
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ LLM обработка запущена")
            print(f"   Статус: {result.get('status')}")
            print(f"   Сообщение: {result.get('message')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при запуске LLM обработки: {e}")
            return False

async def check_processing_status(row_id: str, max_attempts: int = 10):
    """
    Проверяет статус обработки формы с интервалами.
    """
    print_step(3, "МОНИТОРИНГ ОБРАБОТКИ")
    
    async with httpx.AsyncClient() as client:
        for attempt in range(max_attempts):
            try:
                print(f"🔍 Проверка статуса (попытка {attempt + 1}/{max_attempts})")
                
                response = await client.get(
                    f"{BASE_URL}:{PORTS['google_sheets']}/sheets/check-processing/{row_id}",
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                processed = result.get('processed', False)
                print(f"   Статус: {'Завершено' if processed else 'В процессе'}")
                
                if processed:
                    print(f"✅ Обработка завершена!")
                    print(f"   Последнее обновление: {result.get('last_updated', 'неизвестно')}")
                    return True
                
                # Если не завершено, ждем перед следующей проверкой
                if attempt < max_attempts - 1:
                    print(f"⏳ Ожидание {3} секунд перед следующей проверкой...")
                    await asyncio.sleep(3)
                
            except Exception as e:
                print(f"❌ Ошибка при проверке статуса: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
    
    print(f"⚠️ Обработка не завершилась за {max_attempts} попыток")
    return False

async def get_final_results(row_id: str):
    """
    Получает финальные результаты обработки.
    """
    print_step(4, "ПОЛУЧЕНИЕ ФИНАЛЬНЫХ РЕЗУЛЬТАТОВ")
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"📋 Получаем финальные данные для формы {row_id}")
            
            response = await client.get(
                f"{BASE_URL}:{PORTS['google_sheets']}/sheets/form-data/{row_id}",
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                form_data = result.get('data', {})
                qa_pairs = form_data.get('qa_pairs', [])
                
                print(f"✅ Финальные результаты получены")
                print(f"   Форма ID: {form_data.get('row_id')}")
                print(f"   Email пользователя: {form_data.get('user_email')}")
                print(f"   Статус обработки: {'Завершена' if form_data.get('processed') else 'Не завершена'}")
                print(f"   Количество Q&A пар: {len(qa_pairs)}")
                
                # Показываем примеры обработанных пар
                print(f"\n📝 Примеры обработанных вопросов:")
                for i, pair in enumerate(qa_pairs[:2], 1):  # Показываем первые 2
                    question = pair.get('question', '')[:50] + '...' if len(pair.get('question', '')) > 50 else pair.get('question', '')
                    has_llm_response = bool(pair.get('llm_response'))
                    print(f"   {i}. {question}")
                    print(f"      LLM ответ: {'✅ Получен' if has_llm_response else '❌ Отсутствует'}")
                
                return True
            else:
                print(f"❌ Ошибка получения результатов: {result.get('message')}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при получении финальных результатов: {e}")
            return False

async def simulate_direct_llm_call():
    """
    Симулирует прямой вызов LLM сервиса для демонстрации логов.
    """
    print_step(5, "ПРЯМАЯ ДЕМОНСТРАЦИЯ LLM СЕРВИСА")
    
    test_question = {
        "question": "вопрос: Почему отслеживание работает - назовите 4 урока о которых говорит автор. Ответ: Урок первый: не каждый реагирует на процесс обучения. Урок 2: между пониманием и действием дистанция огромного размера. Урок 3: люди не становятся лучше без отслеживания. Урок 4: отслеживание создает ответственность."
    }
    
    print(f"🤖 Отправляем прямой запрос к LLM сервису")
    print(f"   Вопрос: {test_question['question'][:100]}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}:{PORTS['llm_service']}/llm/full-reasoning",
                json=test_question,
                timeout=120.0  # Увеличиваем таймаут для LLM
            )
            response.raise_for_status()
            result = response.json()
            
            answer = result.get('answer', '')
            print(f"✅ LLM ответ получен")
            print(f"   Длина ответа: {len(answer)} символов")
            
            # Показываем начало ответа
            if answer:
                lines = answer.split('\n')
                print(f"   Начало ответа: {lines[0] if lines else 'Пустой ответ'}")
                if len(lines) > 1:
                    print(f"   Вторая строка: {lines[1] if len(lines) > 1 else ''}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при вызове LLM сервиса: {e}")
            return False

async def check_services_health():
    """
    Проверяет доступность всех сервисов перед началом симуляции.
    """
    print_step(0, "ПРОВЕРКА ДОСТУПНОСТИ СЕРВИСОВ")
    
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        # Проверяем каждый сервис
        for service_name, port in PORTS.items():
            try:
                if service_name == "gigachat_init":
                    # Для gigachat_init проверяем специфичный эндпоинт
                    response = await client.get(f"{BASE_URL}:{port}/token/", timeout=10.0)
                elif service_name == "google_sheets":
                    # Для google_sheets проверяем через docs (FastAPI автоматически создает /docs)
                    response = await client.get(f"{BASE_URL}:{port}/docs", timeout=10.0) 
                else:
                    # Для остальных пробуем корневой путь
                    response = await client.get(f"{BASE_URL}:{port}/docs", timeout=10.0)
                
                if response.status_code < 500:
                    services_status[service_name] = "✅ Доступен"
                else:
                    services_status[service_name] = f"⚠️ Ошибка {response.status_code}"
                    
            except Exception as e:
                services_status[service_name] = f"❌ Недоступен ({str(e)[:30]}...)"
    
    # Выводим статус всех сервисов
    all_ok = True
    for service_name, status in services_status.items():
        print(f"   {service_name:20} (:{PORTS[service_name]}) - {status}")
        if not status.startswith("✅"):
            all_ok = False
    
    if not all_ok:
        print(f"\n⚠️ Некоторые сервисы недоступны. Убедитесь, что все сервисы запущены.")
        print(f"   Для запуска используйте: python main.py")
        return False
    
    print(f"\n✅ Все сервисы доступны! Начинаем симуляцию...")
    return True

async def main():
    """
    Основная функция симуляции полного пайплайна.
    """
    print("🚀 СИМУЛЯЦИЯ ПОЛНОГО ПАЙПЛАЙНА ОБРАБОТКИ ДАННЫХ")
    print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем доступность сервисов
    if not await check_services_health():
        return
    
    # Шаг 1: Симулируем получение данных из Google Sheets
    row_id = await simulate_google_sheets_data_receive()
    if not row_id:
        print("❌ Не удалось получить row_id. Завершаем симуляцию.")
        return
    
    # Небольшая пауза для наглядности
    await asyncio.sleep(1)
    
    # Шаг 2: Запускаем LLM обработку
    llm_started = await simulate_llm_processing_start(row_id)
    if not llm_started:
        print("❌ Не удалось запустить LLM обработку. Завершаем симуляцию.")
        return
    
    # Шаг 3: Мониторим процесс обработки
    processing_completed = await check_processing_status(row_id)
    
    # Шаг 4: Получаем финальные результаты
    if processing_completed:
        await get_final_results(row_id)
    
    # Шаг 5: Демонстрируем прямой вызов LLM
    await asyncio.sleep(2)
    await simulate_direct_llm_call()
    
    print(f"\n{'='*60}")
    print("🎉 СИМУЛЯЦИЯ ЗАВЕРШЕНА")
    print(f"⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Запускаем асинхронную симуляцию
    asyncio.run(main())