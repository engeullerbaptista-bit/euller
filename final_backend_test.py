import requests
import sys
import json

class FinalMasonicTest:
    def __init__(self, base_url="https://temple-access.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def test_registration_and_login_flow(self):
        """Test complete registration and login flow"""
        print("\n🔍 Testing Complete Registration and Login Flow...")
        
        # Test registration
        user_data = {
            "email": "final.test@temple.com",
            "password": "FinalTest123!",
            "full_name": "Final Test User",
            "level": 2
        }
        
        try:
            response = requests.post(f"{self.base_url}/register", json=user_data)
            if response.status_code == 200:
                user_info = response.json()
                self.log_test("User Registration", True, f"- User ID: {user_info.get('id')}")
                
                # Test login with pending user (should fail)
                login_response = requests.post(f"{self.base_url}/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                
                if login_response.status_code == 403 and "pending" in login_response.json().get("detail", "").lower():
                    self.log_test("Pending User Login Block", True, "- Correctly blocked pending user")
                else:
                    self.log_test("Pending User Login Block", False, f"- {login_response.json()}")
                
                return user_info.get('id')
            else:
                self.log_test("User Registration", False, f"- {response.json()}")
                return None
        except Exception as e:
            self.log_test("User Registration", False, f"- {str(e)}")
            return None

    def test_approved_user_functionality(self):
        """Test functionality with approved users"""
        print("\n🔍 Testing Approved User Functionality...")
        
        # Test with existing approved users
        test_users = [
            {"email": "admin.temple@masonic.com", "password": "AdminTemple123!", "level": 3},
            {"email": "test@example.com", "password": "TestPass123!", "level": 1}
        ]
        
        for user in test_users:
            try:
                # Test login
                login_response = requests.post(f"{self.base_url}/login", json={
                    "email": user["email"],
                    "password": user["password"]
                })
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    token = login_data.get("access_token")
                    user_info = login_data.get("user", {})
                    
                    self.log_test(f"Login - {user['email']}", True, 
                                f"- Level {user_info.get('level')} ({user_info.get('level_name')})")
                    
                    # Test /me endpoint
                    headers = {"Authorization": f"Bearer {token}"}
                    me_response = requests.get(f"{self.base_url}/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        self.log_test(f"User Info - {user['email']}", True, "- /me endpoint working")
                    else:
                        self.log_test(f"User Info - {user['email']}", False, f"- {me_response.json()}")
                    
                    # Test hierarchical access
                    user_level = user_info.get('level', 1)
                    for test_level in [1, 2, 3]:
                        works_response = requests.get(f"{self.base_url}/works/{test_level}", headers=headers)
                        
                        if user_level >= test_level:
                            # Should have access
                            if works_response.status_code == 200:
                                works = works_response.json()
                                self.log_test(f"Access Level {test_level} - {user['email']}", True, 
                                            f"- {len(works)} works accessible")
                            else:
                                self.log_test(f"Access Level {test_level} - {user['email']}", False, 
                                            f"- {works_response.json()}")
                        else:
                            # Should NOT have access
                            if works_response.status_code == 403:
                                self.log_test(f"Block Level {test_level} - {user['email']}", True, 
                                            "- Correctly blocked")
                            else:
                                self.log_test(f"Block Level {test_level} - {user['email']}", False, 
                                            f"- Should be blocked: {works_response.json()}")
                
                else:
                    self.log_test(f"Login - {user['email']}", False, f"- {login_response.json()}")
                    
            except Exception as e:
                self.log_test(f"User Test - {user['email']}", False, f"- {str(e)}")

    def test_file_upload_api(self):
        """Test file upload API"""
        print("\n🔍 Testing File Upload API...")
        
        # Login as admin user
        try:
            login_response = requests.post(f"{self.base_url}/login", json={
                "email": "admin.temple@masonic.com",
                "password": "AdminTemple123!"
            })
            
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Create dummy PDF content
                pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n32\n%%EOF"
                
                # Test upload
                files = {'file': ('test.pdf', pdf_content, 'application/pdf')}
                data = {'title': 'API Test Upload'}
                
                upload_response = requests.post(
                    f"{self.base_url}/upload-work/3?title=API Test Upload",
                    files=files,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if upload_response.status_code == 200:
                    self.log_test("File Upload API", True, "- PDF upload successful")
                else:
                    self.log_test("File Upload API", False, f"- {upload_response.json()}")
            else:
                self.log_test("File Upload API", False, "- Admin login failed")
                
        except Exception as e:
            self.log_test("File Upload API", False, f"- {str(e)}")

    def run_final_tests(self):
        """Run all final tests"""
        print("🚀 Running Final Masonic Temple API Tests...")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        self.test_registration_and_login_flow()
        self.test_approved_user_functionality()
        self.test_file_upload_api()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 FINAL TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL FINAL TESTS PASSED!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = FinalMasonicTest()
    return tester.run_final_tests()

if __name__ == "__main__":
    sys.exit(main())