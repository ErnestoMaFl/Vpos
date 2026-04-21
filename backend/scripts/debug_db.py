from app.logic.state_manager import state_manager, VPosState
from app.core.config import settings
import uuid
import json

def test_db():
    log_file = open("debug_output.txt", "w", encoding="utf-8")
    
    def log(msg):
        print(msg)
        log_file.write(str(msg) + "\n")

    log(f"URL: {settings.SUPABASE_URL}")
    log(f"KEY: {settings.SUPABASE_KEY[:5]}...")

    user_id = "debug-user-" + str(uuid.uuid4())[:8]
    log(f"Testing with User: {user_id}")

    # 1. Create State
    state = VPosState(
        user_id=user_id,
        command_origin="Test Command",
        valor_retorno_esperado="test_value"
    )
    
    log(f"Pushing state {state.id}...")
    try:
        # We need to call internal logic of push_state to actually see the error if it swallows it
        # But wait, push_state catches exception. 
        # So we should probably try to replicate push_state logic here to see the error.
        
        data = state.model_dump()
        data['timestamp_creacion'] = data['timestamp_creacion'].isoformat()
        data['timestamp_ultima_actividad'] = data['timestamp_ultima_actividad'].isoformat()
        
        log(f"Data to insert: {json.dumps(data, default=str)}")
        
        res = state_manager.supabase.table("vpos_estados").insert(data).execute()
        log(f"Insert Result: {res}")
        
    except Exception as e:
        log(f"DIRECT INSERT FAILED: {e}")
        import traceback
        traceback.print_exc(file=log_file)

    # 2. Retrieve State
    log(f"Retrieving state {state.id}...")
    fetched = state_manager.get_state_by_id(state.id)
    
    if fetched:
        log("SUCCESS: State retrieved from DB.")
    else:
        log("FAILED: State NOT found in DB.")

    log_file.close()

if __name__ == "__main__":
    test_db()
