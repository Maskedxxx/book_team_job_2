#!/usr/bin/env python3
# test_gigachat_token.py
"""
Простой скрипт для проверки токена GigaChat API
"""

import requests
import uuid
from datetime import datetime

def test_gigachat_auth(auth_key):
    """
    Тестирует авторизацию в GigaChat API
    
    Args:
        auth_key (str): Authorization ключ (начинается с "Basic ")
    """
    
    print("🔐 Тестируем токен GigaChat...")
    print(f"🔑 Используемый ключ: {auth_key[:20]}...")
    
    # URL для получения токена
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
    # Заголовки запроса
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),  # Уникальный ID запроса
        "Authorization": auth_key
    }
    
    # Данные запроса
    data = {
        "scope": "GIGACHAT_API_PERS"
    }
    
    try:
        print("📡 Отправляем запрос...")
        print(f"📍 URL: {url}")
        print(f"📋 Headers: {headers}")
        print(f"📦 Data: {data}")
        
        # Делаем запрос с отключенной проверкой SSL
        response = requests.post(
            url, 
            headers=headers, 
            data=data, 
            verify=False,  # Отключаем проверку SSL как в оригинальном коде
            timeout=10
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        print(f"📄 Заголовки ответа: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Успешный ответ
            token_data = response.json()
            print("✅ УСПЕХ! Токен получен:")
            print(f"🎫 Access Token: {token_data.get('access_token', 'N/A')[:50]}...")
            print(f"⏰ Expires At: {token_data.get('expires_at', 'N/A')}")
            
            # Проверяем время истечения
            if 'expires_at' in token_data:
                expires_timestamp = int(token_data['expires_at']) / 1000
                expires_date = datetime.fromtimestamp(expires_timestamp)
                print(f"📅 Истекает: {expires_date}")
                
                # Проверяем, не истёк ли уже
                if expires_date > datetime.now():
                    print("✅ Токен ещё действителен")
                else:
                    print("⚠️ Токен уже истёк!")
            
            return True
            
        else:
            # Ошибка
            print("❌ ОШИБКА!")
            print(f"💥 Код ошибки: {response.status_code}")
            print(f"📝 Текст ответа: {response.text}")
            
            if response.status_code == 401:
                print("🔑 Проблема с авторизацией - проверьте токен!")
            elif response.status_code == 403:
                print("🚫 Доступ запрещён - проверьте права токена!")
            elif response.status_code == 429:
                print("⏱️ Превышен лимит запросов - попробуйте позже!")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"🌐 Ошибка сети: {str(e)}")
        return False
    except Exception as e:
        print(f"💀 Неожиданная ошибка: {str(e)}")
        return False

def main():
    """Основная функция"""
    print("=" * 60)
    print("🤖 GigaChat Token Tester")
    print("=" * 60)
    
    # Вариант 1: Ввести токен вручную
    print("\n1. Введите ваш Authorization ключ:")
    print("   Пример: Basic abcdef1234567890...")
    auth_key = input("🔑 Ключ: ").strip()
    
    if not auth_key:
        print("❌ Ключ не введён!")
        return
    
    if not auth_key.startswith("Basic "):
        print("⚠️ Ключ должен начинаться с 'Basic '")
        auth_key = f"Basic {auth_key}"
    
    # Тестируем
    success = test_gigachat_auth(auth_key)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Токен работает! Можете использовать его в проекте.")
    else:
        print("😞 Токен не работает. Проверьте ключ.")
    print("=" * 60)

if __name__ == "__main__":
    main()