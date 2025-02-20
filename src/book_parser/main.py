# src/book_parser/main.py

from fastapi import FastAPI
from src.book_parser.routes import router as book_parser_router

app = FastAPI(title="Book Parser Service")

app.include_router(book_parser_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
