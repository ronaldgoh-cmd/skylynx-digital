# File: skylynx_digital/api_client.py
from __future__ import annotations

from typing import Tuple, List, Optional, Dict, Any

import requests

from .config import API_BASE
from .session_state import get_session


class LoginError(Exception):
    """Raised when login fails."""


def _auth_headers(explicit_token: Optional[str] = None) -> Dict[str, str]:
    """
    Build Authorization header from either an explicit token or the
    access token in the current session_state.
    """
    token = explicit_token
    if token is None:
        session = get_session()
        if session is None or not session.access_token:
            raise RuntimeError("No active session; please login first.")
        token = session.access_token
    return {"Authorization": f"Bearer {token}"}


def login(email: str, password: str) -> Tuple[str, int, List[str]]:
    """
    Call POST /auth/token and return (access_token, company_id, modules).

    Raises LoginError on failure.
    """
    url = API_BASE.rstrip("/") + "/auth/token"
    data = {
        "username": email,  # OAuth2PasswordRequestForm uses 'username'
        "password": password,
    }

    resp = requests.post(url, data=data, timeout=10)

    if resp.status_code != 200:
        # Try to get detail message if any
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise LoginError(f"Login failed: {detail}")

    payload = resp.json()
    token = payload["access_token"]
    company_id = payload["company_id"]
    modules = payload.get("modules", [])

    return token, company_id, modules


# ---------- Employees ----------


def get_employees(token: Optional[str] = None) -> Any:
    """
    Call GET /employees/ and return the JSON list.

    If 'token' is not provided, it will use the access_token from the
    current session_state.
    """
    headers = _auth_headers(token)
    url = API_BASE.rstrip("/") + "/employees/"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ---------- Company settings (header etc.) ----------


def get_company_settings(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch company settings for the current user's company.
    """
    headers = _auth_headers(token)
    url = API_BASE.rstrip("/") + "/company/settings"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def update_company_settings(
    name: Optional[str],
    detail1: Optional[str],
    detail2: Optional[str],
    version: Optional[str],
    about: Optional[str],
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update company settings text fields.
    """
    headers = _auth_headers(token)
    url = API_BASE.rstrip("/") + "/company/settings"
    payload: Dict[str, Any] = {
        "name": name,
        "detail1": detail1,
        "detail2": detail2,
        "version": version,
        "about": about,
    }
    resp = requests.put(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_company_logo(token: Optional[str] = None) -> Optional[bytes]:
    """
    Download the company logo. Returns None if no logo is set.
    """
    headers = _auth_headers(token)
    url = API_BASE.rstrip("/") + "/company/logo"
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.content


def upload_company_logo(file_path: str, token: Optional[str] = None) -> None:
    """
    Upload / replace the company logo.
    """
    headers = _auth_headers(token)
    url = API_BASE.rstrip("/") + "/company/logo"
    with open(file_path, "rb") as f:
        files = {"file": f}
        resp = requests.post(url, headers=headers, files=files, timeout=30)
    resp.raise_for_status()


# ---------- User settings (timezone / theme) ----------


def get_user_settings(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch user settings (timezone, theme) for current user.
    """
    headers = _auth_headers(token)
    url = API_BASE.rstrip("/") + "/user/settings/me"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def update_user_settings(
    timezone: str,
    theme: str,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update user settings (timezone, theme) for current user.
    """
    headers = _auth_headers(token)
    url = API_BASE.rstrip("/") + "/user/settings/me"
    payload = {"timezone": timezone, "theme": theme}
    resp = requests.put(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()
