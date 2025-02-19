# src/book_parser/main.py

from fastapi import FastAPI
from src.book_parser.routes import router

app = FastAPI(title="Book Parser Service")

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
