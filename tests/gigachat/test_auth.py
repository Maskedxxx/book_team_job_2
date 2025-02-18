import pytest

from datetime import datetime
from src.gigachat_init.auth import get_gigachat_token, is_token_valid, ensure_fresh_token

from src.gigachat_init.logger import get_logger

logger = get_logger(__name__) 

def test_get_gigachat_token():
    """
    Тестирование получения токена GigaChat.
    Проверяет успешный вызов API и структуру ответа.
    """
    try:
        # Получаем токен
        result = get_gigachat_token()
        
        # Логируем результат для отладки
        logger.info("Получен ответ от API:")
        logger.info(f"Тип данных ответа: {type(result)}")
        logger.info(f"Структура ответа: {result.keys()}")
        logger.info(f"Значение expires_at: {result['expires_at']}")
        
        # Проверяем структуру ответа
        assert isinstance(result, dict), "Ответ должен быть словарем"
        assert "access_token" in result, "В ответе должен быть access_token"
        assert "expires_at" in result, "В ответе должен быть expires_at"
        
        # Проверяем типы данных полей
        assert isinstance(result["access_token"], str), "access_token должен быть строкой"
        assert isinstance(result["expires_at"], (int, float)), "expires_at должен быть числом"
        
        logger.info("Все проверки успешно пройдены!")
        
    except Exception as e:
        logger.error(f"Произошла ошибка при тестировании: {str(e)}")
        raise

def test_token_validity():
    """
    Тестирование проверки срока действия токена.
    """
    try:
        # Получаем реальный токен для теста
        token_data = get_gigachat_token()
        
        # Проверяем валидность
        is_valid = is_token_valid(token_data)
        
        logger.info(f"Токен действителен: {is_valid}")
        logger.info(f"Время истечения: {datetime.fromtimestamp(token_data['expires_at']/1000)}")
        
        # Проверяем, что новый токен действителен
        assert is_valid, "Только что полученный токен должен быть действительным"
        
        # Тестируем с заведомо истёкшим токеном
        expired_token = {
            "access_token": "test",
            "expires_at": int(datetime.now().timestamp() * 1000) - 1800000  # 30 минут назад
        }
        assert not is_token_valid(expired_token), "Истёкший токен должен быть недействительным"
        
        logger.info("Все проверки валидности токена успешно пройдены!")
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании валидности токена: {str(e)}")
        raise
    
def test_ensure_fresh_token():
    """
    Тестирование автоматического обновления токена.
    Проверяет различные сценарии обновления токена.
    """
    try:
        # Тест 1: Получение нового токена при отсутствии текущего
        token_data = ensure_fresh_token()
        assert token_data is not None
        assert is_token_valid(token_data)
        logger.info("Тест 1 пройден: Успешно получен новый токен")

        # Тест 2: Использование действующего токена
        reused_token = ensure_fresh_token(token_data)
        assert reused_token == token_data
        logger.info("Тест 2 пройден: Успешно переиспользован действующий токен")

        # Тест 3: Обновление истёкшего токена
        expired_token = {
            "access_token": "test",
            "expires_at": int(datetime.now().timestamp() * 1000) - 1800000
        }
        new_token = ensure_fresh_token(expired_token)
        assert new_token != expired_token
        assert is_token_valid(new_token)
        logger.info("Тест 3 пройден: Успешно обновлён истёкший токен")

        logger.info("Все тесты обновления токена успешно пройдены!")

    except Exception as e:
        logger.error(f"Ошибка при тестировании обновления токена: {str(e)}")
        raise

if __name__ == "__main__":
    test_get_gigachat_token()
    test_token_validity()
    test_ensure_fresh_token()