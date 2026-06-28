import sqlite3
import os
from config import DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_number TEXT UNIQUE,
                user_name   TEXT DEFAULT 'Anonymous',
                text        TEXT NOT NULL,
                type        TEXT NOT NULL,
                category    TEXT,
                confidence_score REAL,
                department  TEXT,
                priority    TEXT,
                sla         TEXT,
                summary     TEXT,
                sections    TEXT,
                submitted_to TEXT,
                location    TEXT,
                status      TEXT DEFAULT 'Received',
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Migrations for existing databases
        migrations = [
            "ALTER TABLE complaints ADD COLUMN complaint_number TEXT",
            "ALTER TABLE complaints ADD COLUMN user_name TEXT DEFAULT 'Anonymous'",
            "ALTER TABLE complaints ADD COLUMN confidence_score REAL",
            "ALTER TABLE complaints ADD COLUMN updated_at TIMESTAMP"
        ]
        
        for migration in migrations:
            try:
                c.execute(migration)
            except sqlite3.OperationalError as e:
                pass  # Column already exists
                
        # Backfill updated_at for older records
        c.execute("UPDATE complaints SET updated_at = created_at WHERE updated_at IS NULL")
        
        # Backfill complaint numbers for older records
        c.execute("SELECT id, created_at FROM complaints WHERE complaint_number IS NULL")
        rows = c.fetchall()
        for row in rows:
            # Safely handle missing created_at fields in older versions
            year = str(row['created_at'])[:4] if row['created_at'] else "2026"
            c_num = f"VJ-{year}-{row['id']:04d}"
            c.execute("UPDATE complaints SET complaint_number = ? WHERE id = ?", (c_num, row['id']))

        # Step 11: Add user and fraud detection fields to complaints
        new_columns = [
            "ALTER TABLE complaints ADD COLUMN user_id INTEGER",
            "ALTER TABLE complaints ADD COLUMN verification_status TEXT DEFAULT 'Unverified'",
            "ALTER TABLE complaints ADD COLUMN submitted_ip TEXT",
            "ALTER TABLE complaints ADD COLUMN fraud_score REAL DEFAULT 0.0",
            "ALTER TABLE complaints ADD COLUMN fraud_status TEXT DEFAULT 'Clean'",
            "ALTER TABLE complaints ADD COLUMN review_status TEXT DEFAULT 'Pending'",
            "ALTER TABLE complaints ADD COLUMN guest_name TEXT",
            "ALTER TABLE complaints ADD COLUMN guest_email TEXT",
            "ALTER TABLE complaints ADD COLUMN guest_phone TEXT",
            "ALTER TABLE complaints ADD COLUMN user_type TEXT"
        ]
        for col_migration in new_columns:
            try:
                c.execute(col_migration)
            except sqlite3.OperationalError:
                pass  # Column already exists
                
        # Backfill old records as Legacy
        c.execute("UPDATE complaints SET user_type = 'Legacy', verification_status = 'Legacy' WHERE user_type IS NULL")

        # Create Indexes
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_complaint_number ON complaints(complaint_number)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_status ON complaints(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_category ON complaints(category)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON complaints(created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON complaints(user_id)")
        
        # User Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password_hash TEXT NOT NULL,
                auth_provider TEXT DEFAULT 'local',
                google_id TEXT,
                profile_picture TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User Table Migrations (for existing data)
        user_migrations = [
            "ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local'",
            "ALTER TABLE users ADD COLUMN google_id TEXT",
            "ALTER TABLE users ADD COLUMN profile_picture TEXT"
        ]
        for migration in user_migrations:
            try:
                c.execute(migration)
            except sqlite3.OperationalError:
                pass  # Column already exists
        
        # Admin Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Seed default admin if none exists
        c.execute("SELECT COUNT(*) FROM admins")
        if c.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            default_hash = generate_password_hash('admin123')
            c.execute("INSERT INTO admins (username, password_hash, role) VALUES (?, ?, ?)", 
                      ('admin', default_hash, 'super_admin'))
        
        conn.commit()
