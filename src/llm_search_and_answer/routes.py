# src/llm_search_and_answer/routes.py
from fastapi import APIRouter, HTTPException
from typing import Union
from src.llm_search_and_answer.services import run_full_reasoning_pipeline
from src.llm_search_and_answer.models import QuestionRequest, FullReasoningResponse, AnswerResponse

router = APIRouter(prefix="/llm", tags=["LLM Search & Answer"])

@router.post("/full-reasoning", response_model=AnswerResponse)
def full_reasoning(payload: QuestionRequest):
    """
    Запускает полный пайплайн рассуждения и возвращает только итоговый ответ.
    
    Принимает:
      - payload (QuestionRequest): тело запроса с текстом вопроса.
    
    Возвращает:
      - FinalAnswerOnlyResponse: объект с единственным полем final_answer.
    """
    try:
        result = run_full_reasoning_pipeline(payload.question)
        return AnswerResponse(answer=result["final_answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
