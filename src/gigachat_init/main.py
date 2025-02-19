from fastapi import FastAPI
from src.gigachat_init.logger import get_logger
from src.gigachat_init.routes import router as gigachat_router

app = FastAPI(title="GigaChat Token Service")
logger = get_logger(__name__)

# Подключаем роутер с эндпоинтами
app.include_router(gigachat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
