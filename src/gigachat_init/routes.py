# src/gigachat_init/routes.py

from fastapi import APIRouter, HTTPException
from src.gigachat_init.client import GigaChatClient
from src.gigachat_init.models import TokenResponse, TokenInfoResponse, TokenRefreshResponse
from src.utils.logger import get_logger

logger = get_logger("gigachat_init")

router = APIRouter(prefix="/token", tags=["GigaChat Token"])

# Инициализируем клиента один раз для всех эндпоинтов
client = GigaChatClient()

@router.get("/", tags=["Health Check"])
def root():
    return {"message": "GigaChat Token Service is running"}

@router.get("/token", response_model=TokenResponse, tags=["Token"])
def get_token():
    try:
        logger.debug("Запрос токена")
        token = client.token
        token_data = client._token_data  # Предполагается, что _token_data содержит 'expires_at'
        return TokenResponse(access_token=token, expires_at=int(token_data['expires_at']))
    except Exception as e:
        logger.error(f"Ошибка получения токена: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/token/info", response_model=TokenInfoResponse, tags=["Token"])
def get_token_info():
    try:
        logger.debug("Запрос информации о токене")
        token_info = client.get_token_info()
        return TokenInfoResponse(**token_info)
    except Exception as e:
        logger.error(f"Ошибка получения информации о токене: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token/refresh", response_model=TokenRefreshResponse, tags=["Token"])
def refresh_token():
    try:
        logger.info("Принудительное обновление токена")
        # Принудительное обновление токена
        client._initialize()  # Обновление токена
        new_token = client.token
        return TokenRefreshResponse(message="Токен успешно обновлен", access_token=new_token)
    except Exception as e:
        logger.error(f"Ошибка обновления токена: {e}")
        raise HTTPException(status_code=500, detail=str(e))