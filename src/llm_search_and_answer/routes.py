# src/llm_search_and_answer/routes.py
from fastapi import APIRouter, HTTPException
from src.llm_search_and_answer.services import run_full_reasoning_pipeline
from src.llm_search_and_answer.models import QuestionRequest, FullReasoningResponse, AnswerResponse

router = APIRouter(prefix="/llm", tags=["LLM Search & Answer"])

@router.post("/full-reasoning", response_model=FullReasoningResponse)
def full_reasoning(payload: QuestionRequest):
    """
    Запускает полный пайплайн рассуждения и возвращает итоговые результаты.
    
    Принимает:
      - payload (QuestionRequest): тело запроса с текстом вопроса.
    
    Возвращает:
      - FullReasoningResponse: все этапы рассуждения и финальный ответ.
    """
    try:
        result = run_full_reasoning_pipeline(payload.question)
        return FullReasoningResponse(
            part_reasoning=result["part_reasoning"],
            chapter_reasoning=result["chapter_reasoning"],
            subchapter_reasoning=result["subchapter_reasoning"],
            final_answer=AnswerResponse(answer=result["final_answer"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
