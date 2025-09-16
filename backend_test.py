import requests
import sys
import json
from datetime import datetime
import uuid

class MasonicTempleAPITester:
    def __init__(self, base_url="https://vasco-docs.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_tokens = {}
        self.test_users = []
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, files=None, token=None, expected_status=None):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if files:
            # Remove content-type for file uploads
            headers.pop('Content-Type', None)

        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = self.session.post(url, files=files, data=data, headers=headers)
                else:
                    response = self.session.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)
            
            if expected_status and response.status_code != expected_status:
                return False, f"Expected {expected_status}, got {response.status_code}: {response.text}"
            
            try:
                return True, response.json()
            except:
                return True, {"status_code": response.status_code, "text": response.text}
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_user_registration(self):
        """Test user registration with different levels"""
        print("\n🔍 Testing User Registration...")
        
        # Test data for different user levels
        test_cases = [
            {
                "email": f"admin@test{uuid.uuid4().hex[:8]}.com",
                "password": "AdminPass123!",
                "full_name": "Admin Test User",
                "level": 3,
                "is_admin": True
            },
            {
                "email": f"mestre@test{uuid.uuid4().hex[:8]}.com", 
                "password": "MestrePass123!",
                "full_name": "Mestre Test User",
                "level": 3,
                "is_admin": False
            },
            {
                "email": f"companheiro@test{uuid.uuid4().hex[:8]}.com",
                "password": "CompPass123!",
                "full_name": "Companheiro Test User", 
                "level": 2,
                "is_admin": False
            },
            {
                "email": f"aprendiz@test{uuid.uuid4().hex[:8]}.com",
                "password": "AprendizPass123!",
                "full_name": "Aprendiz Test User",
                "level": 1,
                "is_admin": False
            }
        ]

        for user_data in test_cases:
            success, response = self.make_request('POST', 'register', user_data, expected_status=200)
            if success:
                user_data['id'] = response.get('id')
                self.test_users.append(user_data)
                self.log_test(f"Register {user_data['full_name']}", True, f"- Level {user_data['level']}")
            else:
                self.log_test(f"Register {user_data['full_name']}", False, f"- {response}")

        # Test duplicate registration
        if self.test_users:
            duplicate_data = self.test_users[0].copy()
            success, response = self.make_request('POST', 'register', duplicate_data, expected_status=400)
            self.log_test("Duplicate registration prevention", success, "- Should reject duplicate emails")

    def test_login_pending_users(self):
        """Test login attempts with pending users (should fail)"""
        print("\n🔍 Testing Login with Pending Users...")
        
        for user in self.test_users:
            success, response = self.make_request('POST', 'login', {
                'email': user['email'],
                'password': user['password']
            }, expected_status=403)
            
            if success and 'pending approval' in response.get('detail', '').lower():
                self.log_test(f"Pending user login rejection - {user['full_name']}", True, "- Correctly rejected")
            else:
                self.log_test(f"Pending user login rejection - {user['full_name']}", False, f"- {response}")

    def test_admin_creation_and_approval(self):
        """Create admin user and test approval system"""
        print("\n🔍 Testing Admin Creation and Approval System...")
        
        # First, create the main admin user manually
        admin_data = {
            "email": "engeullerbaptista@gmail.com",
            "password": "AdminMaster123!",
            "full_name": "Engenheiro Uller Baptista",
            "level": 3
        }
        
        success, response = self.make_request('POST', 'register', admin_data)
        if success:
            admin_data['id'] = response.get('id')
            self.log_test("Admin user registration", True, "- engeullerbaptista@gmail.com created")
            
            # Manually approve the admin user by updating database (simulation)
            # In real scenario, this would be done directly in database
            print("📝 Note: Admin user needs manual approval in database for first-time setup")
            
        else:
            self.log_test("Admin user registration", False, f"- {response}")

    def test_admin_login_and_approval_functions(self):
        """Test admin login and user approval functions"""
        print("\n🔍 Testing Admin Login and Approval Functions...")
        
        # Try to login as admin (this might fail if not manually approved)
        admin_login_data = {
            "email": "engeullerbaptista@gmail.com", 
            "password": "AdminMaster123!"
        }
        
        success, response = self.make_request('POST', 'login', admin_login_data)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log_test("Admin login", True, "- Successfully logged in")
            
            # Test getting pending users
            success, response = self.make_request('GET', 'admin/pending-users', token=self.admin_token)
            if success:
                pending_count = len(response) if isinstance(response, list) else 0
                self.log_test("Get pending users", True, f"- Found {pending_count} pending users")
                
                # Test approving users
                if isinstance(response, list) and len(response) > 0:
                    for pending_user in response[:2]:  # Approve first 2 users
                        user_id = pending_user.get('id')
                        if user_id:
                            success, approve_response = self.make_request('POST', f'admin/approve-user/{user_id}', token=self.admin_token)
                            self.log_test(f"Approve user {pending_user.get('full_name', 'Unknown')}", success, f"- {approve_response}")
            else:
                self.log_test("Get pending users", False, f"- {response}")
                
        else:
            self.log_test("Admin login", False, f"- {response}")
            print("⚠️  Admin user may need manual approval in database first")

    def test_approved_user_login(self):
        """Test login with approved users"""
        print("\n🔍 Testing Approved User Login...")
        
        # Try to login with the first few test users (assuming they were approved)
        for user in self.test_users[:3]:
            success, response = self.make_request('POST', 'login', {
                'email': user['email'],
                'password': user['password']
            })
            
            if success and 'access_token' in response:
                self.user_tokens[user['email']] = response['access_token']
                user_info = response.get('user', {})
                self.log_test(f"Approved user login - {user['full_name']}", True, 
                            f"- Level {user_info.get('level')} ({user_info.get('level_name')})")
            else:
                self.log_test(f"Approved user login - {user['full_name']}", False, f"- {response}")

    def test_user_info_endpoint(self):
        """Test /me endpoint for user info"""
        print("\n🔍 Testing User Info Endpoint...")
        
        for email, token in self.user_tokens.items():
            success, response = self.make_request('GET', 'me', token=token)
            if success and 'email' in response:
                self.log_test(f"Get user info - {email}", True, 
                            f"- {response.get('full_name')} (Level {response.get('level')})")
            else:
                self.log_test(f"Get user info - {email}", False, f"- {response}")

    def test_hierarchical_access_control(self):
        """Test hierarchical access to works"""
        print("\n🔍 Testing Hierarchical Access Control...")
        
        # Test access to different levels
        for email, token in self.user_tokens.items():
            user = next((u for u in self.test_users if u['email'] == email), None)
            if not user:
                continue
                
            user_level = user['level']
            
            # Test access to each level
            for test_level in [1, 2, 3]:
                success, response = self.make_request('GET', f'works/{test_level}', token=token)
                
                if user_level >= test_level:
                    # User should have access
                    if success:
                        works_count = len(response) if isinstance(response, list) else 0
                        self.log_test(f"Access level {test_level} works - {user['full_name']}", True, 
                                    f"- {works_count} works accessible")
                    else:
                        self.log_test(f"Access level {test_level} works - {user['full_name']}", False, f"- {response}")
                else:
                    # User should NOT have access
                    if not success and '403' in str(response):
                        self.log_test(f"Blocked level {test_level} access - {user['full_name']}", True, 
                                    "- Correctly blocked")
                    else:
                        self.log_test(f"Blocked level {test_level} access - {user['full_name']}", False, 
                                    f"- Should be blocked but got: {response}")

    def test_file_upload_system(self):
        """Test PDF file upload system"""
        print("\n🔍 Testing File Upload System...")
        
        # Create a dummy PDF file content for testing
        dummy_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        for email, token in self.user_tokens.items():
            user = next((u for u in self.test_users if u['email'] == email), None)
            if not user:
                continue
                
            user_level = user['level']
            
            # Test uploading to user's own level
            files = {'file': ('test_work.pdf', dummy_pdf_content, 'application/pdf')}
            data = {'title': f'Test Work by {user["full_name"]}'}
            
            success, response = self.make_request('POST', f'upload-work/{user_level}', 
                                                data=data, files=files, token=token)
            
            if success:
                self.log_test(f"Upload work - {user['full_name']}", True, 
                            f"- Level {user_level} upload successful")
            else:
                self.log_test(f"Upload work - {user['full_name']}", False, f"- {response}")
            
            # Test uploading to higher level (should fail for lower level users)
            if user_level < 3:
                higher_level = user_level + 1
                success, response = self.make_request('POST', f'upload-work/{higher_level}', 
                                                    data=data, files=files, token=token)
                
                if not success and '403' in str(response):
                    self.log_test(f"Block higher level upload - {user['full_name']}", True, 
                                f"- Correctly blocked level {higher_level} upload")
                else:
                    self.log_test(f"Block higher level upload - {user['full_name']}", False, 
                                f"- Should block but got: {response}")

    def test_admin_user_management(self):
        """Test admin user management functions"""
        print("\n🔍 Testing Admin User Management...")
        
        if not self.admin_token:
            print("⚠️  Skipping admin tests - no admin token available")
            return
            
        # Test getting all users
        success, response = self.make_request('GET', 'admin/all-users', token=self.admin_token)
        if success:
            user_count = len(response) if isinstance(response, list) else 0
            self.log_test("Get all users", True, f"- Found {user_count} total users")
        else:
            self.log_test("Get all users", False, f"- {response}")
        
        # Test rejecting a user (if any pending)
        success, pending_response = self.make_request('GET', 'admin/pending-users', token=self.admin_token)
        if success and isinstance(pending_response, list) and len(pending_response) > 0:
            user_to_reject = pending_response[-1]  # Reject the last pending user
            user_id = user_to_reject.get('id')
            if user_id:
                success, reject_response = self.make_request('POST', f'admin/reject-user/{user_id}', token=self.admin_token)
                self.log_test(f"Reject user {user_to_reject.get('full_name', 'Unknown')}", success, f"- {reject_response}")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Masonic Temple API Tests...")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run test suites in order
        self.test_user_registration()
        self.test_login_pending_users()
        self.test_admin_creation_and_approval()
        self.test_admin_login_and_approval_functions()
        self.test_approved_user_login()
        self.test_user_info_endpoint()
        self.test_hierarchical_access_control()
        self.test_file_upload_system()
        self.test_admin_user_management()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = MasonicTempleAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())