"""
Employee repository – thin wrapper that lets the Qt UI call simple
functions while the real work is done via the HTTP backend.
"""

from typing import Any, Dict, List
import asyncio

from skylynx_digital.services.api_client import APIClient, AuthError, load_default_credentials
from skylynx_digital.services.employees_service import (
    fetch_all_employees,
    create_employee,
)


def _ensure_authenticated() -> None:
    """
    Make sure the shared API client has a token before the UI calls API helpers.

    Priority for credentials:
    1. Environment variables (SKYLYNX_API_TOKEN or SKYLYNX_API_USERNAME /
       SKYLYNX_API_PASSWORD / SKYLYNX_API_ACCOUNT_ID). Legacy skylynx_* values
       are still read for compatibility.
    2. skylynx_digital/config.json values (api_access_token OR api_username /
       api_password / api_account_id)
    """

    client = APIClient.get()
    if client.has_token():
        return

    creds = load_default_credentials()

    if creds.get("access_token"):
        client.set_token(creds["access_token"] or "", expires_at=creds.get("expires_at"))
        return

    # Fall back to performing a login using stored credentials
    missing = [k for k in ("username", "password", "account_id") if not creds.get(k)]
    if missing:
        raise AuthError(
            "Missing API credentials. Set environment variables (SKYLYNX_API_USERNAME/"
            "PASSWORD/ACCOUNT_ID or SKYLYNX_API_TOKEN; skylynx_* also works) or fill "
            "api_username/api_password/api_account_id in skylynx_digital/config.json."
        )

    asyncio.run(
        client.login(
            username=creds["username"] or "",
            password=creds["password"] or "",
            account_id=creds["account_id"] or "",
        )
    )


def get_all_employees() -> List[Dict[str, Any]]:
    """
    Return a list of employees from the backend API.

    Qt code can call this synchronously.
    """
    _ensure_authenticated()
    return asyncio.run(fetch_all_employees())


def add_employee(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new employee via the backend API.

    'payload' must match the backend EmployeeCreate schema.
    """
    _ensure_authenticated()
    return asyncio.run(create_employee(payload))
