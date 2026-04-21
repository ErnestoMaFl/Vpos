import requests
from app.logic.state_manager import state_manager
import json

API_URL = "http://localhost:8000/api/process-voice"
USER_ID = "test-sales-user"

def run_test():
    print(f"Testing Sales Logic for User: {USER_ID}")
    
    # 1. Start Sale
    print("\n1. Sending 'Vende 2 cocas'...")
    resp1 = requests.post(API_URL, json={"user_id": USER_ID, "text": "Vende 2 cocas"})
    data1 = resp1.json()
    print(f"Response: {data1.get('message')}")
    
    state_id = data1.get('state_id')
    if not state_id:
        print("FAILED: No state_id returned.")
        return

    print(f"State ID: {state_id}")

    # 2. Confirm Sale
    print("\n2. Sending 'Sí'...")
    resp2 = requests.post(API_URL, json={"user_id": USER_ID, "text": "Sí", "state_id": state_id})
    data2 = resp2.json()
    print(f"Response: {data2}")
    
    if data2.get('action') == 'COMPLETED':
        print("API Transaction Completed.")
        
        # 3. Verify DB
        print("\n3. Verifying Database...")
        # Start fetch
        res = state_manager.supabase.table("vpos_ventas")\
            .select("*")\
            .eq("user_id", USER_ID)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
            
        if res.data:
            latest = res.data[0]
            print(f"Success! Found sale in DB:")
            print(json.dumps(latest, indent=2, default=str))
            
            if latest['cantidad'] == 2 and 'coca' in latest['nombre_producto'].lower():
                 print("Data validation PASS.")
            else:
                 print("Data validation FAIL (content mismatch).")
        else:
            print("FAILED: No record found in vpos_ventas.")
    else:
        print(f"FAILED: Transaction not completed. Full Response: {json.dumps(data2, indent=2, default=str)}")

if __name__ == "__main__":
    run_test()
