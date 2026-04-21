import asyncio
from app.logic.command_analyzer import command_analyzer, VPosState
from app.logic.state_manager import state_manager

async def test_stacking_failure():
    user_id = "test-stacking-user"
    
    # 1. Setup State: "Vende coca" -> Ambiguity
    # Simulate we are stuck in ambiguity
    ambiguous_state = VPosState(
        user_id=user_id,
        command_origin="Vende coca",
        valor_retorno_esperado="campos_para_vpos_ventas",
        datos_recolectados={
            "producto": "coca",
            "cantidad": 3,
            "_ambiguity_candidates": [{"id": 1, "nombre": "Coca 600"}, {"id": 2, "nombre": "Coca 2.5L"}]
        }
    )
    state_manager.push_state(user_id, ambiguous_state)
    print(f"State created (Ambiguous): {ambiguous_state.id}")

    # 2. User tries to switch context: "Precio del gansito"
    # EXPECTED: System starts NEW state/search for gansito.
    # ACTUAL (Reported): System returns INFO "No entendí..."
    print("\n--- Sending New Command: 'Precio del gansito' ---")
    res = await command_analyzer.analyze(user_id, "Precio del gansito")
    
    print("Action:", res.get("action"))
    print("Message:", res.get("message"))
    
    if res.get("action") == "INFO" and "No entendí" in res.get("message", ""):
        print("FAILURE: System trapped in ambiguity loop.")
    elif res.get("action") in ["SEARCH_RESULT", "NEW_STATE"]:
        print("SUCCESS: System correctly prioritized new intent.")
    else:
        print("UNCLEAR:", res)

if __name__ == "__main__":
    asyncio.run(test_stacking_failure())
