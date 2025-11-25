# File: skylynx_digital/ui/login_dialog.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QWidget,
)

from skylynx_digital.api_client import login, LoginError


class LoginDialog(QDialog):
    """
    Simple login dialog that talks to the FastAPI backend.

    After exec_():
      - if result() == QDialog.Accepted:
          self.access_token  (str)
          self.company_id    (int)
          self.modules       (list[str])
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Skylynx Digital - Login")
        self.setModal(True)

        self.access_token: str | None = None
        self.company_id: int | None = None
        self.modules: list[str] = []

        # Widgets
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("you@example.com")

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Password")

        self.remember_checkbox = QCheckBox("Remember me")

        self.login_button = QPushButton("Login")
        self.cancel_button = QPushButton("Cancel")

        self.login_button.clicked.connect(self.on_login_clicked)
        self.cancel_button.clicked.connect(self.reject)

        # Layout
        main_layout = QVBoxLayout(self)

        form_layout = QVBoxLayout()
        email_row = QHBoxLayout()
        email_row.addWidget(QLabel("Email:"))
        email_row.addWidget(self.email_edit)

        password_row = QHBoxLayout()
        password_row.addWidget(QLabel("Password:"))
        password_row.addWidget(self.password_edit)

        form_layout.addLayout(email_row)
        form_layout.addLayout(password_row)
        form_layout.addWidget(self.remember_checkbox)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.cancel_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(buttons_layout)

        # For convenience during dev:
        self.email_edit.setText("admin@skylynx.local")
        self.password_edit.setText("ChangeMe123!")

    def on_login_clicked(self) -> None:
        email = self.email_edit.text().strip()
        password = self.password_edit.text()

        if not email or not password:
            QMessageBox.warning(self, "Login", "Please enter both email and password.")
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")

        try:
            token, company_id, modules = login(email, password)
        except LoginError as e:
            QMessageBox.critical(self, "Login failed", str(e))
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")
            return

        # Success
        self.access_token = token
        self.company_id = company_id
        self.modules = modules

        self.accept()
