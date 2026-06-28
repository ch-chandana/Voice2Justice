import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from models.db import get_db

class UserModel:
    @staticmethod
    def register(full_name: str, email: str, phone: str, password: str) -> int | None:
        """Registers a new user and returns their ID. Returns None if email exists."""
        password_hash = generate_password_hash(password)
        try:
            with get_db() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO users (full_name, email, phone, password_hash)
                    VALUES (?, ?, ?, ?)
                ''', (full_name, email, phone, password_hash))
                conn.commit()
                return c.lastrowid
        except sqlite3.IntegrityError:
            return None  # Email already exists

    @staticmethod
    def authenticate(email: str, password: str) -> dict | None:
        """Authenticates a user and returns their dict representation if successful."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = c.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                return dict(user)
        return None

    @staticmethod
    def get_by_id(user_id: int) -> dict | None:
        """Fetches a user by ID."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id, full_name, email, phone, auth_provider, google_id, profile_picture, created_at FROM users WHERE id = ?", (user_id,))
            user = c.fetchone()
            return dict(user) if user else None

    @staticmethod
    def oauth_login_or_register(email: str, full_name: str, google_id: str, profile_picture: str) -> dict:
        """Handles OAuth login. Links existing account or creates a new one."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = c.fetchone()
            
            if user:
                # Link Google account if not already linked (keep password intact)
                c.execute('''
                    UPDATE users 
                    SET auth_provider = 'google', google_id = ?, profile_picture = ?
                    WHERE id = ?
                ''', (google_id, profile_picture, user['id']))
                conn.commit()
                c.execute("SELECT * FROM users WHERE id = ?", (user['id'],))
                return dict(c.fetchone())
            else:
                # Create new user
                dummy_hash = generate_password_hash("OAUTH_MANAGED_NO_PASSWORD")
                c.execute('''
                    INSERT INTO users (full_name, email, password_hash, auth_provider, google_id, profile_picture)
                    VALUES (?, ?, ?, 'google', ?, ?)
                ''', (full_name, email, dummy_hash, google_id, profile_picture))
                conn.commit()
                user_id = c.lastrowid
                c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                return dict(c.fetchone())

    @staticmethod
    def get_complaints(user_id: int) -> list[dict]:
        """Fetches all complaints submitted by a specific user."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT id, complaint_number, category, status, created_at, priority, fraud_status, review_status
                FROM complaints 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            return [dict(row) for row in c.fetchall()]
