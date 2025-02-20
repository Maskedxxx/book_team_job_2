# src/gigachat_init/client.py

"""
Основной клиент для работы с GigaChat API.
Управляет аутентификацией и состоянием токена.
"""
from typing import Dict, Optional
from datetime import datetime
from src.gigachat_init.auth import get_gigachat_token, is_token_valid, ensure_fresh_token
from src.gigachat_init.logger import get_logger

logger = get_logger(__name__) 

class GigaChatClient:
    """
    Клиент для работы с GigaChat API.
    
    Управляет аутентификацией и поддерживает актуальное состояние токена.
    Предоставляет интерфейс для выполнения запросов к API.
    """
    
    def __init__(self):
        """
        Инициализация клиента.
        При создании экземпляра получаем первый токен.
        """
        self._token_data: Optional[Dict[str, str]] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """
        Инициализация клиента и получение первого токена.
        """
        try:
            logger.info("Инициализация клиента GigaChat")
            self._token_data = get_gigachat_token()
            logger.info("Клиент успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации клиента: {e}")
            raise
    
    @property
    def token(self) -> str:
        """
        Получение актуального токена.
        
        Returns:
            str: Текущий действующий токен
        """
        self._token_data = ensure_fresh_token(self._token_data)
        return self._token_data['access_token']
    
    @property
    def token_expires_at(self) -> datetime:
        """
        Получение времени истечения токена в удобном формате.
        
        Returns:
            datetime: Время истечения токена
        """
        if self._token_data:
            timestamp = int(self._token_data['expires_at']) / 1000
            return datetime.fromtimestamp(timestamp)
        return None
    
    def get_token_info(self) -> Dict[str, str]:
        """
        Получение информации о текущем токене.
        
        Returns:
            Dict[str, str]: Информация о токене
        """
        if self._token_data:
            expires_at = self.token_expires_at
            return {
                "is_valid": is_token_valid(self._token_data),
                "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S") if expires_at else None
            }
        return {"is_valid": False, "expires_at": None}