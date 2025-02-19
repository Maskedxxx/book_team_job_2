from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # URL для получения токена GigaChat
    gigachat_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
    # Заголовок авторизации из переменных окружения
    auth_header: str
    
    # Скоуп для запроса токена
    token_scope: str = "GIGACHAT_API_PERS"
    
    # Флаг проверки SSL-сертификата
    verify_ssl: bool = False

    model_config = ConfigDict(
        env_file='.env',
        env_prefix='GIGACHAT_'  # Добавляем префикс для переменных
    )

# Экземпляр настроек, который можно импортировать в другие модули
settings = Settings()