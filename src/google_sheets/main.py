# src/google_sheets/main.py

from fastapi import FastAPI
from src.google_sheets.routes import router as google_sheets_router
from src.config import settings

app = FastAPI(title="Google Sheets Service")

# Подключаем роутер
app.include_router(google_sheets_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.google_sheets_port, reload=True)