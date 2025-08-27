#!/usr/bin/env python3
"""
Test script to verify logout functionality works without crashing.
Run this after implementing the fixes to test the logout process.
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui_main import MainUI

def test_logout():
    """Test the logout functionality"""
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = MainUI()
    main_window.show()
    
    print("Application started. Testing logout in 3 seconds...")
    
    # Test logout after 3 seconds
    def test_logout_after_delay():
        print("Testing logout now...")
        try:
            # Simulate a successful login first
            user_info = {
                'username': 'TestUser',
                'email': 'test@example.com',
                'access_token': 'dummy_token',
                'refresh_token': 'dummy_refresh'
            }
            main_window.on_login_success(user_info)
            
            # Wait a bit then test logout
            QTimer.singleShot(1000, lambda: test_logout_call())
            
        except Exception as e:
            print(f"Error during test: {e}")
    
    def test_logout_call():
        try:
            print("Calling logout...")
            main_window.logout()
            print("Logout completed successfully!")
            
            # Close app after successful test
            QTimer.singleShot(2000, app.quit)
            
        except Exception as e:
            print(f"Logout failed with error: {e}")
            app.quit()
    
    # Start the test
    QTimer.singleShot(3000, test_logout_after_delay)
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_logout()
