# test_chat.py
import requests
import json

def test_gigachat_request():
    """Тестирует запрос к chat/completions для выявления проблемы"""
    
    # Получаем токен
    try:
        token_response = requests.get("http://127.0.0.1:8010/token/token")
        token = token_response.json()["access_token"]
        print(f"✅ Токен получен: {token[:30]}...")
    except Exception as e:
        print(f"❌ Ошибка получения токена: {e}")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Тестируем разные модели
    models_to_test = ["GigaChat-Max", "GigaChat", "GigaChat-Pro"]
    
    for model in models_to_test:
        print(f"\n=== ТЕСТ МОДЕЛИ {model} ===")
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Привет! Это тест."}
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                headers=headers,
                json=payload,
                verify=False,
                timeout=30
            )
            
            print(f"Статус: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']['content']
                usage = result.get('usage', {})
                
                print(f"✅ Успех! Ответ: {message[:50]}...")
                print(f"Использовано токенов: {usage}")
                return  # Если хотя бы одна модель работает, выходим
                
            elif response.status_code == 402:
                print(f"❌ Ошибка 402 для {model}")
                try:
                    error_detail = response.json()
                    print(f"Детали: {error_detail}")
                except:
                    print(f"Ответ: {response.text}")
                    
            else:
                print(f"⚠️ Код {response.status_code}")
                print(f"Ответ: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Ошибка запроса для {model}: {e}")
    
    # Дополнительная проверка токена
    print(f"\n=== ПРОВЕРКА ТОКЕНА ===")
    print(f"Длина токена: {len(token)}")
    print(f"Начинается с: {token[:10]}")
    
    # Проверим, не истек ли токен
    try:
        token_info_response = requests.get("http://127.0.0.1:8010/token/token/info")
        if token_info_response.status_code == 200:
            info = token_info_response.json()
            print(f"Токен валиден: {info.get('is_valid')}")
            print(f"Истекает: {info.get('expires_at')}")
    except Exception as e:
        print(f"Не удалось проверить info токена: {e}")

if __name__ == "__main__":
    test_gigachat_request()