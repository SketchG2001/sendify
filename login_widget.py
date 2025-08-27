from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from api_client import ApiClient

class LoginWidget(QWidget):
    login_success = pyqtSignal(dict)
    switch_to_signup = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.api_client = ApiClient()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Login to Sendify")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)

        self.signup_button = QPushButton("Don't have an account? Sign Up")
        self.signup_button.setStyleSheet("QPushButton { border: none; color: blue; text-decoration: underline; }")
        self.signup_button.clicked.connect(self.switch_to_signup.emit)

        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both email and password.")
            return

        self.login_button.setEnabled(False)

        self.worker = self.api_client.login(email, password)
        self.worker.success.connect(self.on_login_success)
        self.worker.error.connect(self.on_login_error)
        self.worker.finished.connect(lambda: self.login_button.setEnabled(True))
        self.worker.start()

    def on_login_success(self, data):
        user_info = {
            'username': data.get('user', {}).get('name'),
            'email': data.get('user', {}).get('email'),
            'access_token': data.get('tokens', {}).get('access'),
            'refresh_token': data.get('tokens', {}).get('refresh'),
            'message': data.get('message', 'Login successful')
        }
        
        QMessageBox.information(self, "Success", user_info['message'])
        self.login_success.emit(user_info)

    def on_login_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
