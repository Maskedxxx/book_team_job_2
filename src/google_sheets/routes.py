# src/google_sheets/routes.py

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import json
from src.google_sheets.services import process_form_data, save_form_submission
from src.google_sheets.services import get_form_submission_by_row_id
from src.google_sheets.services import process_form_submission_with_llm
from src.google_sheets.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/sheets", tags=["google_sheets"])

@router.post("/receive-data")
async def receive_data(request: Request):
    """
    Эндпоинт для получения данных из Google Sheets и сохранения их в JSON.
    
    Принимает JSON с данными из формы Google Sheets и обрабатывает их.
    Возвращает результат операции с дополнительными метаданными.
    """
    try:
        # Получаем данные из запроса
        data = await request.json()
        row_id = data.get('row_id', 'неизвестно')
        logger.info(f"Получены данные из строки {row_id}")
        
        # Обрабатываем данные с помощью сервиса
        form_submission = process_form_data(data)
        
        # Сохраняем данные в JSON
        entry_id = save_form_submission(form_submission)
        
        # Формируем ответ
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Данные из строки {row_id} успешно обработаны и сохранены",
                "entry_id": entry_id,
                "qa_pairs_count": len(form_submission.qa_pairs)
            }
        )
    
    except json.JSONDecodeError as e:
        error_msg = "Ошибка формата данных: неверный JSON"
        logger.error(f"{error_msg}. Детали: {str(e)}")
        return JSONResponse(
            status_code=400, 
            content={"status": "error", "message": error_msg}
        )
    
    except KeyError as e:
        error_msg = f"Отсутствует обязательное поле: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": error_msg}
        )
    
    except Exception as e:
        error_msg = f"Ошибка при обработке данных: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": error_msg}
        )


@router.get("/process-form/{row_id}")
async def process_form_with_llm(row_id: str):
    """
    Эндпоинт для обработки формы с помощью LLM сервиса по ID строки.
    
    Находит форму по указанному ID строки, запускает асинхронную обработку 
    с помощью LLM и возвращает статус запуска обработки.
    
    Args:
        row_id (str): Идентификатор строки из Google Sheets
    
    Returns:
        JSONResponse: Статус запуска обработки
    
    Raises:
        404: Если форма не найдена
        500: При ошибках запуска обработки
    """
    logger.info(f"Запрошена обработка формы для строки: {row_id}")
    
    try:
        # Проверяем существование формы
        form_data = get_form_submission_by_row_id(row_id)
        
        if form_data is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Форма для строки {row_id} не найдена"
                }
            )
        
        # Проверяем, не обработана ли форма уже
        if form_data.get("processed", False):
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Форма уже обработана",
                    "processed": True,
                    "form_id": row_id
                }
            )
        
        # Запускаем обработку формы в фоновом режиме
        # Используем create_task вместо await для асинхронной обработки
        from asyncio import create_task
        create_task(process_form_submission_with_llm(row_id))
        
        # Возвращаем статус запуска
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Обработка формы запущена",
                "processed": False,
                "form_id": row_id
            }
        )
    
    except FileNotFoundError as e:
        error_msg = f"Форма для строки {row_id} не найдена"
        logger.error(f"{error_msg}: {str(e)}")
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": error_msg,
                "form_id": row_id
            }
        )
    
    except ValueError as e:
        error_msg = f"Некорректные данные в форме {row_id}"
        logger.error(f"{error_msg}: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": error_msg,
                "form_id": row_id,
                "details": str(e)
            }
        )
    
    except Exception as e:
        error_msg = f"Ошибка при обработке формы {row_id}"
        logger.error(f"{error_msg}: {str(e)}")
        
        # Логируем трассировку стека для отладки
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": error_msg,
                "form_id": row_id
            }
        )


@router.get("/form-data/{row_id}")
async def get_form_data(row_id: str):
    """
    Возвращает данные формы по ID строки из Google Sheets.
    
    Args:
        row_id (str): Идентификатор строки из Google Sheets
    
    Returns:
        JSONResponse: Данные формы или сообщение об ошибке
    
    Raises:
        404: Если данные не найдены
        500: При ошибке обработки запроса
    """
    logger.info(f"Запрос данных формы для строки: {row_id}")
    
    try:
        # Получаем данные формы
        form_data = get_form_submission_by_row_id(row_id)
        
        # Если данные не найдены
        if form_data is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Данные для строки {row_id} не найдены"
                }
            )
        
        # Формируем ответ с данными
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": form_data
            }
        )
    
    except Exception as e:
        logger.error(f"Ошибка при запросе данных строки {row_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Внутренняя ошибка сервера"
            }
        )
        
        
@router.get("/check-processing/{row_id}")
async def check_processing(row_id: str):
    """
    Проверяет статус обработки формы LLM-моделью.
    
    Args:
        row_id (str): Идентификатор строки из Google Sheets
        
    Returns:
        JSONResponse: Статус обработки формы
    """
    try:
        # Получаем данные формы
        form_data = get_form_submission_by_row_id(row_id)
        
        # Если данные не найдены
        if form_data is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Данные для строки {row_id} не найдены"
                }
            )
        
        # Проверяем статус обработки
        processed = form_data.get("processed", False)
        
        # Возвращаем статус
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "row_id": row_id,
                "processed": processed,
                "last_updated": form_data.get("updated_at", "")
            }
        )
    
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса обработки для строки {row_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Внутренняя ошибка сервера: {str(e)}"
            }
        )