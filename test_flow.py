import requests

BASE_URL = "http://localhost:5000/api"

def login(email, password):
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    return r.json()

def test_flow():
    print("Logging in as citizen...")
    # Wait, I don't know citizen email. Will use the test users from database.py.
    # ('System Admin', 'admin@system.com', 'admin@123', 'admin', 'General'),
    # ('Waste Expert', 'waste@test.com', 'password123', 'vendor', 'Waste Management'),
    # Wait, there's no citizen. I will register one.
    
    # Register citizen
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Test Citizen", "email": "cit@test.com", "password": "password123", "role": "citizen"
    })
    
    # Login citizen
    cit_token = login("cit@test.com", "password123")["data"]["token"]
    cit_header = {"Authorization": f"Bearer {cit_token}"}
    
    # Create complaint
    r = requests.post(f"{BASE_URL}/complaints", json={
        "category": "Other", "description": "Test diff", "location": "Here"
    }, headers=cit_header)
    comp_id = r.json()["data"]["id"]
    print(f"Complaint {comp_id} created.")
    
    # Login Admin
    admin_token = login("admin@system.com", "admin@123")["data"]["token"]
    admin_header = {"Authorization": f"Bearer {admin_token}"}
    
    # Route to private
    r = requests.post(f"{BASE_URL}/admin/route/private", json={"complaint_id": comp_id}, headers=admin_header)
    print("Routed:", r.json())
    
    # Login Vendor
    ven_token = login("waste@test.com", "password123")["data"]["token"]
    ven_header = {"Authorization": f"Bearer {ven_token}"}
    
    # Submit quote
    r = requests.post(f"{BASE_URL}/vendor/quote", json={
        "complaint_id": comp_id, "price": "100.5", "estimated_time": "1 day"
    }, headers=ven_header)
    print("Quote Submit:", r.json())
    
    # Citizen fetches complaints
    r = requests.get(f"{BASE_URL}/complaints/my", headers=cit_header)
    print("Citizen Complaints:", r.json())
    
    # Citizen fetches quotes
    r = requests.get(f"{BASE_URL}/complaints/{comp_id}/quotes", headers=cit_header)
    print("Citizen Quotes:", r.json())

if __name__ == "__main__":
    test_flow()
