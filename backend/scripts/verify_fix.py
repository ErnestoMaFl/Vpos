import requests
import sys

API_URL = "http://localhost:8000/api/process-voice"
USER_ID = "test-verification-user"

def run_test():
    # 1. Start Transaction
    print("1. Sending 'Vende 5 cocas'...")
    try:
        resp1 = requests.post(API_URL, json={"user_id": USER_ID, "text": "Vende 5 cocas"})
        data1 = resp1.json()
        print(f"Response: {data1.get('message')}")
    except Exception as e:
        print(f"Error contacting API: {e}")
        return

    state_id = data1.get('state_id')
    if not state_id:
        print("FAILED: No state_id returned.")
        # Depending on logic, maybe it executed immediately?
        if data1.get('action') == 'COMPLETED':
             print("Action completed immediately (unexpected for this test case).")
        return

    print(f"State ID: {state_id}")

    # 2. Confirm Transaction (passing state_id)
    print("\n2. Sending 'Sí' with state_id...")
    resp2 = requests.post(API_URL, json={"user_id": USER_ID, "text": "Sí", "state_id": state_id})
    data2 = resp2.json()
    print(f"Response: {data2}")

    if data2.get('action') == 'COMPLETED':
        print("\nSUCCESS: Transaction completed.")
    else:
        print(f"\nFAILED: Unexpected action {data2.get('action')}")

if __name__ == "__main__":
    run_test()
