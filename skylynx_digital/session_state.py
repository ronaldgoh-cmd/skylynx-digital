# File: skylynx_digital/session_state.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Session:
    access_token: str
    company_id: int
    modules: List[str]
    email: Optional[str] = None


_current_session: Optional[Session] = None


def set_session(
    access_token: str,
    company_id: int,
    modules: List[str],
    email: Optional[str] = None,
) -> None:
    """
    Store the current logged-in session in memory.
    """
    global _current_session
    _current_session = Session(
        access_token=access_token,
        company_id=company_id,
        modules=list(modules) if modules is not None else [],
        email=email,
    )


def get_session() -> Optional[Session]:
    """
    Return the current session, or None if not logged in.
    """
    return _current_session


def clear_session() -> None:
    """
    Clear any active session (e.g. on logout).
    """
    global _current_session
    _current_session = None
