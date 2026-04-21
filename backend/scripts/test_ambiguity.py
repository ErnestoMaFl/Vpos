import asyncio
import json
from app.services.search_service import search_service
from app.logic.command_analyzer import command_analyzer, VPosState

async def test_ambiguity_flow():
    query = "coca"
    print(f"--- 1. Testing Search Service Ambiguity for '{query}' ---")
    
    # Direct Service Test
    result = await search_service.search_product(query)
    print("Search Result Keys:", result.keys())
    if result.get("method") == "ambiguous":
        print("SUCCESS: Search service detected ambiguity.")
        print("Candidates:", [c['nombre'] for c in result.get('candidates', [])])
    else:
        print(f"FAILURE: Search service returned method '{result.get('method')}' instead of 'ambiguous'")
        print("Winner:", result.get("ganador"))

    print("\n--- 2. Testing Command Analyzer Ambiguity Handling ---")
    
    # Mock State
    mock_state = VPosState(
        user_id="test-ambiguity-user",
        command_origin="Vende coca",
        valor_retorno_esperado="campos_para_vpos_ventas",
        datos_recolectados={"producto": "coca", "cantidad": 1}
    )
    # Persist state to satisfy FK
    from app.logic.state_manager import state_manager
    state_manager.push_state("test-ambiguity-user", mock_state)

    
    # Execute Action
    try:
        action_res = await command_analyzer._execute_action(mock_state)
        # print("Action Result:", json.dumps(action_res, indent=2, default=str)) 
    except Exception as e:
        print(f"CRITICAL EXCEPTION in _execute_action: {e}")
        return

    if action_res.get("action") == "AMBIGUITY_DETECTED":
        print("SUCCESS: Command Analyzer returned AMBIGUITY_DETECTED.")
        print("Message:", action_res.get("message"))
    else:
        print(f"FAILURE: Command Analyzer returned '{action_res.get('action')}'")
        print("Message:", action_res.get("message"))
        if action_res.get("details"):
             print("Details:", action_res.get("details"))


if __name__ == "__main__":
    asyncio.run(test_ambiguity_flow())
