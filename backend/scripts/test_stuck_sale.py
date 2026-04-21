import asyncio
from app.logic.command_analyzer import command_analyzer, VPosState
from app.logic.state_manager import state_manager

async def test_stuck_sale():
    user_id = "test-stuck-user"
    
    # 1. Setup Active Sale Ambiguity State
    stuck_state = VPosState(
        user_id=user_id,
        command_origin="Vende coca",
        valor_retorno_esperado="campos_para_vpos_ventas",
        datos_recolectados={
            "producto": "coca",
            "_ambiguity_candidates": [{"id": 1, "nombre": "Option A"}, {"id": 2, "nombre": "Option B"}]
        }
    )
    state_manager.push_state(user_id, stuck_state)
    print(f"Stuck State Created: {stuck_state.id}")

    # 2. User tries NEW SALE: "Vende 5 pepsis"
    # Current logic might trap this because table vpos_ventas == vpos_ventas
    print("\n--- Sending New Sale Command: 'Vende 5 pepsis' ---")
    res = await command_analyzer.analyze(user_id, "Vende 5 pepsis")
    
    print("Action:", res.get("action"))
    print("Message:", res.get("message"))
    
    if res.get("action") == "INFO" and "No entendí" in res.get("message", ""):
        print("FAILURE: System trapped in ambiguity loop.")
    elif res.get("action") == "NEW_STATE" or res.get("action") == "AMBIGUITY_DETECTED": 
        # Note: If it detects 'pepsis' ambiguity or creates new state, that's success (broke out of old loop)
        print("SUCCESS: System recognized new command.")
    else:
        print("UNCLEAR:", res)

if __name__ == "__main__":
    asyncio.run(test_stuck_sale())
