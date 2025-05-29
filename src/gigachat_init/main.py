# src/gigachat_init/main.py

from fastapi import FastAPI
from src.gigachat_init.routes import router as gigachat_router
from src.config import settings


app = FastAPI(title="GigaChat Token Service")

# Подключаем роутер с эндпоинтами
app.include_router(gigachat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.gigachat_init_port, reload=True)
