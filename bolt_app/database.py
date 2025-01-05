import psycopg2
import pandas as pd
from typing import Optional, Tuple, List, Dict
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self):
        self.connection_params = {
            "dbname": "bpo_system",
            "user": "postgres",
            "password": "Vivek@2004",
            "host": "localhost",
            "port": "5432"
        }

    def connect(self) -> Optional[psycopg2.extensions.connection]:
        try:
            return psycopg2.connect(**self.connection_params)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None

    def submit_complaint(self, name: str, phone: str, description: str, 
                        sentiment: float, urgency: float, politeness: float, 
                        priority_score: float) -> Optional[int]:
        conn = self.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO complaints 
                        (customer_name, customer_phone_number, complaint_description, 
                         sentiment_score, urgency_score, priority_score, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING complaint_id
                        """, (name, phone, description, sentiment, urgency, 
                              priority_score, 'pending'))
                    complaint_id = cursor.fetchone()[0]
                conn.commit()
                return complaint_id
            except Exception as e:
                print(f"Error submitting complaint: {e}")
                return None
            finally:
                conn.close()
        return None

    def get_complaints(self, status_filter: str = "All", 
                      priority_filter: str = "All",
                      search: str = "") -> pd.DataFrame:
        conn = self.connect()
        if conn:
            try:
                query = """
                    SELECT 
                        complaint_id, customer_name, customer_phone_number,
                        complaint_description, sentiment_score, urgency_score,
                        priority_score, status, created_at
                    FROM complaints 
                    WHERE 1=1
                """
                params = []

                if status_filter != "All":
                    query += " AND status = %s"
                    params.append(status_filter.lower())

                if priority_filter != "All":
                    if priority_filter == "High":
                        query += " AND priority_score >= 0.7"
                    elif priority_filter == "Medium":
                        query += " AND priority_score >= 0.4 AND priority_score < 0.7"
                    else:
                        query += " AND priority_score < 0.4"

                if search:
                    query += """ AND (
                        customer_name ILIKE %s 
                        OR complaint_description ILIKE %s
                    )"""
                    search_pattern = f"%{search}%"
                    params.extend([search_pattern, search_pattern])

                query += " ORDER BY priority_score DESC, created_at DESC"
                
                return pd.read_sql_query(query, conn, params=params)
            finally:
                conn.close()
        return pd.DataFrame()

    def get_dashboard_metrics(self) -> Tuple[int, int, float]:
        conn = self.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                            AVG(priority_score) as avg_priority
                        FROM complaints
                    """)
                    total, pending, avg_priority = cursor.fetchone()
                    return total or 0, pending or 0, avg_priority or 0.0
            finally:
                conn.close()
        return 0, 0, 0.0

    def resolve_complaint(self, complaint_id: int) -> bool:
        conn = self.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE complaints
                        SET 
                            status = 'resolved',
                            resolution_time = NOW() - created_at
                        WHERE complaint_id = %s
                    """, (complaint_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error resolving complaint: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_agent_calls(self, agent_id: str, time_period: str = "daily") -> pd.DataFrame:
        conn = self.connect()
        if conn:
            try:
                query = """
                    SELECT * FROM call_summaries
                    WHERE agent_id = %s
                """
                if time_period == "daily":
                    query += " AND created_at >= CURRENT_DATE"
                elif time_period == "weekly":
                    query += " AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
                elif time_period == "monthly":
                    query += " AND created_at >= CURRENT_DATE - INTERVAL '30 days'"
                
                return pd.read_sql_query(query, conn, params=[agent_id])
            finally:
                conn.close()
        return pd.DataFrame()

    def get_all_calls(self) -> pd.DataFrame:
        conn = self.connect()
        if conn:
            try:
                query = "SELECT * FROM call_summaries"
                return pd.read_sql_query(query, conn)
            finally:
                conn.close()
        return pd.DataFrame()

    def update_callback_time(self, complaint_id: int, callback_time: datetime) -> bool:
        conn = self.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO callbacks (complaint_id, scheduled_time)
                        VALUES (%s, %s)
                        ON CONFLICT (complaint_id) 
                        DO UPDATE SET scheduled_time = EXCLUDED.scheduled_time
                    """, (complaint_id, callback_time))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error updating callback time: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_pending_callbacks(self) -> List[Dict]:
        conn = self.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            cb.id,
                            c.customer_name,
                            c.complaint_description,
                            cb.scheduled_time,
                            c.priority_score
                        FROM callbacks cb
                        JOIN complaints c ON cb.complaint_id = c.complaint_id
                        WHERE cb.status = 'pending'
                        ORDER BY cb.scheduled_time ASC
                    """)
                    columns = ['id', 'customer_name', 'complaint_description', 
                              'scheduled_time', 'priority']
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
            finally:
                conn.close()
        return []

    def get_pending_complaints_count(self) -> int:
        conn = self.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM complaints 
                        WHERE status = 'pending'
                    """)
                    return cursor.fetchone()[0]
            finally:
                conn.close()
        return 0

    def save_call_summary(self, summary_data: Dict) -> bool:
        conn = self.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO call_summaries 
                        (call_id, summary, created_at)
                        VALUES (%s, %s, %s)
                    """, (
                        summary_data['call_id'],
                        json.dumps(summary_data['summary']),
                        summary_data['created_at']
                    ))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error saving call summary: {e}")
                return False
            finally:
                conn.close()
        return False