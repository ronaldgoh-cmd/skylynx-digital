from __future__ import annotations

import json
import threading
import time
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal

# Reuse the same config + token logic as the HTTP client
from nexacore_erp.services.api_client import load_default_credentials, _load_base_url

try:
    # Provided by `pip install websocket-client`
    from websocket import WebSocketApp  # type: ignore
except ImportError:  # pragma: no cover
    WebSocketApp = None


class EmployeeRealtimeClient(QObject):
    """
    Background WebSocket client for employee change events.

    It connects to the backend /ws endpoint using the same base URL and
    access token as the HTTP API. When the backend broadcasts an event
    like:

        {"channel": "employees", "action": "created", "data": {...}}

    the `employee_event` signal emits that dict back into the Qt thread.
    """

    # Emitted whenever a message arrives from the backend
    employee_event = Signal(dict)

    # Optional: simple status string ("connecting", "closed", "error: ...")
    connection_state_changed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._thread: Optional[threading.Thread] = None
        self._stop = False
        self._ws_url = self._build_ws_url()

    def _build_ws_url(self) -> str:
        creds = load_default_credentials()
        token = creds.get("access_token")
        if not token:
            raise RuntimeError(
                "No API access token configured for WebSocket. "
                "Set it in config.json or SKYLYNX_API_TOKEN (legacy NEXACORE_API_TOKEN is still read)."
            )

        base = _load_base_url()
        if base.startswith("https://"):
            base_ws = "wss://" + base[len("https://") :]
        elif base.startswith("http://"):
            base_ws = "ws://" + base[len("http://") :]
        else:
            base_ws = "ws://" + base

        # Backend expects: /ws?token=<JWT>
        return f"{base_ws}/ws?token={token}"

    def start(self) -> None:
        """Start the background WebSocket thread (idempotent)."""
        if self._thread is not None or WebSocketApp is None:
            # Either already running, or websocket-client not installed.
            if WebSocketApp is None:
                self.connection_state_changed.emit(
                    "disabled: websocket-client package not installed"
                )
            return

        self._stop = False
        self._thread = threading.Thread(target=self._run_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the background thread to stop on next reconnect."""
        self._stop = True

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _run_forever(self) -> None:
        assert WebSocketApp is not None  # for type checkers

        while not self._stop:
            try:
                self.connection_state_changed.emit("connecting")

                ws = WebSocketApp(
                    self._ws_url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )

                # Blocks until socket closes or errors
                ws.run_forever()
                self.connection_state_changed.emit("closed")
            except Exception as exc:  # pragma: no cover - defensive
                self.connection_state_changed.emit(f"error: {exc}")

            if self._stop:
                break

            # Small delay before reconnect attempt
            time.sleep(5)

    # WebSocket callbacks run in the background thread, but Qt signals are
    # thread-safe and will be delivered back to the GUI event loop.

    def _on_message(self, ws, message: str) -> None:  # type: ignore[override]
        try:
            payload: Dict[str, Any] = json.loads(message)
        except Exception:
            return
        self.employee_event.emit(payload)

    def _on_error(self, ws, error: Any) -> None:  # type: ignore[override]
        self.connection_state_changed.emit(f"error: {error}")

    def _on_close(self, ws, status_code: Any, msg: Any) -> None:  # type: ignore[override]
        self.connection_state_changed.emit("closed")
