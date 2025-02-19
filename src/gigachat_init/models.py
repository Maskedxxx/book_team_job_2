# src/gigachat_init/models.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TokenResponse(BaseModel):
    """Модель для ответа, содержащего токен и время его истечения."""
    access_token: str
    expires_at: int  # время в формате Unix epoch (миллисекунды)

class TokenInfoResponse(BaseModel):
    """Модель для ответа с информацией о токене."""
    is_valid: bool
    expires_at: Optional[str]  # время истечения в виде строки (например, 'YYYY-MM-DD HH:MM:SS')

class TokenRefreshResponse(BaseModel):
    """Модель для ответа при принудительном обновлении токена."""
    message: str
    access_token: str
