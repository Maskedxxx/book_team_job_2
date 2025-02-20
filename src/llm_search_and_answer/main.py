# src/llm_search_and_answer/main.py

from fastapi import FastAPI
from src.llm_search_and_answer.routes import router as llm_router
from src.llm_search_and_answer.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="LLM Search & Answer Service")

# Подключаем роутер
app.include_router(llm_router)

# Для локального запуска:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100, reload=True)
