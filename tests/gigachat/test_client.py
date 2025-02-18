"""
Тесты для клиента GigaChat API.
"""

import pytest
from datetime import datetime
from src.gigachat_init.client import GigaChatClient

from src.gigachat_init.logger import get_logger

logger = get_logger(__name__) 

def test_client_initialization():
    """
    Тестирование инициализации клиента и работы с токеном.
    """
    try:
        # Создаем клиент
        client = GigaChatClient()
        
        # Проверяем, что токен получен
        assert client._token_data is not None
        
        # Получаем информацию о токене
        token_info = client.get_token_info()
        assert token_info['is_valid']
        
        # Проверяем получение токена через свойство
        token = client.token
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Проверяем время истечения
        expires_at = client.token_expires_at
        assert isinstance(expires_at, datetime)
        assert expires_at > datetime.now()
        
        logger("Тесты клиента успешно пройдены!")
        
    except Exception as e:
        logger(f"Ошибка при тестировании клиента: {e}")
        raise
    
if __name__ == "__main__":
    test_client_initialization()