#!/usr/bin/env python3
"""
Test script to demonstrate email configuration functionality.
This script shows how the email configuration system works.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from ui_main import MainUI

def test_email_config():
    """Test the email configuration functionality"""
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = MainUI()
    main_window.show()
    
    print("Application started. Testing email configuration in 3 seconds...")
    
    # Test login and email config after 3 seconds
    def test_email_config_after_delay():
        print("Testing email configuration now...")
        try:
            # Simulate a successful login first
            user_info = {
                'username': 'TestUser',
                'email': 'test@example.com',
                'access_token': 'dummy_token',
                'refresh_token': 'dummy_refresh'
            }
            main_window.on_login_success(user_info)
            
            # Wait a bit then switch to email config tab
            QTimer.singleShot(1000, lambda: switch_to_email_config())
            
        except Exception as e:
            print(f"Error during test: {e}")
    
    def switch_to_email_config():
        try:
            print("Switching to email configuration tab...")
            # Switch to email configuration tab (index 1)
            main_window.tab_widget.setCurrentIndex(1)
            print("Email configuration tab activated!")
            
            # Close app after successful test
            QTimer.singleShot(5000, app.quit)
            
        except Exception as e:
            print(f"Tab switch failed with error: {e}")
            app.quit()
    
    # Start the test
    QTimer.singleShot(3000, test_email_config_after_delay)
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_email_config()
