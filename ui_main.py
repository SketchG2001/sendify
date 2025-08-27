# ui_main.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QLabel, QPushButton, QHBoxLayout, QLineEdit, QTabWidget
from PyQt6.QtCore import QTimer, Qt
from login_widget import LoginWidget
from signup_widget import SignupWidget
from email_config_widget import EmailConfigWidget
from api_client import ApiClient

class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sendify")
        self.setGeometry(400, 300, 400, 500)

        self.api_client = ApiClient()
        self.is_logging_out = False
        self.user_info = None  # Store user info for later use

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        self.init_widgets()

        self.show_login()

    def init_widgets(self):
        """Initialize login and signup widgets"""

        self.login_widget = LoginWidget()
        self.login_widget.login_success.connect(self.on_login_success)
        self.login_widget.switch_to_signup.connect(self.show_signup)

        self.signup_widget = SignupWidget()
        self.signup_widget.switch_to_login.connect(self.show_login)

        self.stacked_widget.addWidget(self.login_widget)
        self.stacked_widget.addWidget(self.signup_widget)

    def show_login(self):
        """Switch to login screen"""
        self.stacked_widget.setCurrentWidget(self.login_widget)

    def show_signup(self):
        """Switch to signup screen"""
        self.stacked_widget.setCurrentWidget(self.signup_widget)

    def on_login_success(self, user_info):
        """Called after successful login"""
        try:
            print("Creating welcome screen...")
            
            # Store user info for later use
            self.user_info = user_info
            
            # Clear the stacked widget
            while self.stacked_widget.count() > 0:
                widget = self.stacked_widget.widget(0)
                self.stacked_widget.removeWidget(widget)
                widget.deleteLater()

            self.welcome_widget = QWidget()
            welcome_layout = QVBoxLayout(self.welcome_widget)

            # Header with welcome message and logout
            header_layout = QHBoxLayout()
            user_name = user_info.get('username') or user_info.get('name', 'User')
            welcome_label = QLabel(f"Welcome {user_name} 🎉")
            welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
            
            logout_button = QPushButton("Logout")
            logout_button.clicked.connect(self.logout)
            logout_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; }")
            
            header_layout.addWidget(welcome_label)
            header_layout.addStretch()
            header_layout.addWidget(logout_button)
            
            welcome_layout.addLayout(header_layout)

            # Create tab widget for different functionalities
            self.tab_widget = QTabWidget()
            
            # Dashboard Tab
            dashboard_tab = QWidget()
            dashboard_layout = QVBoxLayout(dashboard_tab)
            
            # Dashboard title
            dashboard_title = QLabel("Dashboard")
            dashboard_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
            dashboard_layout.addWidget(dashboard_title)
            
            # Quick action buttons
            profile_button = QPushButton("Get User Profile")
            profile_button.clicked.connect(self.get_user_profile)
            profile_button.setStyleSheet("QPushButton { background-color: #007bff; color: white; border: none; padding: 10px; margin: 5px; border-radius: 4px; }")
            
            secure_data_button = QPushButton("Get Secure Data")
            secure_data_button.clicked.connect(self.get_secure_data)
            secure_data_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; border: none; padding: 10px; margin: 5px; border-radius: 4px; }")
            
            dashboard_layout.addWidget(profile_button)
            dashboard_layout.addWidget(secure_data_button)
            dashboard_layout.addStretch()
            
            # Add dashboard tab first
            self.tab_widget.addTab(dashboard_tab, "Dashboard")
            
            # Create a placeholder for email configuration tab (lazy loading)
            self.create_email_config_placeholder()
            
            welcome_layout.addWidget(self.tab_widget)
            
            self.stacked_widget.addWidget(self.welcome_widget)
            
            print("Welcome screen created successfully!")
            
        except Exception as e:
            print(f"Error creating welcome screen: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simple welcome screen
            self.create_fallback_welcome_screen(user_info)
    
    def create_email_config_placeholder(self):
        """Create a placeholder for email configuration tab that loads on demand"""
        try:
            # Create a simple placeholder widget
            placeholder_widget = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_widget)
            
            placeholder_label = QLabel("Loading Email Configuration...")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_label.setStyleSheet("font-size: 14px; color: #666; padding: 20px;")
            
            load_button = QPushButton("Load Email Configuration")
            load_button.clicked.connect(self.load_email_config_tab)
            load_button.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            
            placeholder_layout.addWidget(placeholder_label)
            placeholder_layout.addWidget(load_button)
            placeholder_layout.addStretch()
            
            # Add the placeholder tab
            self.tab_widget.addTab(placeholder_widget, "Email Configuration")
            
        except Exception as e:
            print(f"Error creating email config placeholder: {e}")
            # Add a simple tab without email config
            simple_tab = QWidget()
            simple_layout = QVBoxLayout(simple_tab)
            simple_label = QLabel("Email Configuration - Not Available")
            simple_layout.addWidget(simple_label)
            self.tab_widget.addTab(simple_tab, "Email Configuration")
    
    def load_email_config_tab(self):
        """Load the actual email configuration tab when requested"""
        try:
            print("Loading email configuration tab...")
            
            # Check if user_info is available
            if not self.user_info:
                print("No user info available, cannot load email config")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Warning", "User information not available. Please login again.")
                return
            
            # Remove the placeholder tab
            placeholder_index = self.tab_widget.indexOf(self.tab_widget.currentWidget())
            if placeholder_index >= 0:
                try:
                    placeholder_widget = self.tab_widget.widget(placeholder_index)
                    self.tab_widget.removeTab(placeholder_index)
                    placeholder_widget.deleteLater()
                except Exception as e:
                    print(f"Error removing placeholder tab: {e}")
            
            # Create the actual email configuration tab with error handling
            try:
                print("Creating EmailConfigWidget...")
                # Add a small delay to prevent immediate crash and improve stability
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(50, self.create_email_config_widget)
                
            except Exception as email_config_error:
                print(f"Error creating EmailConfigWidget: {email_config_error}")
                import traceback
                traceback.print_exc()
                # Create a fallback tab
                self.create_email_config_fallback_tab()
                
        except Exception as e:
            print(f"Error loading email configuration tab: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error message
            try:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to load email configuration: {str(e)}")
            except Exception as msg_error:
                print(f"Error showing error message: {msg_error}")
            
            # Create fallback tab as last resort
            try:
                self.create_email_config_fallback_tab()
            except Exception as fallback_error:
                print(f"Error creating fallback tab: {fallback_error}")
                # Create a simple tab
                simple_tab = QWidget()
                simple_layout = QVBoxLayout(simple_tab)
                simple_label = QLabel("Email Configuration - Failed to Load")
                simple_layout.addWidget(simple_label)
                self.tab_widget.addTab(simple_tab, "Email Configuration")

    def create_email_config_widget(self):
        """Create the email config widget with proper error handling and delayed execution"""
        try:
            print("Creating EmailConfigWidget with delay...")
            self.email_config_tab = EmailConfigWidget(self.user_info)
            print("EmailConfigWidget created successfully")
            
            # Connect signals with error handling
            try:
                self.email_config_tab.config_updated.connect(self.on_email_config_updated)
                print("Signals connected successfully")
            except Exception as signal_error:
                print(f"Error connecting signals: {signal_error}")
            
            # Add the actual tab
            self.tab_widget.addTab(self.email_config_tab, "Email Configuration")
            print("Tab added successfully")
            
            # Switch to the email configuration tab
            self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
            print("Tab switched successfully")
            
            print("Email configuration tab loaded successfully!")
            
        except Exception as e:
            print(f"Error creating EmailConfigWidget: {e}")
            import traceback
            traceback.print_exc()
            self.create_email_config_fallback_tab()
    
    def create_email_config_fallback_tab(self):
        """Create a fallback email configuration tab if the main one fails"""
        try:
            fallback_tab = QWidget()
            fallback_layout = QVBoxLayout(fallback_tab)
            
            error_label = QLabel("Email Configuration - Error Loading")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("font-size: 14px; color: #dc3545; padding: 20px;")
            
            retry_button = QPushButton("Retry Loading")
            retry_button.clicked.connect(self.load_email_config_tab)
            retry_button.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: #212529;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
            
            fallback_layout.addWidget(error_label)
            fallback_layout.addWidget(retry_button)
            fallback_layout.addStretch()
            
            # Add the fallback tab
            self.tab_widget.addTab(fallback_tab, "Email Configuration")
            
            print("Email configuration fallback tab created")
            
        except Exception as e:
            print(f"Error creating fallback tab: {e}")
            # Last resort - simple message
            simple_tab = QWidget()
            simple_layout = QVBoxLayout(simple_tab)
            simple_label = QLabel("Email Configuration - Unavailable")
            simple_layout.addWidget(simple_label)
            self.tab_widget.addTab(simple_tab, "Email Configuration")
    
    def create_fallback_welcome_screen(self, user_info):
        """Create a simple fallback welcome screen if the main one fails"""
        try:
            print("Creating fallback welcome screen...")
            
            # Clear the stacked widget
            while self.stacked_widget.count() > 0:
                widget = self.stacked_widget.widget(0)
                self.stacked_widget.removeWidget(widget)
                widget.deleteLater()

            self.welcome_widget = QWidget()
            welcome_layout = QVBoxLayout(self.welcome_widget)

            # Simple header
            welcome_label = QLabel(f"Welcome {user_info.get('username', 'User')} 🎉")
            welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
            welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            welcome_layout.addWidget(welcome_label)
            
            # Simple logout button
            logout_button = QPushButton("Logout")
            logout_button.clicked.connect(self.logout)
            logout_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; }")
            welcome_layout.addWidget(logout_button)
            
            welcome_layout.addStretch()
            
            self.stacked_widget.addWidget(self.welcome_widget)
            
            print("Fallback welcome screen created successfully!")
            
        except Exception as e:
            print(f"Error creating fallback welcome screen: {e}")
            # Last resort - just show login again
            self.show_login()

    def on_email_config_updated(self):
        """Handle email configuration updates"""
        print("Email configuration updated, refreshing data...")


    def closeEvent(self, event):
        """Handle application close event"""
        print("Application closing, cleaning up...")
        try:
            if hasattr(self, 'welcome_widget') and self.welcome_widget:
                self.safe_disconnect_widget(self.welcome_widget)

            while self.stacked_widget.count() > 0:
                widget = self.stacked_widget.widget(0)
                self.stacked_widget.removeWidget(widget)
                widget.deleteLater()

            if hasattr(self, 'api_client'):
                self.api_client.logout()
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        event.accept()

    def safe_disconnect_widget(self, widget):
        """Safely disconnect all signals from a widget and its children"""
        if not widget:
            return
            
        try:
            # Disconnect all signals from the widget itself
            widget.disconnect()
        except:
            pass
            
        # Disconnect signals from all child widgets
        for child in widget.findChildren(QPushButton):
            try:
                child.clicked.disconnect()
            except:
                pass
                
        for child in widget.findChildren(QLineEdit):
            try:
                child.textChanged.disconnect()
                child.returnPressed.disconnect()
            except:
                pass

    def logout(self):
        """Logout user and return to login screen"""
        if self.is_logging_out:
            print("Logout already in progress. Ignoring new request.")
            return

        self.is_logging_out = True
        print("Initiating logout process...")

        try:
            # Safely disconnect all signals from the welcome widget to prevent crashes
            if hasattr(self, 'welcome_widget') and self.welcome_widget:
                self.safe_disconnect_widget(self.welcome_widget)
                
                # Remove and delete the welcome widget
                self.stacked_widget.removeWidget(self.welcome_widget)
                self.welcome_widget.deleteLater()
                self.welcome_widget = None
            
            # Clear any existing widgets and reinitialize
            while self.stacked_widget.count() > 0:
                widget = self.stacked_widget.widget(0)
                self.stacked_widget.removeWidget(widget)
                widget.deleteLater()
            
            # Clear user info
            self.user_info = None
            
            # Clear email config tab reference
            if hasattr(self, 'email_config_tab'):
                try:
                    self.email_config_tab.deleteLater()
                except:
                    pass
                self.email_config_tab = None
            
            # Clear tab widget reference
            if hasattr(self, 'tab_widget'):
                try:
                    self.tab_widget.deleteLater()
                except:
                    pass
                self.tab_widget = None
            
        except Exception as e:
            print(f"Error during logout cleanup: {e}")
            import traceback
            traceback.print_exc()
        
        # Use a timer to delay the final cleanup and reinitialization
        # This ensures all widget deletion operations complete
        QTimer.singleShot(100, self._complete_logout)
    
    def _complete_logout(self):
        """Complete the logout process after widget cleanup"""
        try:
            self.init_widgets()
            self.api_client.logout()
            self.show_login()
            
        except Exception as e:
            print(f"Error during logout completion: {e}")
        finally:
            self.is_logging_out = False
            print("Logout process finished.")

    def get_user_profile(self):
        """Example of making a secure API call"""
        worker = self.api_client.get_user_profile()
        if worker:
            worker.success.connect(lambda data: print("User Profile:", data))
            worker.error.connect(lambda error: print("Error getting profile:", error))
            worker.start()
        else:
            print("No valid token available")

    def get_secure_data(self):
        """Example of making a secure API call"""
        worker = self.api_client.get_secure_data()
        if worker:
            worker.success.connect(lambda data: print("Secure Data:", data))
            worker.error.connect(lambda error: print("Error getting secure data:", error))
            worker.start()
        else:
            print("No valid token available")
