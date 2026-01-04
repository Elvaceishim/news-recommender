
import httpx
import time
import random
import string
import sys

BASE_URL = "http://localhost:8001"

def get_random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def verify():
    email = f"test_{get_random_string()}@example.com"
    password = "password123"
    full_name = f"Test User {get_random_string()}"
    
    print(f"--- Starting E2E Verification for user: {email} ---")
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Signup
        print("\n1. Signing up...")
        r = client.post("/auth/signup", json={
            "email": email,
            "password": password,
            "full_name": full_name
        })
        if r.status_code not in [200, 201]:
            print(f"FAILED: Signup returned {r.status_code}: {r.text}")
            sys.exit(1)
        print("SUCCESS: Signup complete.")
        
        # 2. Login
        print("\n2. Logging in...")
        # OAuth2 form request usually sends form-data
        r = client.post("/auth/login", data={
            "username": email,
            "password": password
        })
        if r.status_code != 200:
            print(f"FAILED: Login returned {r.status_code}: {r.text}")
            sys.exit(1)
        
        token = r.json().get("access_token")
        user_id = r.json().get("user_id")
        headers = {"Authorization": f"Bearer {token}"}
        print(f"SUCCESS: Logged in. User ID: {user_id}")
        
        # 3. Get Recommendations (Cold Start)
        print("\n3. Fetching Recommendations (Cold Start)...")
        r = client.get(f"/recommend?user_id={user_id}&limit=5", headers=headers)
        if r.status_code != 200:
            print(f"FAILED: Recommend returned {r.status_code}: {r.text}")
            sys.exit(1)
        
        recs = r.json()
        print(f"SUCCESS: Got {len(recs)} articles.")
        if len(recs) == 0:
            print("WARNING: No articles found. Is the DB empty?")
            # We won't fail here because empty DB is a valid state, but we can't test interactions well.
            # If we want to be strict, we might want to ingest some dummy data first.
        
        if recs:
            # 4. Interact with first article
            article = recs[0]
            print(f"\n4. Interacting with article {article['id']} ({article['title']})...")
            
            r = client.post("/interactions", json={
                "user_id": user_id,
                "article_id": article['id'],
                "interaction_type": "click"
            }, headers=headers)
            
            if r.status_code != 200:
                print(f"FAILED: Interaction log returned {r.status_code}: {r.text}")
                sys.exit(1)
            print("SUCCESS: Interaction logged.")
            
            # 5. Re-fetch Recommendations
            print("\n5. Fetching Recommendations (After Interaction)...")
            # Give background task a moment? Usually async triggers fast.
            time.sleep(1) 
            
            r = client.get(f"/recommend?user_id={user_id}&limit=5", headers=headers)
            if r.status_code != 200:
                print(f"FAILED: Recommend returned {r.status_code}: {r.text}")
                sys.exit(1)
            
            new_recs = r.json()
            print(f"SUCCESS: Got {len(new_recs)} articles.")
            
    print("\n--- E2E VERIFICATION PASSED ---")

if __name__ == "__main__":
    # Wait a bit for server to be likely ready if script runs immediately after server start command
    time.sleep(2)
    try:
        verify()
    except httpx.ConnectError:
        print("FAILED: Could not connect to localhost:8001. Is the server running?")
        sys.exit(1)
    except Exception as e:
        print(f"FAILED: Unexpected error: {e}")
        sys.exit(1)
