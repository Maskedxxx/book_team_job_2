# get_models.py
import requests
import os
from dotenv import load_dotenv

def get_models_via_api():
    """Получает список моделей через API"""
    
    # Получаем токен
    try:
        token_response = requests.get("http://127.0.0.1:8010/token/token")
        token = token_response.json()["access_token"]
        print(f"✅ Токен получен")
    except Exception as e:
        print(f"❌ Ошибка получения токена: {e}")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n=== СПИСОК МОДЕЛЕЙ ЧЕРЕЗ API ===")
    
    try:
        response = requests.get(
            "https://gigachat.devices.sberbank.ru/api/v1/models",
            headers=headers,
            verify=False
        )
        
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            models_data = response.json()
            
            print("✅ Доступные модели:")
            if 'data' in models_data:
                for i, model in enumerate(models_data['data'], 1):
                    model_id = model.get('id', 'Неизвестно')
                    model_object = model.get('object', 'Неизвестно') 
                    print(f"   {i}. {model_id} (тип: {model_object})")
            else:
                print(f"   Ответ: {models_data}")
                
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

def get_models_via_lib():
    """Получает список моделей через библиотеку gigachat"""
    
    load_dotenv()
    auth_header = os.getenv("GIGACHAT_INIT_AUTH_HEADER")
    
    if not auth_header:
        print("❌ GIGACHAT_INIT_AUTH_HEADER не найден в .env")
        return
    
    print("\n=== СПИСОК МОДЕЛЕЙ ЧЕРЕЗ БИБЛИОТЕКУ ===")
    
    try:
        from gigachat import GigaChat
        
        # Извлекаем ключ из Base64 заголовка
        if auth_header.startswith("Basic "):
            credentials = auth_header.replace("Basic ", "")
        else:
            credentials = auth_header
            
        giga = GigaChat(credentials=credentials, verify_ssl_certs=False)
        
        response = giga.get_models()
        print("✅ Модели через библиотеку:")
        
        if hasattr(response, 'data'):
            for i, model in enumerate(response.data, 1):
                print(f"   {i}. {model.id}")
        else:
            print(f"   {response}")
        
    except ImportError:
        print("⚠️  Библиотека gigachat не установлена")
        print("   Установите: pip install gigachat")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    get_models_via_api()
    get_models_via_lib()