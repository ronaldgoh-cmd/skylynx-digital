# File: skylynx_digital/api_client.py
from typing import Tuple, List
import requests

from .config import API_BASE


class LoginError(Exception):
    """Raised when login fails."""


def login(email: str, password: str) -> Tuple[str, int, List[str]]:
    """
    Call POST /auth/token and return (access_token, company_id, modules).

    Raises LoginError on failure.
    """
    url = API_BASE + "auth/token"
    data = {
        "username": email,   # OAuth2PasswordRequestForm uses 'username'
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


def get_employees(token: str):
    """
    Call GET /employees/ and return the JSON list.
    """
    url = API_BASE + "employees/"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()
