import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.logic.command_analyzer import command_analyzer
from app.logic.state_manager import state_manager

async def test_orchestrator():
    user_id = "test_user"
    
    print("\n--- TEST 1: New Intent (Venta) ---")
    # Mock AI to return a sales intent
    with patch('app.logic.ai_helpers.ai_helpers.determine_intent', new_callable=AsyncMock) as mock_intent:
        mock_intent.return_value = {
            "tipo": "crear",
            "tabla": "ventas",
            "filtros": {}
        }
        
        result = await command_analyzer.analyze(user_id, "quiero vender una coca")
        print(f"Result: {result}")
        assert result["action"] == "NEW_STATE"
        assert result["table"] == "ventas"
        
        active = state_manager.get_active_state(user_id)
        assert active is not None
        print("Active state verified.")

    print("\n--- TEST 2: Active State Update ---")
    # Mock AI to return entity extraction
    with patch('app.logic.ai_helpers.ai_helpers.clean_and_extract', new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = {"cantidad": 1, "producto": "coca cola"}
        
        # User says "son 2" (updating quantity), context is active state
        result = await command_analyzer.analyze(user_id, "son 2")
        print(f"Result: {result}")
        
        assert result["action"] == "STATE_UPDATE"
        assert result["data"]["cantidad"] == 1
        
        active_data = state_manager.get_active_state(user_id).datos_recolectados
        assert active_data["cantidad"] == 1
        print("State update verified.")

    print("\n--- TEST 3: Interruption ---")
    result = await command_analyzer.analyze(user_id, "cancelar todo")
    print(f"Result: {result}")
    assert result["action"] == "CANCEL_STATE"
    
    active = state_manager.get_active_state(user_id)
    assert active is None
    print("State cancellation verified.")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
