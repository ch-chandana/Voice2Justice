import sqlite3
import uuid
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
                    department, priority, sla, summary, sections, submitted_to, location,
                    user_id, verification_status, submitted_ip, fraud_score, fraud_status,
                    guest_name, guest_email, guest_phone, user_type, tracking_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('user_name'),
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
                data['location'],
                data.get('user_id'),
                data.get('verification_status', 'Unverified'),
                data.get('submitted_ip'),
                data.get('fraud_score', 0.0),
                data.get('fraud_status', 'Clean'),
                data.get('guest_name'),
                data.get('guest_email'),
                data.get('guest_phone'),
                data.get('user_type'),
                str(uuid.uuid4())
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
    def get_by_tracking_id(tracking_id: str) -> dict | None:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM complaints WHERE tracking_id = ?", (tracking_id,))
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
    def update_review_status(complaint_id: int, review_status: str) -> bool:
        with get_db() as conn:
            c = conn.cursor()
            updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute('''
                UPDATE complaints 
                SET review_status = ?, updated_at = ?
                WHERE id = ?
            ''', (review_status, updated_at, complaint_id))
            conn.commit()
            return c.rowcount > 0

    # ── Fraud Detection Helpers ──────────────────────────────────────────

    @staticmethod
    def count_recent_by_ip(ip: str, hours: int = 1) -> int:
        if not ip: return 0
        with get_db() as conn:
            c = conn.cursor()
            c.execute(f"SELECT COUNT(*) FROM complaints WHERE submitted_ip = ? AND created_at >= datetime('now', '-{hours} hour')", (ip,))
            return c.fetchone()[0]

    @staticmethod
    def count_recent_by_user(user_id: int, hours: int = 1) -> int:
        if not user_id: return 0
        with get_db() as conn:
            c = conn.cursor()
            c.execute(f"SELECT COUNT(*) FROM complaints WHERE user_id = ? AND created_at >= datetime('now', '-{hours} hour')", (user_id,))
            return c.fetchone()[0]

    @staticmethod
    def check_duplicate_text(text: str) -> bool:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM complaints WHERE text = ?", (text,))
            return c.fetchone()[0] > 0

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
                SELECT c.id, c.complaint_number, 
                       COALESCE(u.full_name, c.guest_name, c.user_name, 'Anonymous') as display_name,
                       COALESCE(u.email, c.guest_email, 'Unknown') as display_email,
                       c.user_type, c.category, c.status, c.created_at,
                       c.fraud_score, c.fraud_status, c.verification_status, c.review_status
                FROM complaints c
                LEFT JOIN users u ON c.user_id = u.id
                ORDER BY c.created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in c.fetchall()]

    # ── Fraud & Verification Analytics ────────────────────────────────────

    @staticmethod
    def get_fraud_stats() -> dict:
        """Returns fraud-related aggregate stats for the dashboard."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT
                    SUM(CASE WHEN fraud_status = 'Clean' THEN 1 ELSE 0 END) as clean_count,
                    SUM(CASE WHEN fraud_status = 'Review Required' THEN 1 ELSE 0 END) as review_required_count,
                    SUM(CASE WHEN fraud_status = 'Suspicious' THEN 1 ELSE 0 END) as suspicious_count,
                    SUM(CASE WHEN verification_status = 'Verified' THEN 1 ELSE 0 END) as verified_count,
                    SUM(CASE WHEN verification_status = 'Unverified' THEN 1 ELSE 0 END) as unverified_count,
                    SUM(CASE WHEN review_status = 'Pending' THEN 1 ELSE 0 END) as pending_review_count,
                    SUM(CASE WHEN review_status = 'Genuine' THEN 1 ELSE 0 END) as genuine_count,
                    SUM(CASE WHEN review_status = 'Fake' THEN 1 ELSE 0 END) as fake_count,
                    AVG(fraud_score) as avg_fraud_score
                FROM complaints
            ''')
            row = c.fetchone()
            return {
                'clean': row['clean_count'] or 0,
                'review_required': row['review_required_count'] or 0,
                'suspicious': row['suspicious_count'] or 0,
                'verified': row['verified_count'] or 0,
                'unverified': row['unverified_count'] or 0,
                'pending_review': row['pending_review_count'] or 0,
                'genuine': row['genuine_count'] or 0,
                'fake': row['fake_count'] or 0,
                'avg_fraud_score': round(row['avg_fraud_score'] or 0.0, 3)
            }

    @staticmethod
    def get_all_complaints_detailed() -> list[dict]:
        """Returns all complaints with fraud/verification/review columns for admin table."""
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT c.id, c.complaint_number, 
                       COALESCE(u.full_name, c.guest_name, c.user_name, 'Anonymous') as display_name,
                       COALESCE(u.email, c.guest_email, 'Unknown') as display_email,
                       c.user_type, c.category, c.status, c.created_at,
                       c.fraud_score, c.fraud_status, c.verification_status, c.review_status
                FROM complaints c
                LEFT JOIN users u ON c.user_id = u.id
                ORDER BY c.created_at DESC
            ''')
            return [dict(row) for row in c.fetchall()]
