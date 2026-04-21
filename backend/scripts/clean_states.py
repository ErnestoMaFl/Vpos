from app.logic.state_manager import state_manager

def clean_states():
    user_id = "demo-user"
    print(f"Cleaning states for {user_id}...")
    
    # Loop until no active states remain
    while True:
        state = state_manager.pop_state(user_id)
        if not state:
            break
        print(f"Popped state: {state.id} ({state.command_origin})")

    print("All states cleaned.")

if __name__ == "__main__":
    clean_states()
