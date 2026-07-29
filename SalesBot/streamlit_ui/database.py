"""
SQLite database manager for Streamlit UI thread/conversation persistence.
"""

import sqlite3
import json
import uuid
import os
import hashlib
import hmac
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import asdict


# Database path
DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "streamlit_threads.db"


def get_connection():
    """Get a database connection."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table (auth)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    )

    # Threads table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS threads (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            persona_json TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """
    )

    # Add persona_json column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE threads ADD COLUMN persona_json TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add user_id column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE threads ADD COLUMN user_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Messages table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            bot_state_json TEXT,
            FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
        )
    """
    )

    # Global settings table (for global persona)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
    )

    # Per-user persona table (persona shared across all threads for that user)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_persona (
            user_id TEXT PRIMARY KEY,
            persona_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """
    )

    conn.commit()
    conn.close()


# ===================== Auth / Users =====================


def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150_000)
    return dk.hex()


def create_user(
    username: str, full_name: str, password: str, email: Optional[str] = None
) -> str:
    user_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    salt = os.urandom(16).hex()
    password_hash = _hash_password(password, salt)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (id, username, full_name, email, password_hash, password_salt, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            username.strip().lower(),
            full_name.strip(),
            (email or "").strip(),
            password_hash,
            salt,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return user_id


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ?", (username.strip().lower(),)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_username(username)
    if not user:
        return None
    expected = user.get("password_hash", "")
    salt = user.get("password_salt", "")
    candidate = _hash_password(password, salt)
    if hmac.compare_digest(expected, candidate):
        return user
    return None


# ===================== Thread Operations =====================


def create_thread(user_id: str, title: str = "New Chat") -> str:
    """Create a new thread and return its ID."""
    thread_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO threads (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (thread_id, user_id, title, now, now),
    )
    conn.commit()
    conn.close()

    return thread_id


def get_all_threads(user_id: str) -> List[Dict[str, Any]]:
    """Get all threads sorted by most recent."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM threads WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    """Get a single thread by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def update_thread_title(thread_id: str, title: str):
    """Update a thread's title."""
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE threads SET title = ?, updated_at = ? WHERE id = ?",
        (title, now, thread_id),
    )
    conn.commit()
    conn.close()


def delete_thread(thread_id: str):
    """Delete a thread and all its messages."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
    cursor.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
    conn.commit()
    conn.close()


def touch_thread(thread_id: str):
    """Update thread's updated_at timestamp."""
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE threads SET updated_at = ? WHERE id = ?", (now, thread_id))
    conn.commit()
    conn.close()


# ===================== Persona Operations =====================


def save_thread_persona(thread_id: str, persona: Dict[str, Any]):
    """Save persona configuration for a thread."""
    now = datetime.now().isoformat()
    persona_json = json.dumps(persona) if persona else None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE threads SET persona_json = ?, updated_at = ? WHERE id = ?",
        (persona_json, now, thread_id),
    )
    conn.commit()
    conn.close()


def get_thread_persona(thread_id: str) -> Optional[Dict[str, Any]]:
    """Get persona configuration for a thread."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT persona_json FROM threads WHERE id = ?", (thread_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row["persona_json"]:
        try:
            return json.loads(row["persona_json"])
        except:
            return None
    return None


def get_most_recent_custom_persona() -> Optional[Dict[str, Any]]:
    """Get the most recent custom persona from any thread."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT persona_json FROM threads 
           WHERE persona_json IS NOT NULL 
           ORDER BY updated_at DESC LIMIT 1"""
    )
    row = cursor.fetchone()
    conn.close()

    if row and row["persona_json"]:
        try:
            return json.loads(row["persona_json"])
        except:
            return None
    return None


# ===================== Global Persona Operations =====================


def save_global_persona(persona: Dict[str, Any]):
    """Save the global persona configuration."""
    now = datetime.now().isoformat()
    persona_json = json.dumps(persona) if persona else None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO global_settings (key, value, updated_at) 
           VALUES ('global_persona', ?, ?)""",
        (persona_json, now),
    )
    conn.commit()
    conn.close()


def get_global_persona() -> Optional[Dict[str, Any]]:
    """Get the global persona configuration."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM global_settings WHERE key = 'global_persona'")
    row = cursor.fetchone()
    conn.close()

    if row and row["value"]:
        try:
            return json.loads(row["value"])
        except:
            return None
    return None


# ===================== User Persona Operations =====================


def save_user_persona(user_id: str, persona: Dict[str, Any]):
    now = datetime.now().isoformat()
    persona_json = json.dumps(persona) if persona else json.dumps({})

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_persona (user_id, persona_json, updated_at) VALUES (?, ?, ?)",
        (user_id, persona_json, now),
    )
    conn.commit()
    conn.close()


def get_user_persona(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT persona_json FROM user_persona WHERE user_id = ?", (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row and row["persona_json"]:
        try:
            return json.loads(row["persona_json"])
        except Exception:
            return None
    return None


# ===================== Message Operations =====================


def add_message(thread_id: str, role: str, content: str, bot_state: Any = None) -> int:
    """Add a message to a thread. Returns message ID."""
    now = datetime.now().isoformat()

    # Convert bot_state to JSON if provided
    bot_state_json = None
    if bot_state is not None:
        try:
            if hasattr(bot_state, "__dataclass_fields__"):
                bot_state_json = json.dumps(asdict(bot_state))
            elif isinstance(bot_state, dict):
                bot_state_json = json.dumps(bot_state)
            else:
                bot_state_json = str(bot_state)
        except Exception as e:
            bot_state_json = json.dumps({"error": str(e)})

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (thread_id, role, content, timestamp, bot_state_json) VALUES (?, ?, ?, ?, ?)",
        (thread_id, role, content, now, bot_state_json),
    )
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Update thread's updated_at
    touch_thread(thread_id)

    return message_id


def get_thread_messages(thread_id: str) -> List[Dict[str, Any]]:
    """Get all messages for a thread."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE thread_id = ? ORDER BY timestamp ASC",
        (thread_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for row in rows:
        msg = dict(row)
        # Parse bot_state_json if present
        if msg.get("bot_state_json"):
            try:
                msg["bot_state"] = json.loads(msg["bot_state_json"])
            except:
                msg["bot_state"] = None
        else:
            msg["bot_state"] = None
        messages.append(msg)

    return messages


def get_last_bot_state(thread_id: str) -> Optional[Dict[str, Any]]:
    """Get the last bot state for a thread."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT bot_state_json FROM messages 
           WHERE thread_id = ? AND bot_state_json IS NOT NULL 
           ORDER BY timestamp DESC LIMIT 1""",
        (thread_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row and row["bot_state_json"]:
        try:
            return json.loads(row["bot_state_json"])
        except:
            return None
    return None


def clear_thread_messages(thread_id: str):
    """Clear all messages in a thread."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
    conn.commit()
    conn.close()


# Initialize database on import
init_db()
