import uuid
from datetime import datetime, timezone, timedelta
from src.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expire_iso(minutes: int = 0, days: int = 0) -> str:
    delta = timedelta(minutes=minutes, days=days)
    return (datetime.now(timezone.utc) + delta).isoformat()


def create_magic_token(email: str, expire_minutes: int = 15) -> str:
    """Upsert user, create a magic token, return the token string."""
    token = str(uuid.uuid4())
    now = _now_iso()
    expires_at = _expire_iso(minutes=expire_minutes)

    with get_connection() as conn:
        # Upsert user
        conn.execute(
            "INSERT INTO users (email, created_at) VALUES (?, ?)"
            " ON CONFLICT(email) DO NOTHING",
            (email, now),
        )
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()

        conn.execute(
            "INSERT INTO magic_tokens (user_id, token, expires_at, used, created_at)"
            " VALUES (?, ?, ?, 0, ?)",
            (user["id"], token, expires_at, now),
        )

    return token


def verify_magic_token(token: str, session_expire_days: int = 7) -> str | None:
    """Validate token, mark used, create session. Returns session_token or None."""
    now = _now_iso()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, user_id FROM magic_tokens"
            " WHERE token = ? AND used = 0 AND expires_at > ?",
            (token, now),
        ).fetchone()

        if row is None:
            return None

        # Mark token as used
        conn.execute(
            "UPDATE magic_tokens SET used = 1 WHERE id = ?", (row["id"],)
        )

        # Create session
        session_token = str(uuid.uuid4())
        expires_at = _expire_iso(days=session_expire_days)
        conn.execute(
            "INSERT INTO sessions (user_id, session_token, expires_at, created_at)"
            " VALUES (?, ?, ?, ?)",
            (row["user_id"], session_token, expires_at, now),
        )

    return session_token


def get_session_user(session_token: str) -> dict | None:
    """Return user row for a valid (non-expired) session token, or None."""
    now = _now_iso()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT u.id, u.email FROM users u"
            " JOIN sessions s ON s.user_id = u.id"
            " WHERE s.session_token = ? AND s.expires_at > ?",
            (session_token, now),
        ).fetchone()

    return dict(row) if row else None


def delete_session(session_token: str) -> None:
    """Remove session (logout)."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE session_token = ?", (session_token,)
        )
