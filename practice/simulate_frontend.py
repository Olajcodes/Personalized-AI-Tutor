import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def simulate_journey():
    student_id = "ajee_01"
    
    # --- Step 1: Try to jump straight to Calculus (Should fail) ---
    print(f"🚀 Attempting Calculus without prerequisites...")
    res = requests.post(f"{BASE_URL}/master-concept", json={
        "student_id": student_id,
        "concept_name": "Calculus",
        "score": 0.95
    })
    print(f"Response: {res.json()}\n")
    
    time.sleep(1) # Simulating user thinking time

    # --- Step 2: User completes Algebra (The prerequisite) ---
    print(f"✍️ Completing Algebra quiz...")
    res = requests.post(f"{BASE_URL}/master-concept", json={
        "student_id": student_id,
        "concept_name": "Algebra",
        "score": 0.88
    })
    print(f"Response: {res.json()}\n")

    # --- Step 3: Try Calculus again (Should succeed now) ---
    print(f"🔓 Attempting Calculus again after Algebra...")
    res = requests.post(f"{BASE_URL}/master-concept", json={
        "student_id": student_id,
        "concept_name": "Calculus",
        "score": 0.92
    })
    print(f"Response: {res.json()}")

if __name__ == "__main__":
    simulate_journey()