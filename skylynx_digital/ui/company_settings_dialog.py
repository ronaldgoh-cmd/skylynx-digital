# File: skylynx_digital/ui/company_settings_dialog.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QTextEdit,
    QHBoxLayout,
    QMessageBox,
    QProgressDialog,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import QCoreApplication, Qt
    # noqa
from PySide6.QtGui import QPixmap

from ..core.database import (
    get_module_db_path,
    wipe_module_database,
    create_backup,
    list_backups,
    restore_backup,
)
from ..core.plugins import discover_modules
from ..api_client import (
    get_company_settings,
    update_company_settings,
    fetch_company_logo,
    upload_company_logo,
)


class CompanySettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Company Settings")

        layout = QVBoxLayout(self)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Company Name")
        self.detail1 = QLineEdit()
        self.detail1.setPlaceholderText("Details Line 1")
        self.detail2 = QLineEdit()
        self.detail2.setPlaceholderText("Details Line 2")
        self.version = QLineEdit()
        self.version.setPlaceholderText("Version")
        self.about = QTextEdit()
        self.about.setPlaceholderText("About text")
        self.logo_path = ""
        self.logo_btn = QPushButton("Upload Logo")
        self.logo_lbl = QLabel("")
        self.update_btn = QPushButton("Update Version")
        self.backup_btn = QPushButton("Back Up Data…")
        self.restore_btn = QPushButton("Restore Data…")
        self.save_btn = QPushButton("Save")
        self.factory_btn = QPushButton("Factory Reset…")

        layout.addWidget(self.name)
        layout.addWidget(self.detail1)
        layout.addWidget(self.detail2)
        layout.addWidget(self.version)
        layout.addWidget(self.about)
        layout.addWidget(self.logo_btn)
        layout.addWidget(self.logo_lbl)

        actions_row = QHBoxLayout()
        actions_row.addWidget(self.update_btn)
        actions_row.addWidget(self.backup_btn)
        actions_row.addWidget(self.restore_btn)
        layout.addLayout(actions_row)

        factory_row = QHBoxLayout()
        factory_row.addStretch(1)
        factory_row.addWidget(self.factory_btn)
        layout.addLayout(factory_row)

        layout.addWidget(self.save_btn)

        self.logo_btn.clicked.connect(self.pick_logo)
        self.update_btn.clicked.connect(self.bump_version)
        self.backup_btn.clicked.connect(self.backup_data)
        self.restore_btn.clicked.connect(self.restore_data)
        self.save_btn.clicked.connect(self.save)
        self.factory_btn.clicked.connect(self.factory_reset)

        self.load_settings()

    # ---------- Online settings ----------

    def load_settings(self):
        """
        Pull company settings + logo from the backend.
        """
        try:
            data = get_company_settings()
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Company Settings",
                f"Unable to load settings from server:\n{exc}",
            )
            data = {}

        self.name.setText(data.get("name") or "")
        self.detail1.setText(data.get("detail1") or "")
        self.detail2.setText(data.get("detail2") or "")
        self.version.setText(data.get("version") or "")
        self.about.setPlainText(data.get("about") or "")

        # Load logo (if any)
        try:
            logo_bytes = fetch_company_logo()
        except Exception:
            logo_bytes = None

        if logo_bytes:
            pm = QPixmap()
            pm.loadFromData(logo_bytes)
            self.logo_lbl.setPixmap(pm.scaledToHeight(64))
        else:
            self.logo_lbl.clear()

        # Reset temporary logo path
        self.logo_path = ""

    def pick_logo(self):
        p, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if p:
            self.logo_path = p
            self.logo_lbl.setText(p)

    def bump_version(self):
        parts = self.version.text().split(".")
        try:
            parts[-1] = str(int(parts[-1]) + 1)
            self.version.setText(".".join(parts))
        except Exception:
            # ignore invalid version formats
            pass

    def save(self):
        """
        Save settings back to the backend (text + optional logo).
        """
        try:
            update_company_settings(
                name=self.name.text().strip(),
                detail1=self.detail1.text().strip(),
                detail2=self.detail2.text().strip(),
                version=self.version.text().strip(),
                about=self.about.toPlainText(),
            )

            if self.logo_path:
                upload_company_logo(self.logo_path)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Company Settings",
                f"Failed to save settings:\n{exc}",
            )
            return

        # Reload from server to reflect the actual stored values / logo
        self.load_settings()
        self.accept()

    # ---------- Backup / restore remain local to this workstation ----------

    def backup_data(self):
        from datetime import datetime

        progress = QProgressDialog("Preparing backup…", None, 0, 1, self)
        progress.setWindowTitle("Database Backup")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        def progress_callback(current: int, total: int, message: str) -> None:
            progress.setMaximum(max(total, 1))
            progress.setValue(current)
            progress.setLabelText(message)
            QCoreApplication.processEvents()

        try:
            metadata = create_backup(progress_callback)
        except Exception as exc:
            progress.cancel()
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"An error occurred while backing up the databases:\n{exc}",
            )
            return
        finally:
            progress.setValue(progress.maximum())
            progress.close()

        created_at = metadata.get("created_at")
        display_time = ""
        if created_at:
            try:
                display_time = datetime.fromisoformat(created_at).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except Exception:
                display_time = created_at
        QMessageBox.information(
            self,
            "Backup Complete",
            "Database backup was created successfully."
            + (f"\nTimestamp: {display_time}" if display_time else ""),
        )

    def restore_data(self):
        from datetime import datetime

        backups = list_backups()
        if not backups:
            QMessageBox.information(self, "Restore", "No backups are currently available.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Restore from Backup")
        v = QVBoxLayout(dialog)

        info = QLabel("Select a backup to restore. Current data will be replaced.")
        info.setWordWrap(True)
        v.addWidget(info)

        lw = QListWidget()
        for meta in backups:
            created_at = meta.get("created_at")
            stamp = "Unknown"
            if created_at:
                try:
                    stamp = datetime.fromisoformat(created_at).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except Exception:
                    stamp = created_at
            item = QListWidgetItem(f"{stamp} — {meta.get('id')}", lw)
            item.setData(Qt.UserRole, meta)
        v.addWidget(lw)

        btns = QHBoxLayout()
        restore_btn = QPushButton("Restore")
        cancel_btn = QPushButton("Cancel")
        btns.addStretch(1)
        btns.addWidget(restore_btn)
        btns.addWidget(cancel_btn)
        v.addLayout(btns)

        def do_restore():
            item = lw.currentItem()
            if not item:
                QMessageBox.information(dialog, "Restore", "Select a backup first.")
                return
            meta = item.data(Qt.UserRole) or {}
            backup_id = meta.get("id")
            if not backup_id:
                QMessageBox.warning(
                    dialog,
                    "Restore",
                    "Selected backup is missing required information.",
                )
                return
            if (
                QMessageBox.question(
                    dialog,
                    "Confirm Restore",
                    "Restoring from this backup will replace the current databases. Continue?",
                )
                != QMessageBox.Yes
            ):
                return

            progress = QProgressDialog("Preparing restore…", None, 0, 1, self)
            progress.setWindowTitle("Restore Databases")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)

            def progress_callback(current: int, total: int, message: str) -> None:
                progress.setMaximum(max(total, 1))
                progress.setValue(current)
                progress.setLabelText(message)
                QCoreApplication.processEvents()

            try:
                restore_backup(str(backup_id), progress_callback)
            except Exception as exc:
                progress.cancel()
                QMessageBox.critical(
                    self,
                    "Restore Failed",
                    f"Unable to restore the backup:\n{exc}",
                )
                return
            finally:
                progress.setValue(progress.maximum())
                progress.close()

            QMessageBox.information(
                self,
                "Restore Complete",
                "The databases have been restored successfully.",
            )
            dialog.accept()
            self.load_settings()

        restore_btn.clicked.connect(do_restore)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def factory_reset(self):
        if (
            QMessageBox.warning(
                self,
                "Factory Reset",
                "Please close all open module tabs and widgets before wiping the databases to "
                "release any active connections. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        module_entries: list[tuple[str, str, str]] = []
        for info, module in discover_modules():
            module_path = getattr(module.__class__, "__module__", "")
            parts = module_path.split(".")
            key = ""
            if "modules" in parts:
                idx = parts.index("modules")
                if idx + 1 < len(parts):
                    key = parts[idx + 1]
            if not key or key == "account_management":
                continue
            path = get_module_db_path(key)
            name = info.get("name") or key.replace("_", " ").title()
            suffix = "" if path.exists() else " — no data file found"
            module_entries.append((f"{name} ({path.name}){suffix}", key, str(path)))

        if not module_entries:
            QMessageBox.information(
                self,
                "Factory Reset",
                "No module databases are available to wipe.",
            )
            return

        d = QDialog(self)
        d.setWindowTitle("Factory Reset")
        v = QVBoxLayout(d)

        info_lbl = QLabel(
            "Select the module databases to delete. Account data is preserved."
        )
        info_lbl.setWordWrap(True)
        v.addWidget(info_lbl)

        lw = QListWidget()
        for label, key, path in module_entries:
            item = QListWidgetItem(label, lw)
            item.setData(Qt.UserRole, {"key": key, "path": path})
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
        v.addWidget(lw)

        run = QPushButton("Wipe Selected")
        v.addWidget(run)

        def wipe():
            checked_items = [
                lw.item(i)
                for i in range(lw.count())
                if lw.item(i).checkState() == Qt.Checked
            ]
            if not checked_items:
                QMessageBox.information(
                    d,
                    "Factory Reset",
                    "Select at least one module database to wipe.",
                )
                return
            summary = "\n".join(it.text() for it in checked_items)
            if (
                QMessageBox.question(
                    d,
                    "Confirm Wipe",
                    f"Delete the following module database(s)?\n\n{summary}",
                )
                != QMessageBox.Yes
            ):
                return
            for it in checked_items:
                data = it.data(Qt.UserRole) or {}
                key = data.get("key")
                if key:
                    wipe_module_database(key)
            QMessageBox.information(
                d,
                "Factory Reset",
                "Selected module databases have been wiped.",
            )
            d.accept()

        run.clicked.connect(wipe)
        d.exec()
