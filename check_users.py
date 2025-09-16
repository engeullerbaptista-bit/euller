import requests
import json

def check_users():
    base_url = "https://vasco-docs.preview.emergentagent.com/api"
    
    # Try to login as super admin first
    print("🔍 Checking Super Admin login...")
    admin_response = requests.post(f"{base_url}/login", json={
        "email": "vg@admin.com",
        "password": "admin123"
    })
    
    if admin_response.status_code == 200:
        admin_data = admin_response.json()
        admin_token = admin_data.get("access_token")
        print("✅ Super Admin login successful")
        
        # Get all users
        headers = {"Authorization": f"Bearer {admin_token}"}
        users_response = requests.get(f"{base_url}/super-admin/all-users-with-passwords", headers=headers)
        
        if users_response.status_code == 200:
            users = users_response.json()
            print(f"\n📋 Found {len(users)} users:")
            for user in users:
                print(f"  - {user.get('email')} | {user.get('full_name')} | Level: {user.get('level')} | Status: {user.get('status', 'NO STATUS')}")
        else:
            print(f"❌ Failed to get users: {users_response.status_code} - {users_response.text}")
    else:
        print(f"❌ Super Admin login failed: {admin_response.status_code} - {admin_response.text}")
    
    # Try test user
    print("\n🔍 Checking Test User login...")
    test_response = requests.post(f"{base_url}/login", json={
        "email": "teste@example.com",
        "password": "teste123"
    })
    
    if test_response.status_code == 200:
        print("✅ Test User login successful")
    else:
        print(f"❌ Test User login failed: {test_response.status_code} - {test_response.text}")

if __name__ == "__main__":
    check_users()