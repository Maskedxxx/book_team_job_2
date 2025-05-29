# llm_diagnostic.py
import requests
import json
from src.config import settings as port_settings

def test_llm_service():
    """Тестирует LLM сервис пошагово"""
    
    base_url = f"http://127.0.0.1:{port_settings.llm_service_port}"
    
    print("=== ДИАГНОСТИКА LLM СЕРВИСА ===")
    print(f"Тестируем порт: {port_settings.llm_service_port}")
    print(f"База URL: {base_url}")
    print()
    
    # Тест 1: Проверка доступности сервиса
    print("1. Проверка доступности сервиса...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"   ✅ Сервис доступен - код {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Сервис недоступен: {e}")
        return
    
    # Тест 2: Проверка эндпоинта /llm/full-reasoning
    print("2. Проверка эндпоинта /llm/full-reasoning...")
    test_payload = {
        "question": "Тестовый вопрос для проверки работы сервиса"
    }
    
    try:
        response = requests.post(
            f"{base_url}/llm/full-reasoning",
            json=test_payload,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Код ответа: {response.status_code}")
        print(f"   Заголовки ответа: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Успешный ответ: {result}")
            except json.JSONDecodeError:
                print(f"   ⚠️ Ответ не в формате JSON: {response.text[:200]}")
        else:
            print(f"   ❌ Ошибка:")
            print(f"   Текст ошибки: {response.text}")
            
    except requests.exceptions.Timeout:
        print("   ❌ Таймаут запроса (60 секунд)")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка запроса: {e}")

def test_dependencies():
    """Проверяет зависимые сервисы"""
    print("\n=== ПРОВЕРКА ЗАВИСИМЫХ СЕРВИСОВ ===")
    
    # Проверка GigaChat Init
    print("1. Проверка GigaChat Init...")
    try:
        gigachat_url = f"http://127.0.0.1:{port_settings.gigachat_init_port}/token/token"
        response = requests.get(gigachat_url, timeout=10)
        if response.status_code == 200:
            token_data = response.json()
            print(f"   ✅ GigaChat токен получен: {token_data.get('access_token', '')[:20]}...")
        else:
            print(f"   ❌ Ошибка получения токена: {response.status_code}")
    except Exception as e:
        print(f"   ❌ GigaChat Init недоступен: {e}")
    
    # Проверка Book Parser
    print("2. Проверка Book Parser...")
    try:
        parser_url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/parts"
        response = requests.get(parser_url, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Book Parser работает")
        else:
            print(f"   ❌ Book Parser ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Book Parser недоступен: {e}")

def check_config():
    """Проверяет конфигурацию портов"""
    print("\n=== КОНФИГУРАЦИЯ ПОРТОВ ===")
    print(f"GigaChat Init: {port_settings.gigachat_init_port}")
    print(f"Book Parser: {port_settings.book_parser_port}")
    print(f"Google Sheets: {port_settings.google_sheets_port}")
    print(f"LLM Service: {port_settings.llm_service_port}")

def test_simple_request():
    """Простой тест запроса как делает Google Sheets сервис"""
    print("\n=== СИМУЛЯЦИЯ ЗАПРОСА ОТ GOOGLE SHEETS ===")
    
    # Имитируем тот же запрос, что делает Google Sheets сервис
    test_prompt = "вопрос: Тестовый вопрос\nОтвет: Тестовый ответ пользователя"
    
    try:
        response = requests.post(
            f"http://127.0.0.1:{port_settings.llm_service_port}/llm/full-reasoning",
            json={"question": test_prompt},
            timeout=60.0
        )
        
        print(f"Код ответа: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Ошибка: {response.text}")
        else:
            result = response.json()
            print(f"Успешный ответ: {result.get('answer', '')[:100]}...")
            
    except Exception as e:
        print(f"Ошибка при запросе: {e}")

if __name__ == "__main__":
    check_config()
    test_dependencies()
    test_llm_service()
    test_simple_request()