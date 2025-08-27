from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from api_client import ApiClient


class SignupWidget(QWidget):
    switch_to_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.api_client = ApiClient()

        layout = QVBoxLayout()

        self.label = QLabel("Signup")
        layout.addWidget(self.label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.signup_button = QPushButton("Signup")
        self.signup_button.clicked.connect(self.handle_signup)
        layout.addWidget(self.signup_button)

        self.back_to_login_button = QPushButton("Back to Login")
        self.back_to_login_button.clicked.connect(self.switch_to_login.emit)
        layout.addWidget(self.back_to_login_button)

        self.setLayout(layout)

    def handle_signup(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()

        if not username or not password or not email:
            QMessageBox.warning(self, "Error", "All fields are required")
            return

        self.signup_button.setEnabled(False)

        # use centralized API client
        self.worker = self.api_client.signup(username, email, password)
        self.worker.success.connect(self.on_signup_success)
        self.worker.error.connect(self.on_signup_error)
        self.worker.finished.connect(lambda: self.signup_button.setEnabled(True))
        self.worker.start()

    def on_signup_success(self, data):
        QMessageBox.information(self, "Success", "Signup successful!")
        self.switch_to_login.emit()

    def on_signup_error(self, error_message):
        QMessageBox.warning(self, "Failed", f"Signup failed: {error_message}")
