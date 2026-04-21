from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.logic.command_analyzer import command_analyzer
from app.logic.state_manager import state_manager

router = APIRouter()

class VoiceRequest(BaseModel):
    user_id: str
    text: str
    state_id: Optional[str] = None

@router.post("/process-voice")
async def process_voice(request: VoiceRequest):
    result = await command_analyzer.analyze(request.user_id, request.text, request.state_id)
    return result

@router.get("/states/{user_id}")
async def get_active_states(user_id: str):
    """
    Returns all active (uncompleted) states for the user.
    """
    states = state_manager.get_all_active_states(user_id)
    return {"states": [s.model_dump() for s in states]}

@router.get("/state/{state_id}/analysis")
async def get_state_analysis(state_id: str):
    """
    Returns the current analysis/completion status of a specific state.
    Used for hydrating the UI when switching contexts.
    """
    state = state_manager.get_state_by_id(state_id)
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    # Re-run completion check to get current status message and missing fields
    # Accessing internal method _check_completion - acceptable for this coupling
    check = command_analyzer._check_completion(state)
    
    return {
        "action": "STATE_UPDATE",
        "state_id": state.id,
        "data": state.datos_recolectados,
        "message": check["message"],
        "missing_fields": check.get("missing", []),
        "context": state.valor_retorno_esperado
    }

class SearchRequest(BaseModel):
    query: str
    context: Optional[str] = "general"

@router.post("/test-search")
async def test_search(request: SearchRequest):
    from app.services.search_service import search_service
    return await search_service.search_product(request.query, request.context)
