# File: skylynx_digital/ui/employees_window.py
from __future__ import annotations

from PySide6 import QtWidgets, QtCore

from skylynx_digital.api_client import get_employees


class EmployeesWindow(QtWidgets.QWidget):
    def __init__(self, access_token: str, parent=None) -> None:
        super().__init__(parent)
        self.access_token = access_token

        self.setWindowTitle("Employees - Skylynx Digital")

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Role"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table)

        # Poll every 7 seconds for updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_employees)
        self.timer.start(7000)

        # Initial load
        self.refresh_employees()

    def refresh_employees(self) -> None:
        try:
            employees = get_employees(self.access_token)
        except Exception as e:
            # In production, you may want a toast / status bar instead
            print(f"Error refreshing employees: {e}")
            return

        self.table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(emp.get("id", ""))))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(emp.get("name", "")))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(emp.get("role", "")))
