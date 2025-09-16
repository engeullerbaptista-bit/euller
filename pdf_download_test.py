import requests
import sys
import json
import os
from pathlib import Path

class PDFDownloadTester:
    def __init__(self, base_url="https://vasco-docs.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.tokens = {}
        self.work_files = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, files=None, token=None, expected_status=None, stream=False):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if not files and data:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, stream=stream)
            elif method == 'POST':
                if files:
                    response = self.session.post(url, files=files, data=data, headers=headers)
                else:
                    response = self.session.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)
            
            if expected_status and response.status_code != expected_status:
                return False, f"Expected {expected_status}, got {response.status_code}: {response.text}"
            
            if stream or response.headers.get('content-type', '').startswith('application/pdf'):
                return True, response
            
            try:
                return True, response.json()
            except:
                return True, {"status_code": response.status_code, "text": response.text}
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_authentication_login(self):
        """Test user authentication and login functionality"""
        print("\n🔍 Testing Authentication and Login...")
        
        # Test users as specified in the review request
        test_users = [
            {
                "email": "vg@admin.com",
                "password": "admin123",
                "role": "Super Admin",
                "expected_level": 3
            },
            {
                "email": "teste@example.com", 
                "password": "teste123",
                "role": "Test User",
                "expected_level": 1
            }
        ]
        
        for user in test_users:
            success, response = self.make_request('POST', 'login', {
                'email': user['email'],
                'password': user['password']
            })
            
            if success and 'access_token' in response:
                self.tokens[user['email']] = response['access_token']
                user_info = response.get('user', {})
                self.log_test(f"Login - {user['role']}", True, 
                            f"- Level {user_info.get('level')} ({user_info.get('level_name')})")
                
                # Verify user level matches expected
                if user_info.get('level') == user['expected_level']:
                    self.log_test(f"Level verification - {user['role']}", True, 
                                f"- Correct level {user['expected_level']}")
                else:
                    self.log_test(f"Level verification - {user['role']}", False, 
                                f"- Expected level {user['expected_level']}, got {user_info.get('level')}")
            else:
                self.log_test(f"Login - {user['role']}", False, f"- {response}")

    def test_upload_test_files(self):
        """Upload test PDF files for different levels to test download functionality"""
        print("\n🔍 Uploading Test PDF Files...")
        
        # Create dummy PDF content for testing
        dummy_pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        
        # Use Super Admin token to upload files for different levels
        admin_token = self.tokens.get("vg@admin.com")
        if not admin_token:
            print("⚠️  No admin token available for file upload")
            return
        
        test_files = [
            {"level": 1, "title": "Aprendiz Test Document"},
            {"level": 2, "title": "Companheiro Test Document"}, 
            {"level": 3, "title": "Mestre Test Document"}
        ]
        
        for file_info in test_files:
            files = {'file': (f'test_level_{file_info["level"]}.pdf', dummy_pdf_content, 'application/pdf')}
            data = {'title': file_info['title']}
            
            success, response = self.make_request('POST', f'upload-work/{file_info["level"]}', 
                                                data=data, files=files, token=admin_token)
            
            if success and 'file_id' in response:
                file_id = response['file_id']
                self.work_files.append({
                    'id': file_id,
                    'level': file_info['level'],
                    'title': file_info['title']
                })
                self.log_test(f"Upload Level {file_info['level']} PDF", True, 
                            f"- File ID: {file_id}")
            else:
                self.log_test(f"Upload Level {file_info['level']} PDF", False, f"- {response}")

    def test_work_file_endpoint(self):
        """Test the work-file endpoint used by download functionality"""
        print("\n🔍 Testing Work-File Endpoint...")
        
        for email, token in self.tokens.items():
            user_role = "Super Admin" if email == "vg@admin.com" else "Test User"
            user_level = 3 if email == "vg@admin.com" else 1
            
            for work_file in self.work_files:
                work_id = work_file['id']
                work_level = work_file['level']
                
                success, response = self.make_request('GET', f'work-file/{work_id}', 
                                                    token=token, stream=True)
                
                # Check if user should have access based on hierarchy
                should_have_access = user_level >= work_level
                
                if should_have_access:
                    if success and hasattr(response, 'headers'):
                        content_type = response.headers.get('content-type', '')
                        if 'application/pdf' in content_type:
                            self.log_test(f"Work-file access L{work_level} - {user_role}", True, 
                                        f"- PDF served correctly")
                        else:
                            self.log_test(f"Work-file access L{work_level} - {user_role}", False, 
                                        f"- Wrong content type: {content_type}")
                    else:
                        self.log_test(f"Work-file access L{work_level} - {user_role}", False, 
                                    f"- {response}")
                else:
                    # Should be blocked
                    if not success and ('403' in str(response) or 'permission' in str(response).lower()):
                        self.log_test(f"Work-file block L{work_level} - {user_role}", True, 
                                    "- Correctly blocked access")
                    else:
                        self.log_test(f"Work-file block L{work_level} - {user_role}", False, 
                                    f"- Should be blocked but got: {response}")

    def test_pdf_download_endpoint(self):
        """Test the PDF download endpoint with proper authentication headers"""
        print("\n🔍 Testing PDF Download Endpoint...")
        
        for email, token in self.tokens.items():
            user_role = "Super Admin" if email == "vg@admin.com" else "Test User"
            user_level = 3 if email == "vg@admin.com" else 1
            
            for work_file in self.work_files:
                work_id = work_file['id']
                work_level = work_file['level']
                work_title = work_file['title']
                
                success, response = self.make_request('GET', f'download-work/{work_id}', 
                                                    token=token, stream=True)
                
                # Check if user should have access based on hierarchy
                should_have_access = user_level >= work_level
                
                if should_have_access:
                    if success and hasattr(response, 'headers'):
                        # Verify PDF content type
                        content_type = response.headers.get('content-type', '')
                        content_disposition = response.headers.get('content-disposition', '')
                        
                        if 'application/pdf' in content_type:
                            self.log_test(f"Download L{work_level} content-type - {user_role}", True, 
                                        f"- Correct PDF content-type")
                        else:
                            self.log_test(f"Download L{work_level} content-type - {user_role}", False, 
                                        f"- Wrong content-type: {content_type}")
                        
                        # Verify download headers
                        if 'attachment' in content_disposition:
                            self.log_test(f"Download L{work_level} headers - {user_role}", True, 
                                        f"- Correct download headers")
                        else:
                            self.log_test(f"Download L{work_level} headers - {user_role}", False, 
                                        f"- Missing attachment header: {content_disposition}")
                        
                        # Verify file content is PDF
                        try:
                            content = response.content[:10]  # Read first 10 bytes
                            if content.startswith(b'%PDF'):
                                self.log_test(f"Download L{work_level} content - {user_role}", True, 
                                            f"- Valid PDF content")
                            else:
                                self.log_test(f"Download L{work_level} content - {user_role}", False, 
                                            f"- Invalid PDF content")
                        except Exception as e:
                            self.log_test(f"Download L{work_level} content - {user_role}", False, 
                                        f"- Error reading content: {e}")
                    else:
                        self.log_test(f"Download L{work_level} - {user_role}", False, 
                                    f"- {response}")
                else:
                    # Should be blocked
                    if not success and ('403' in str(response) or 'permission' in str(response).lower()):
                        self.log_test(f"Download block L{work_level} - {user_role}", True, 
                                    "- Correctly blocked download")
                    else:
                        self.log_test(f"Download block L{work_level} - {user_role}", False, 
                                    f"- Should be blocked but got: {response}")

    def test_access_control_hierarchy(self):
        """Test access control based on Masonic level hierarchy"""
        print("\n🔍 Testing Masonic Level Hierarchy Access Control...")
        
        # Test hierarchy rules:
        # Aprendiz (1) sees Aprendiz
        # Companheiro (2) sees Aprendiz + Companheiro  
        # Mestre (3) sees all
        
        hierarchy_tests = [
            {
                "user_email": "teste@example.com",
                "user_level": 1,
                "user_role": "Test User (Aprendiz)",
                "should_access": [1],
                "should_block": [2, 3]
            },
            {
                "user_email": "vg@admin.com", 
                "user_level": 3,
                "user_role": "Super Admin (Mestre)",
                "should_access": [1, 2, 3],
                "should_block": []
            }
        ]
        
        for test_case in hierarchy_tests:
            user_token = self.tokens.get(test_case['user_email'])
            if not user_token:
                continue
                
            # Test access to allowed levels
            for level in test_case['should_access']:
                level_files = [f for f in self.work_files if f['level'] == level]
                for work_file in level_files:
                    success, response = self.make_request('GET', f'download-work/{work_file["id"]}', 
                                                        token=user_token, stream=True)
                    
                    if success and hasattr(response, 'headers'):
                        self.log_test(f"Hierarchy access L{level} - {test_case['user_role']}", True, 
                                    f"- Correctly allowed access")
                    else:
                        self.log_test(f"Hierarchy access L{level} - {test_case['user_role']}", False, 
                                    f"- Should allow access: {response}")
            
            # Test blocking of restricted levels
            for level in test_case['should_block']:
                level_files = [f for f in self.work_files if f['level'] == level]
                for work_file in level_files:
                    success, response = self.make_request('GET', f'download-work/{work_file["id"]}', 
                                                        token=user_token, stream=True)
                    
                    if not success and ('403' in str(response) or 'permission' in str(response).lower()):
                        self.log_test(f"Hierarchy block L{level} - {test_case['user_role']}", True, 
                                    f"- Correctly blocked access")
                    else:
                        self.log_test(f"Hierarchy block L{level} - {test_case['user_role']}", False, 
                                    f"- Should block access: {response}")

    def test_unauthenticated_access(self):
        """Test that unauthenticated requests are properly blocked"""
        print("\n🔍 Testing Unauthenticated Access Protection...")
        
        if not self.work_files:
            print("⚠️  No work files available for unauthenticated testing")
            return
            
        work_id = self.work_files[0]['id']
        
        # Test download without token
        success, response = self.make_request('GET', f'download-work/{work_id}')
        if not success and ('401' in str(response) or 'unauthorized' in str(response).lower()):
            self.log_test("Unauthenticated download block", True, "- Correctly blocked")
        else:
            self.log_test("Unauthenticated download block", False, f"- Should block: {response}")
        
        # Test work-file without token
        success, response = self.make_request('GET', f'work-file/{work_id}')
        if not success and ('401' in str(response) or 'unauthorized' in str(response).lower()):
            self.log_test("Unauthenticated work-file block", True, "- Correctly blocked")
        else:
            self.log_test("Unauthenticated work-file block", False, f"- Should block: {response}")

    def run_all_tests(self):
        """Run all PDF download functionality tests"""
        print("🚀 Starting PDF Download Functionality Tests...")
        print(f"🔗 Testing against: {self.base_url}")
        print("📋 Focus: PDF download functionality after removing PDF visualization")
        print("=" * 70)
        
        # Run test suites in order
        self.test_authentication_login()
        self.test_upload_test_files()
        self.test_work_file_endpoint()
        self.test_pdf_download_endpoint()
        self.test_access_control_hierarchy()
        self.test_unauthenticated_access()
        
        # Print final results
        print("\n" + "=" * 70)
        print(f"📊 PDF DOWNLOAD TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL PDF DOWNLOAD TESTS PASSED!")
            print("✅ PDF download functionality is working correctly")
            print("✅ Access control hierarchy is properly enforced")
            print("✅ Authentication is working as expected")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed")
            print("❌ PDF download functionality has issues that need attention")
            return 1

def main():
    tester = PDFDownloadTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())