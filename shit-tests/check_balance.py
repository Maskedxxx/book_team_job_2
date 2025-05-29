# check_balance_official.py
import requests
import os
from dotenv import load_dotenv

def check_balance_via_api():
    """Проверяет баланс через официальный эндпоинт /balance"""
    
    # Получаем токен
    try:
        token_response = requests.get("http://127.0.0.1:8010/token/token")
        token = token_response.json()["access_token"]
        print(f"✅ Токен получен")
    except Exception as e:
        print(f"❌ Ошибка получения токена: {e}")
        return
    
    # Запрашиваем баланс
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n=== ПРОВЕРКА БАЛАНСА ТОКЕНОВ ===")
    
    try:
        response = requests.get(
            "https://gigachat.devices.sberbank.ru/api/v1/balance",
            headers=headers,
            verify=False
        )
        
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            balance_data = response.json()
            print("✅ Баланс токенов:")
            
            if 'balance' in balance_data:
                for model_balance in balance_data['balance']:
                    model = model_balance.get('model', 'Неизвестная модель')
                    remaining = model_balance.get('tokens_remaining', 'Неизвестно')
                    total = model_balance.get('tokens_total', 'Неизвестно')
                    print(f"   {model}: {remaining} из {total} токенов")
            else:
                print(f"   Ответ: {balance_data}")
                
        elif response.status_code == 403:
            print("⚠️  Ошибка 403: Метод доступен только для пакетных токенов")
            print("   Вы используете схему pay-as-you-go")
            print("   Проверить баланс можно в личном кабинете: https://developers.sber.ru/studio")
            
        elif response.status_code == 402:
            print("❌ Ошибка 402: Закончились токены")
            
        else:
            print(f"⚠️  Код {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

def check_balance_via_gigachat_lib():
    """Проверяет баланс через официальную библиотеку gigachat"""
    
    load_dotenv()
    auth_header = os.getenv("GIGACHAT_INIT_AUTH_HEADER")
    
    if not auth_header:
        print("❌ GIGACHAT_INIT_AUTH_HEADER не найден в .env")
        return
    
    print("\n=== ПРОВЕРКА ЧЕРЕЗ БИБЛИОТЕКУ GIGACHAT ===")
    
    try:
        from gigachat import GigaChat
        
        # Извлекаем ключ из Base64 заголовка
        if auth_header.startswith("Basic "):
            credentials = auth_header.replace("Basic ", "")
        else:
            credentials = auth_header
            
        giga = GigaChat(credentials=credentials, verify_ssl_certs=False)
        
        response = giga.get_balance()
        print("✅ Баланс через библиотеку:")
        print(f"   {response}")
        
    except ImportError:
        print("⚠️  Библиотека gigachat не установлена")
        print("   Установите: pip install gigachat")
        
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Permission Denied" in error_msg:
            print("⚠️  Метод доступен только для пакетных токенов")
            print("   Вы используете схему pay-as-you-go")
        else:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_balance_via_api()
    check_balance_via_gigachat_lib()