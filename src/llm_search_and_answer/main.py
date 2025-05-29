# src/llm_search_and_answer/main.py

from fastapi import FastAPI
from src.llm_search_and_answer.routes import router as llm_router
from src.llm_search_and_answer.logger import get_logger
from src.config import settings

logger = get_logger(__name__)

app = FastAPI(title="LLM Search & Answer Service")

# Подключаем роутер
app.include_router(llm_router)

# Для локального запуска:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.llm_service_port, reload=True)
