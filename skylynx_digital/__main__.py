# File: skylynx_digital/__main__.py
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from skylynx_digital.ui.login_dialog import LoginDialog
from skylynx_digital.ui.employees_window import EmployeesWindow


def main() -> int:
    app = QApplication(sys.argv)

    # 1) Show login dialog
    login_dialog = LoginDialog()
    if login_dialog.exec() != LoginDialog.Accepted:
        return 0  # user cancelled

    access_token = login_dialog.access_token
    company_id = login_dialog.company_id
    modules = login_dialog.modules

    print("Logged in as company_id:", company_id)
    print("Modules:", modules)

    # 2) For now, just show Employees window
    win = EmployeesWindow(access_token)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
