import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select, func
import google.generativeai as genai

from app.api.deps import get_db
from app.core.config import settings
from app.models.object import Object
from app.models.inspection import Inspection
from app.models.defect import Defect
from app.models.diagnostic import Diagnostic

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not set. Bot functionality will be limited.")


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


def get_system_context(db: Session) -> str:
    """Get system context with database statistics"""
    try:
        # Get statistics
        object_count = db.exec(select(func.count(Object.object_id))).first() or 0
        inspection_count = db.exec(select(func.count(Inspection.inspection_id))).first() or 0
        defect_count = db.exec(select(func.count(Defect.defect_id))).first() or 0
        diagnostic_count = db.exec(select(func.count(Diagnostic.diag_id))).first() or 0
        
        # Get criticality distribution
        high_criticality = db.exec(
            select(func.count(Inspection.inspection_id))
            .where(Inspection.ml_label == "high")
        ).first() or 0
        
        medium_criticality = db.exec(
            select(func.count(Inspection.inspection_id))
            .where(Inspection.ml_label == "medium")
        ).first() or 0
        
        normal_criticality = db.exec(
            select(func.count(Inspection.inspection_id))
            .where(Inspection.ml_label == "normal")
        ).first() or 0
        
        context = f"""Ты - AI ассистент для системы мониторинга трубопроводов PromTech.

Текущая статистика базы данных:
- Объектов: {object_count}
- Обследований: {inspection_count}
- Дефектов: {defect_count}
- Диагностик: {diagnostic_count}
- Высокая критичность: {high_criticality}
- Средняя критичность: {medium_criticality}
- Норма: {normal_criticality}

Ты можешь отвечать на вопросы о:
- Статистике и данных в системе
- Объектах, обследованиях, дефектах
- Методах диагностики (VIK, PVK, MPK, UZK, RGK, TVK, VIBRO, MFL, TFI, GEO, UTWM, UT)
- Критичности объектов (normal, medium, high)
- Оценках качества (удовлетворительно, допустимо, требует мер, недопустимо)

Отвечай на русском языке, будь полезным и информативным. Если не знаешь точного ответа, скажи об этом честно."""
        return context
    except Exception as e:
        logger.error(f"Error getting system context: {e}")
        return "Ты - AI ассистент для системы мониторинга трубопроводов PromTech. Отвечай на русском языке."


@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    message: ChatMessage,
    db: Session = Depends(get_db),
):
    """Chat with AI bot that has access to system data"""
    
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    try:
        # Get system context
        system_context = get_system_context(db)
        
        # Initialize model
        model = genai.GenerativeModel('gemini-pro')
        
        # Create prompt with context
        prompt = f"{system_context}\n\nПользователь: {message.message}\n\nАссистент:"
        
        # Generate response
        response = model.generate_content(prompt)
        
        bot_response = response.text.strip() if response.text else "Извините, не удалось получить ответ."
        
        return ChatResponse(response=bot_response)
        
    except Exception as e:
        logger.error(f"Error in bot chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке запроса: {str(e)}"
        )

