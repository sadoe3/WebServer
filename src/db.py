import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT    UNIQUE NOT NULL,
                role       TEXT    NOT NULL DEFAULT 'viewer',
                created_at TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS magic_tokens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                token      TEXT    UNIQUE NOT NULL,
                expires_at TEXT    NOT NULL,
                used       INTEGER NOT NULL DEFAULT 0,
                created_at TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                session_token TEXT    UNIQUE NOT NULL,
                expires_at    TEXT    NOT NULL,
                created_at    TEXT    NOT NULL
            );
        """)
        # Migrate existing DBs that lack the role column
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'viewer'")
        except sqlite3.OperationalError:
            pass  # Column already exists


def seed_admin() -> None:
    """Ensure ADMIN_EMAIL exists as admin role.
    - Empty table: insert admin user.
    - ADMIN_EMAIL already exists with wrong role: promote to admin.
    """
    admin_email = os.getenv("ADMIN_EMAIL", "")
    if not admin_email:
        return
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, role FROM users WHERE email = ?", (admin_email,)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (email, role, created_at) VALUES (?, 'admin', ?)",
                (admin_email, now),
            )
        elif row["role"] != "admin":
            conn.execute(
                "UPDATE users SET role = 'admin' WHERE id = ?", (row["id"],)
            )


# --- User CRUD helpers ---

def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email, role, created_at FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email, role, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, email, role, created_at FROM users ORDER BY created_at"
        ).fetchall()
    return [dict(r) for r in rows]


def add_user(email: str, role: str = "viewer") -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, role, created_at) VALUES (?, ?, ?)",
            (email, role, now),
        )
        row = conn.execute(
            "SELECT id, email, role, created_at FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row)


def update_user_role(user_id: int, role: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))


def delete_user(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM magic_tokens WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


# --- Cleanup ---

def cleanup_expired() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute("DELETE FROM magic_tokens WHERE expires_at < ?", (now,))
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
