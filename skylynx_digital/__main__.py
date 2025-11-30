from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from skylynx_digital.ui.login_dialog import LoginDialog
from skylynx_digital.ui.main_window import MainWindow
from skylynx_digital.session_state import set_session


def main() -> int:
    app = QApplication(sys.argv)

    # 1) Show cloud login dialog
    dlg = LoginDialog()
    if dlg.exec() != LoginDialog.Accepted:
        return 0

    # 2) Store session for the rest of the app
    set_session(dlg.access_token, dlg.company_id, dlg.modules)

    # 3) Show your full ERP main window (same frame of work as before)
    win = MainWindow()
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
