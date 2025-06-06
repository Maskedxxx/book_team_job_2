# src/gigachat_init/auth.py

import requests
import uuid
from datetime import datetime
from typing import Dict, Union, Tuple, Optional
from src.utils.logger import get_logger
from src.gigachat_init.config import settings

logger = get_logger("gigachat_init") 


def get_gigachat_token() -> Dict[str, str]:
    """
    Получает токен авторизации для GigaChat API.
    
    Returns:
        dict: Словарь с токеном и временем истечения
            Пример: {"access_token": "...", "expires_at": 1739803001958}
    
    Raises:
        requests.RequestException: При ошибке выполнения запроса
    """
    logger.debug("Запрос токена GigaChat")
    url = settings.auth_url
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),  # Генерируем уникальный ID для каждого запроса
        "Authorization": settings.auth_header
    }
    
    data = {
        "scope": settings.token_scope
    }
    
    response = requests.post(url, headers=headers, data=data, verify=settings.verify_ssl)
    response.raise_for_status()  # Проверяем на ошибки HTTP
    
    logger.info("Токен GigaChat получен успешно")
    return response.json()  # Автоматически преобразует JSON в словарь Python

def is_token_valid(token_data: Dict[str, str]) -> bool:
    """
    Проверяет, действителен ли токен GigaChat.
    
    Args:
        token_data: Словарь с данными токена, содержащий ключ 'expires_at'
        
    Returns:
        bool: True если токен действителен, False если истёк
        
    Raises:
        KeyError: Если в token_data отсутствует ключ 'expires_at'
    """
    try:
        # Получаем текущее время в миллисекундах
        current_time = int(datetime.now().timestamp() * 1000)
        
        # Получаем время истечения токена
        expires_at = int(token_data['expires_at'])
        
        # Сравниваем текущее время с временем истечения
        return current_time < expires_at
        
    except KeyError:
        raise KeyError("В данных токена отсутствует поле 'expires_at'")
    
    
def ensure_fresh_token(current_token: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Проверяет токен и при необходимости получает новый.
    
    Функция реализует следующую логику:
    1. Если токена нет - получает новый
    2. Если токен есть - проверяет срок действия
    3. Если токен истёк - получает новый
    4. Если токен действителен - возвращает текущий
    
    Args:
        current_token: Текущий токен и его данные (если есть)
        
    Returns:
        Dict[str, str]: Актуальный токен и время его истечения
        
    Raises:
        requests.RequestException: При ошибке получения нового токена
    """
    try:
        # Проверяем, есть ли у нас токен
        if current_token is None:
            logger.debug("Токен отсутствует, получаем новый")
            return get_gigachat_token()
        
        # Проверяем валидность существующего токена
        # Добавляем запас в 1 минуту для избежания граничных случаев
        if is_token_valid(current_token):
            current_time = int(datetime.now().timestamp() * 1000)
            expires_at = int(current_token['expires_at'])
            minutes_left = (expires_at - current_time) / (1000 * 60)
            
            if minutes_left > 1:  # Если осталось больше минуты
                logger.debug(f"Токен действителен ещё {int(minutes_left)} мин")
                return current_token
        
        # Если токен истёк или близок к истечению, получаем новый
        logger.debug("Обновляем токен")
        return get_gigachat_token()
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении токена: {str(e)}")
        raise