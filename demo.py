#!/usr/bin/env python3
"""
Interactive demo script for OTP Authentication Service.
Tests all endpoints and demonstrates API functionality.
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
SWAGGER_URL = "http://localhost:8000/api/docs/"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_response(response: requests.Response, title: str = "Response"):
    """Pretty print API response"""
    print(f"\n{Colors.BOLD}{title}:{Colors.ENDC}")
    print(f"Status Code: {Colors.OKBLUE}{response.status_code}{Colors.ENDC}")
    try:
        data = response.json()
        print(f"Body:\n{json.dumps(data, indent=2)}")
    except:
        print(f"Body: {response.text}")

def test_swagger_ui():
    """Test that Swagger UI is accessible"""
    print_header("TEST 1: Swagger UI Documentation")
    print_info(f"Open browser to: {SWAGGER_URL}")
    try:
        response = requests.get(SWAGGER_URL)
        if response.status_code == 200:
            print_success(f"Swagger UI is accessible at {SWAGGER_URL}")
        else:
            print_error(f"Swagger UI returned status {response.status_code}")
    except Exception as e:
        print_error(f"Could not connect to Swagger UI: {e}")

def test_otp_request(email: str) -> Optional[Dict[str, Any]]:
    """Test OTP request endpoint"""
    print_header("TEST 2: OTP Request Endpoint")
    print_info(f"Requesting OTP for: {email}")
    
    url = f"{BASE_URL}/auth/otp/request/"
    payload = {"email": email}
    
    try:
        response = requests.post(url, json=payload)
        print_response(response, "OTP Request Response")
        
        if response.status_code == 202:
            print_success("OTP request successful (202 Accepted)")
            return response.json()
        else:
            print_error(f"OTP request failed with status {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error requesting OTP: {e}")
        return None

def test_otp_rate_limit(email: str):
    """Test OTP rate limiting"""
    print_header("TEST 3: OTP Rate Limiting (3 requests per 10 minutes)")
    print_info(f"Making 4 rapid OTP requests for {email}...")
    
    url = f"{BASE_URL}/auth/otp/request/"
    payload = {"email": email}
    
    for i in range(4):
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 202:
                print_success(f"Request {i+1}/4: Accepted (202)")
            elif response.status_code == 429:
                data = response.json()
                retry_after = data.get('data', {}).get('retry_after_seconds', 'unknown')
                print_warning(f"Request {i+1}/4: Rate limited (429) - Retry after {retry_after}s")
            else:
                print_error(f"Request {i+1}/4: Unexpected status {response.status_code}")
        except Exception as e:
            print_error(f"Request {i+1}/4: Error - {e}")
        time.sleep(0.5)

def test_otp_verify(email: str, otp: str) -> Optional[Dict[str, Any]]:
    """Test OTP verification endpoint"""
    print_header("TEST 4: OTP Verification (Success)")
    print_info(f"Verifying OTP for {email}")
    
    url = f"{BASE_URL}/auth/otp/verify/"
    payload = {"email": email, "otp": otp}
    
    try:
        response = requests.post(url, json=payload)
        print_response(response, "OTP Verification Response")
        
        if response.status_code == 201:
            print_success("OTP verified successfully (201 Created)")
            data = response.json()
            if 'data' in data and 'access' in data['data']:
                print_success(f"JWT Access Token received: {data['data']['access'][:50]}...")
                print_success(f"JWT Refresh Token received: {data['data']['refresh'][:50]}...")
                return data
        else:
            print_error(f"OTP verification failed with status {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error verifying OTP: {e}")
        return None

def test_failed_otp_attempts(email: str):
    """Test failed OTP verification and lockout"""
    print_header("TEST 5: Failed OTP Attempts & Lockout (5 attempts in 15 minutes)")
    print_info(f"Making 6 failed OTP attempts for {email}...")
    
    url = f"{BASE_URL}/auth/otp/verify/"
    payload = {"email": email, "otp": "000000"}
    
    for i in range(6):
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 400:
                print_warning(f"Attempt {i+1}/6: Invalid OTP (400)")
            elif response.status_code == 423:
                data = response.json()
                unlock_eta = data.get('data', {}).get('unlock_eta_seconds', 'unknown')
                print_error(f"Attempt {i+1}/6: Account locked (423) - Unlock ETA: {unlock_eta}s")
            else:
                print_warning(f"Attempt {i+1}/6: Status {response.status_code}")
        except Exception as e:
            print_error(f"Attempt {i+1}/6: Error - {e}")
        time.sleep(0.5)

def test_audit_logs(access_token: str):
    """Test audit logs endpoint"""
    print_header("TEST 6: Audit Logs (Authenticated Access)")
    print_info("Fetching audit logs with JWT authentication")
    
    url = f"{BASE_URL}/audit/logs/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response, "Audit Logs Response")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print_success(f"Retrieved {count} audit log entries")
            
            # Test filtering
            print_info("\nTesting audit log filtering...")
            
            # Filter by event
            response = requests.get(f"{url}?event=OTP_REQUESTED", headers=headers)
            if response.status_code == 200:
                filtered = response.json()
                print_success(f"Filter by event: Found {filtered.get('count', 0)} OTP_REQUESTED events")
        else:
            print_error(f"Audit logs request failed with status {response.status_code}")
    except Exception as e:
        print_error(f"Error fetching audit logs: {e}")

def test_pagination(access_token: str):
    """Test audit logs pagination"""
    print_header("TEST 7: Audit Logs Pagination")
    print_info("Testing paginated audit log retrieval")
    
    url = f"{BASE_URL}/audit/logs/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Page 1
        response = requests.get(f"{url}?page=1", headers=headers)
        if response.status_code == 200:
            data = response.json()
            total = data.get('count', 0)
            page_size = len(data.get('results', []))
            print_success(f"Page 1: {page_size} results (Total: {total})")
            
            # Check next page
            if data.get('next'):
                print_info("Next page available")
    except Exception as e:
        print_error(f"Error testing pagination: {e}")

def interactive_demo():
    """Run interactive demo"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════╗")
    print("║   OTP Authentication Service - Interactive Demo        ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # Test connectivity
    print_info("Testing API connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/auth/otp/request/", json={"email": "test@test.com"})
        print_success(f"API is responsive (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API at {BASE_URL}")
        print_error("Make sure docker-compose is running: docker-compose up --build")
        return
    
    # Get test email
    email = input(f"\n{Colors.BOLD}Enter email for testing (default: test@example.com):{Colors.ENDC} ").strip()
    if not email:
        email = "test@example.com"
    
    print_info(f"Using email: {email}")
    
    # Run tests
    test_swagger_ui()
    
    # OTP Request
    otp_response = test_otp_request(email)
    
    # Rate limiting test (use different email to avoid hitting our limit)
    rate_limit_email = f"ratelimit-{int(time.time())}@example.com"
    test_otp_rate_limit(rate_limit_email)
    
    # Failed attempts test (use different email)
    failed_email = f"failed-{int(time.time())}@example.com"
    test_failed_otp_attempts(failed_email)
    
    # OTP Verification (if we got a previous response)
    access_token = None
    if otp_response:
        otp = input(f"\n{Colors.BOLD}Enter the OTP you received (check Celery logs):{Colors.ENDC} ").strip()
        if otp:
            verify_response = test_otp_verify(email, otp)
            if verify_response and 'data' in verify_response:
                access_token = verify_response['data'].get('access')
    
    # Audit logs and pagination tests
    if access_token:
        test_audit_logs(access_token)
        test_pagination(access_token)
    else:
        print_warning("Skipping audit log tests (no valid access token)")
    
    print_header("Demo Complete!")
    print_info(f"Swagger UI: {SWAGGER_URL}")
    print_info(f"API Base URL: {BASE_URL}")
    print_info("Check docker-compose logs for Celery task execution")

if __name__ == "__main__":
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Demo interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
