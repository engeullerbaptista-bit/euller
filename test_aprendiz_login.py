import requests

def test_aprendiz_passwords():
    base_url = "https://vasco-docs.preview.emergentagent.com/api"
    
    passwords_to_try = ["teste123", "aprendiz123", "123456", "password"]
    
    for password in passwords_to_try:
        print(f"🔍 Trying password: {password}")
        response = requests.post(f"{base_url}/login", json={
            "email": "aprendiz@teste.com",
            "password": password
        })
        
        if response.status_code == 200:
            print(f"✅ Success with password: {password}")
            user_data = response.json()
            print(f"   User: {user_data.get('user', {})}")
            return password
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    
    return None

if __name__ == "__main__":
    test_aprendiz_passwords()