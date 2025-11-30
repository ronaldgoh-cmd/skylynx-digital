# File: skylynx_digital/ui/user_settings_dialog.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QDialogButtonBox,
)


class UserSettingsDialog(QDialog):
    """
    Simple dialog to edit time zone and theme for the current user.

    Call with the current values, e.g.:

        dlg = UserSettingsDialog(current_tz, current_theme)
        if dlg.exec() == QDialog.Accepted:
            tz, theme = dlg.values()
    """

    def __init__(self, timezone: str, theme: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("User Settings")

        tz_value = timezone or "Asia/Singapore"
        theme_value = (theme or "light").lower()

        layout = QVBoxLayout(self)

        # Time zone
        layout.addWidget(QLabel("Time zone:"))
        self.timezone_box = QComboBox(self)
        tz_options = [
            "Asia/Singapore",
            "Asia/Kuala_Lumpur",
            "Asia/Bangkok",
            "Asia/Jakarta",
            "UTC",
        ]
        for tz in tz_options:
            self.timezone_box.addItem(tz)
        idx = self.timezone_box.findText(tz_value)
        if idx < 0:
            self.timezone_box.addItem(tz_value)
            idx = self.timezone_box.findText(tz_value)
        self.timezone_box.setCurrentIndex(max(idx, 0))
        layout.addWidget(self.timezone_box)

        # Theme
        layout.addWidget(QLabel("Theme:"))
        self.theme_box = QComboBox(self)
        self.theme_box.addItems(["light", "dark"])
        idx_theme = self.theme_box.findText(theme_value)
        self.theme_box.setCurrentIndex(max(idx_theme, 0))
        layout.addWidget(self.theme_box)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str]:
        """
        Return (timezone, theme)
        """
        return self.timezone_box.currentText(), self.theme_box.currentText()
