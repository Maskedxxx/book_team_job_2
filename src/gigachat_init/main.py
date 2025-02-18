# src/main.py

from src.gigachat_init.client import GigaChatClient
from fastapi import FastAPI
from src.gigachat_init.logger import get_logger

# Создаем FastAPI приложение
app = FastAPI()

# Создаем экземпляр клиента для работы с GigaChat API
client = GigaChatClient()

@app.get("/")
def root():
    return {"message": "GigaChat Token Service is running"}

@app.get("/token")
def get_token():
    """
    Получение актуального токена.
    """
    token = client.token
    return {"access_token": token}

@app.get("/token/info")
def get_token_info():
    """
    Получение информации о текущем токене.
    """
    token_info = client.get_token_info()
    return token_info

@app.post("/token/refresh")
def refresh_token():
    """
    Принудительное обновление токена.
    """
    # Запрашиваем новый токен
    client._token_data = client._initialize()  # Принудительное обновление
    new_token = client.token
    return {
        "message": "Токен успешно обновлен",
        "access_token": new_token
    }

# Запуск сервиса
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
