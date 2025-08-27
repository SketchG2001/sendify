from config import BASE_URL
import requests
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime, timedelta

class ApiWorker(QThread):
    success = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()  # Add finished signal for proper cleanup

    def __init__(self, endpoint, data, headers=None, method="POST"):
        super().__init__()
        self.endpoint = endpoint
        self.data = data
        self.headers = headers or {}
        self.method = method
        

    def run(self):
        try:
            if self.method == "POST":
                response = requests.post(self.endpoint, json=self.data, headers=self.headers, timeout=10)
            elif self.method == "GET":
                response = requests.get(self.endpoint, headers=self.headers, timeout=10)
            elif self.method == "PUT":
                response = requests.put(self.endpoint, json=self.data, headers=self.headers, timeout=10)
            elif self.method == "DELETE":
                response = requests.delete(self.endpoint, headers=self.headers, timeout=10)
            
            if response.status_code in (200, 201):
                self.success.emit(response.json())
            else:
                self.error.emit(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()  # Always emit finished signal for cleanup


class TokenManager:
    """Manages JWT token storage and refresh"""
    
    def __init__(self):
        self.tokens_file = "tokens.json"
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.load_tokens()
    
    def load_tokens(self):
        """Load tokens from file"""
        try:
            if os.path.exists(self.tokens_file):
                print(f"Loading tokens from {self.tokens_file}")
                with open(self.tokens_file, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    
                    # Parse the token_expiry string back to datetime object
                    expiry_str = data.get('token_expiry')
                    if expiry_str:
                        try:
                            self.token_expiry = datetime.fromisoformat(expiry_str)
                            print(f"Successfully parsed token expiry: {self.token_expiry}")
                        except ValueError:
                            # If the format is different, try parsing as timestamp
                            try:
                                self.token_expiry = datetime.fromtimestamp(float(expiry_str))
                                print(f"Successfully parsed token expiry from timestamp: {self.token_expiry}")
                            except (ValueError, TypeError):
                                self.token_expiry = None
                                print("Warning: Could not parse token expiry date")
                    else:
                        self.token_expiry = None
                        print("No token expiry found in file")
                
                print(f"Loaded tokens - Access: {'Yes' if self.access_token else 'No'}, Refresh: {'Yes' if self.refresh_token else 'No'}, Expiry: {self.token_expiry}")
            else:
                print(f"Tokens file {self.tokens_file} does not exist")
        except Exception as e:
            print(f"Error loading tokens: {e}")
            # Reset tokens if loading fails
            self.access_token = None
            self.refresh_token = None
            self.token_expiry = None
    
    def save_tokens(self):
        """Save tokens to file"""
        try:
            data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None
            }
            with open(self.tokens_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving tokens: {e}")
    
    def set_tokens(self, access_token, refresh_token, expires_in=3600):
        """Set new tokens"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
        self.save_tokens()
    
    def clear_tokens(self):
        """Clear all tokens"""
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        if os.path.exists(self.tokens_file):
            os.remove(self.tokens_file)
    
    def is_token_valid(self):
        """Check if access token is still valid"""
        if not self.access_token:
            print("Debug: No access token found")
            return False
        
        if not self.token_expiry:
            print("Debug: No token expiry found")
            return False
        
        try:
            current_time = datetime.now()
            is_valid = current_time < self.token_expiry
            print(f"Debug: Token validation - Current: {current_time}, Expiry: {self.token_expiry}, Valid: {is_valid}")
            return is_valid
        except Exception as e:
            print(f"Error validating token: {e}")
            return False
    
    def get_auth_header(self):
        """Get authorization header with access token"""
        if self.is_token_valid():
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}


class ApiClient(QObject):
    API_BASE_URL = BASE_URL

    def __init__(self):
        super().__init__()
        self.token_manager = TokenManager()

    def login(self, email, password):
        """Login and store JWT tokens"""
        
        endpoint = f"{self.API_BASE_URL}/api/auth/login/"

        data = {"email": email, "password": password}
        worker = ApiWorker(endpoint, data)
        worker.success.connect(self._handle_login_success)
        return worker

    def signup(self, username, email, password):
        """Signup new user"""
        endpoint = f"{self.API_BASE_URL}/api/auth/signup/"
        data = {"username": username, "email": email, "password": password}
        worker = ApiWorker(endpoint, data)
        return worker

    def _handle_login_success(self, response_data):
        """Handle successful login and store tokens"""
        # Extract tokens from the specific Django backend response format
        tokens = response_data.get('tokens', {})
        access_token = tokens.get('access')
        refresh_token = tokens.get('refresh')
        
        # Extract user info
        user_info = response_data.get('user', {})
        
        if access_token and refresh_token:
            # Set tokens with default expiry (adjust if your backend provides expires_in)
            self.token_manager.set_tokens(access_token, refresh_token, 3600)
            print(f"Login successful for user: {user_info.get('name', 'Unknown')}")
        else:
            print("Warning: No tokens found in login response")
            print(f"Response data: {response_data}")

    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.token_manager.refresh_token:
            return None
        
        endpoint = self.API_BASE_URL + "/token/refresh/"
        data = {"refresh": self.token_manager.refresh_token}
        worker = ApiWorker(endpoint, data)
        worker.success.connect(self._handle_refresh_success)
        worker.error.connect(self._handle_refresh_error)
        return worker

    def _handle_refresh_success(self, response_data):
        """Handle successful token refresh"""
        # Handle Django backend refresh response format
        access_token = response_data.get('access')
        if access_token:
            self.token_manager.set_tokens(access_token, self.token_manager.refresh_token)
            print("Token refreshed successfully")
        else:
            print("Warning: No access token in refresh response")
            print(f"Refresh response: {response_data}")

    def _handle_refresh_error(self, error):
        """Handle token refresh error - clear tokens"""
        print(f"Token refresh failed: {error}")
        self.token_manager.clear_tokens()

    def logout(self):
        """Logout and clear tokens"""
        try:
            if self.token_manager.refresh_token:
                # Optionally call backend logout endpoint
                endpoint = self.API_BASE_URL + "api/auth/logout/"
                data = {"refresh": self.token_manager.refresh_token}
                worker = ApiWorker(endpoint, data)
                # Don't connect signals to avoid potential issues during logout
                worker.start()
                # Give it a moment to complete, but don't wait indefinitely
                worker.wait(2000)  # Wait max 2 seconds
        except Exception as e:
            print(f"Logout API call failed: {e}")
        finally:
            # Always clear tokens regardless of API call success
            self.token_manager.clear_tokens()

    def make_authenticated_request(self, endpoint, data=None, method="GET"):
        """Make authenticated API request with automatic token refresh"""
        
        if not self.token_manager.is_token_valid():
            # Try to refresh token first
            refresh_worker = self.refresh_access_token()
            if refresh_worker:
                # For simplicity, we'll just return an error
                # In a real app, you'd want to queue the request and retry after refresh
                return None
        
        headers = self.token_manager.get_auth_header()
        full_endpoint = self.API_BASE_URL + endpoint
        
        worker = ApiWorker(full_endpoint, data, headers, method)
        return worker

    # Example secure API methods
    def get_user_profile(self):
        """Get user profile (example of secure API call)"""
        return self.make_authenticated_request("user/profile/", method="GET")

    def update_user_profile(self, profile_data):
        """Update user profile (example of secure API call)"""
        return self.make_authenticated_request("user/profile/", profile_data, method="PUT")

    def get_secure_data(self):
        """Get secure data (example of secure API call)"""
        return self.make_authenticated_request("secure/data/", method="GET")

    # Email Configuration API methods
    def get_email_configurations(self):
        """Get all email configurations for the current user"""
        
        return self.make_authenticated_request("/api/email/configurations/", method="GET")
    
    def get_email_configuration(self, config_id):
        """Get a specific email configuration by ID"""
        return self.make_authenticated_request(f"/api/email/configurations/{config_id}/", method="GET")
    
    def create_email_configuration(self, email, app_password, is_active=True):
        """Create a new email configuration"""
        
        data = {
            "email": email,
            "app_password": app_password,
            "is_active": is_active
        }
        return self.make_authenticated_request("/api/email/configurations/", data, method="POST")
    
    def update_email_configuration(self, config_id, email, app_password, is_active=True):
        """Update an existing email configuration"""
        data = {
            "email": email,
            "app_password": app_password,
            "is_active": is_active
        }
        return self.make_authenticated_request(f"/api/email/configurations/{config_id}/", data, method="PUT")
    
    def delete_email_configuration(self, config_id):
        """Delete an email configuration"""
        return self.make_authenticated_request(f"/api/email/configurations/{config_id}/", method="DELETE")
    
    def use_email_configuration(self, config_id):
        """Activate/use a specific email configuration"""
        data = {
            "is_active": True
        }
        
        return self.make_authenticated_request(f"/api/email/configurations/{config_id}/",data=data, method="PUT")
