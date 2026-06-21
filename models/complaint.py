import sqlite3
from datetime import datetime
from models.db import get_db

class ComplaintModel:
    @staticmethod
    def create(data: dict) -> int:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO complaints (
                    user_name, text, type, category, confidence_score,
                    department, priority, sla, summary, sections, submitted_to, location
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('user_name', 'Anonymous'),
                data['text'],
                data['type'],
                data['category'],
                data.get('confidence_score', 0.0),
                data['department'],
                data['priority'],
                data['sla'],
                data['summary'],
                data['sections'],
                data['submitted_to'],
                data['location']
            ))
            comp_id = c.lastrowid
            
            # Generate and assign the unique VJ complaint number
            year = datetime.now().strftime("%Y")
            c_num = f"VJ-{year}-{comp_id:04d}"
            c.execute("UPDATE complaints SET complaint_number = ? WHERE id = ?", (c_num, comp_id))
            
            conn.commit()
            return comp_id

    @staticmethod
    def get(complaint_id: int) -> dict | None:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
            row = c.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_status(complaint_id: int, status: str) -> bool:
        with get_db() as conn:
            c = conn.cursor()
            updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute('''
                UPDATE complaints 
                SET status = ?, updated_at = ?
                WHERE id = ?
            ''', (status, updated_at, complaint_id))
            conn.commit()
            return c.rowcount > 0

    @staticmethod
    def delete(complaint_id: int) -> bool:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
            conn.commit()
            return c.rowcount > 0

    @staticmethod
    def list_all() -> list[dict]:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM complaints ORDER BY created_at DESC")
            return [dict(row) for row in c.fetchall()]

    # ── Analytics & Dashboard Queries ──────────────────────────────────────

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Returns total, open, and closed complaint counts using SQL aggregation."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('Received', 'Under Review', 'Investigating', 'In Progress') THEN 1 ELSE 0 END) as open_count,
                    SUM(CASE WHEN status IN ('Resolved', 'Closed', 'Rejected') THEN 1 ELSE 0 END) as closed_count
                FROM complaints
            ''')
            row = c.fetchone()
            return {
                'total': row['total'] or 0,
                'open': row['open_count'] or 0,
                'closed': row['closed_count'] or 0
            }

    @staticmethod
    def get_category_distribution() -> list[dict]:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT category, COUNT(*) as count 
                FROM complaints 
                GROUP BY category 
                ORDER BY count DESC
            ''')
            return [dict(row) for row in c.fetchall()]

    @staticmethod
    def get_status_distribution() -> list[dict]:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT status, COUNT(*) as count 
                FROM complaints 
                GROUP BY status 
                ORDER BY count DESC
            ''')
            return [dict(row) for row in c.fetchall()]

    @staticmethod
    def get_monthly_trends() -> list[dict]:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
                FROM complaints 
                GROUP BY month 
                ORDER BY month ASC
            ''')
            return [dict(row) for row in c.fetchall()]

    @staticmethod
    def get_top_categories(limit: int = 5) -> list[dict]:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT category, COUNT(*) as count 
                FROM complaints 
                GROUP BY category 
                ORDER BY count DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in c.fetchall()]

    @staticmethod
    def get_recent_complaints(limit: int = 10) -> list[dict]:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT id, complaint_number, user_name, category, status, created_at 
                FROM complaints 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in c.fetchall()]
