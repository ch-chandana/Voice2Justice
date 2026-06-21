from models.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash

class AdminModel:
    @staticmethod
    def authenticate(username, password):
        """Verifies admin credentials and returns the admin record if valid."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM admins WHERE username = ?", (username,))
            admin = c.fetchone()
            
            if admin and check_password_hash(admin['password_hash'], password):
                return dict(admin)
            return None

    @staticmethod
    def get_admin(admin_id):
        """Fetches an admin by ID."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, role, created_at FROM admins WHERE id = ?", (admin_id,))
            admin = c.fetchone()
            return dict(admin) if admin else None

    @staticmethod
    def create_admin(username, password, role='admin'):
        """Creates a new admin with hashed password."""
        hashed = generate_password_hash(password)
        with get_db() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO admins (username, password_hash, role) VALUES (?, ?, ?)",
                      (username, hashed, role))
            conn.commit()
            return c.lastrowid
