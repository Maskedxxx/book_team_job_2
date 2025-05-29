#!/usr/bin/env python3
# test_gigachat_scopes.py
"""
Тестирует разные scope для GigaChat API
"""

import requests
import uuid

def test_scope(auth_key, scope):
    """Тестирует конкретный scope"""
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": auth_key
    }
    
    data = {"scope": scope}
    
    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
        
        print(f"🔍 Scope: {scope}")
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ УСПЕХ! Token получен: {token_data.get('access_token', '')[:50]}...")
            return True
        else:
            print(f"❌ Ошибка: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Исключение: {str(e)}")
        return False

def main():
    # Твой токен (добавляем Basic если нет)
    auth_key = "Basic NGUyMGQ1MzMtYzAxYS00NDBhLWI0YjctNzc4MDIyNDQyNDAyOmE0YTVkMjIwLTI0ZDItNDUwMS1iZDc5LTExZmUzOGIxYWQ5Yw=="
    
    print("🧪 Тестируем разные scope для твоего токена...")
    print("=" * 60)
    
    # Список возможных scope
    scopes_to_test = [
        "GIGACHAT_API_PERS",      # Персональный (не работает)
        "GIGACHAT_API_CORP",      # Корпоративный
        "GIGACHAT_API_B2B",       # B2B
        "GIGACHAT_API",           # Базовый
        "GIGACHAT_LITE",          # Lite версия
        "",                       # Пустой scope
    ]
    
    working_scopes = []
    
    for scope in scopes_to_test:
        print(f"\n🧪 Тестируем scope: '{scope}'")
        if test_scope(auth_key, scope):
            working_scopes.append(scope)
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ:")
    if working_scopes:
        print(f"✅ Рабочие scope: {working_scopes}")
        print(f"\n🔧 Обновите .env файл:")
        print(f"GIGACHAT_INIT_TOKEN_SCOPE={working_scopes[0]}")
    else:
        print("❌ Ни один scope не работает")
    print("=" * 60)

if __name__ == "__main__":
    main()