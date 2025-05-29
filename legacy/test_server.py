# test_server.py

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from src.google_sheets.models import FormSubmission
from src.google_sheets.services import process_form_data, save_form_submission
import json
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_server")

# Создаем экземпляр FastAPI
app = FastAPI(title="Google Sheets Test API")

@app.post("/sheets/data")
async def receive_data(request: Request):
    """
    Тестовый эндпоинт для получения данных из Google Sheets.
    """
    try:
        # Получаем данные из запроса
        data = await request.json()
        logger.info(f"Получены данные: {json.dumps(data, ensure_ascii=False)[:100]}...")
        
        # Обрабатываем данные с помощью нашего сервиса
        form_submission = process_form_data(data)
        
        # Сохраняем данные в JSON
        entry_id = save_form_submission(form_submission)
        
        # Выводим информацию о результате
        logger.info(f"Создан и сохранён объект FormSubmission с ID: {entry_id}")
        logger.info(f"Количество пар вопрос-ответ: {len(form_submission.qa_pairs)}")
        
        # Возвращаем успешный ответ
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Данные успешно обработаны и сохранены",
                "entry_id": entry_id,
                "qa_pairs_count": len(form_submission.qa_pairs)
            }
        )
    
    except Exception as e:
        logger.error(f"Ошибка при обработке данных: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Ошибка при обработке данных: {str(e)}"
            }
        )

@app.get("/api/test")
async def test_api():
    """
    Простой тестовый эндпоинт для проверки работоспособности API.
    """
    logger.info("Обработка тестового запроса")
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "message": "API работает"}
    )

@app.get("/api/responses/{response_id}")
async def get_response(response_id: str):
    """
    Получает и возвращает данные по указанному ID.
    """
    logger.info(f"Обработка запроса данных: /api/responses/{response_id}")
    logger.info(f"Извлечен ID: {response_id}")
    
    try:
        # Загружаем данные
        filename = 'form_data.json'
        if not os.path.exists(filename):
            logger.error(f"Файл {filename} не найден")
            raise HTTPException(status_code=404, detail="Файл с данными не найден")
        
        logger.info(f"Открываем файл {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            file_content = json.load(f)
        
        # Проверяем, находятся ли данные под ключом 'data'
        if 'data' in file_content:
            all_responses = file_content['data']
        else:
            all_responses = file_content
        
        # Ищем запись с указанным ID
        if response_id in all_responses:
            logger.info(f"Запись {response_id} найдена")
            response_data = all_responses[response_id]
            
            # Проверяем, есть ли ответы LLM в qa_pairs
            if 'qa_pairs' in response_data:
                for qa_pair in response_data['qa_pairs']:
                    # Если нет поля llm_response, добавляем его
                    if 'llm_response' not in qa_pair:
                        qa_pair['llm_response'] = "Ожидает обработки"
            
            # Отправляем данные
            logger.info(f"Отправляем ответ (первые 100 символов): {json.dumps(response_data, ensure_ascii=False)[:100]}...")
            return response_data
        else:
            logger.info(f"Запись {response_id} не найдена")
            logger.info(f"Доступные ключи: {list(all_responses.keys())[:10]}...")
            raise HTTPException(
                status_code=404,
                detail=f"Запись с ID {response_id} не найдена"
            )
        
    except HTTPException:
        # Пробрасываем ошибки HTTPException дальше
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке GET-запроса: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )

@app.get("/")
async def root():
    return {"message": "Тестовый сервер для Google Sheets API работает"}

# Запуск сервера
if __name__ == "__main__":
    logger.info("Запуск тестового сервера на порту 8050")
    logger.info("Для публичного доступа используйте команду: ngrok http 8050")
    uvicorn.run(app, host="0.0.0.0", port=8050)