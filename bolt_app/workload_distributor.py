from typing import Dict, Optional
import pandas as pd
from datetime import datetime, timedelta

class WorkloadDistributor:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_agent_workload(self, agent_id: str) -> Dict:
        """Get current workload metrics for an agent"""
        conn = self.db.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as active_complaints,
                            AVG(priority_score) as avg_priority,
                            (
                                SELECT efficiency_score 
                                FROM agent_performance 
                                WHERE agent_id = %s 
                                AND date = CURRENT_DATE
                            ) as today_efficiency
                        FROM complaints
                        WHERE assigned_agent = %s AND status = 'pending'
                    """, (agent_id, agent_id))
                    
                    result = cursor.fetchone()
                    return {
                        "active_complaints": result[0],
                        "avg_priority": result[1] or 0,
                        "efficiency_score": result[2] or 0
                    }
            finally:
                conn.close()
        return {"active_complaints": 0, "avg_priority": 0, "efficiency_score": 0}

    def find_best_agent(self, complaint_priority: float) -> Optional[str]:
        """Find the most suitable agent for a new complaint"""
        conn = self.db.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            a.agent_id,
                            a.current_workload,
                            COALESCE(ap.efficiency_score, 0) as efficiency,
                            COUNT(c.complaint_id) as active_complaints
                        FROM agents a
                        LEFT JOIN agent_performance ap 
                            ON a.agent_id = ap.agent_id 
                            AND ap.date = CURRENT_DATE
                        LEFT JOIN complaints c 
                            ON a.agent_id = c.assigned_agent 
                            AND c.status = 'pending'
                        WHERE a.status = 'available'
                        GROUP BY a.agent_id, a.current_workload, ap.efficiency_score
                        ORDER BY 
                            active_complaints ASC,
                            efficiency DESC
                        LIMIT 1
                    """)
                    
                    result = cursor.fetchone()
                    return result[0] if result else None
            finally:
                conn.close()
        return None

    def update_agent_workload(self, agent_id: str, complaint_priority: float):
        """Update agent's workload after assigning a new complaint"""
        conn = self.db.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE agents
                        SET current_workload = current_workload + %s
                        WHERE agent_id = %s
                    """, (complaint_priority, agent_id))
                conn.commit()
            finally:
                conn.close()

    def rebalance_workload(self):
        """Rebalance workload among available agents"""
        conn = self.db.connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # Find overloaded agents
                    cursor.execute("""
                        WITH agent_loads AS (
                            SELECT 
                                assigned_agent,
                                COUNT(*) as complaint_count,
                                AVG(priority_score) as avg_priority
                            FROM complaints
                            WHERE status = 'pending'
                            GROUP BY assigned_agent
                        )
                        SELECT assigned_agent
                        FROM agent_loads
                        WHERE complaint_count > (
                            SELECT AVG(complaint_count) * 1.2
                            FROM agent_loads
                        )
                    """)
                    
                    overloaded_agents = cursor.fetchall()
                    
                    for agent in overloaded_agents:
                        # Reassign some complaints to less loaded agents
                        cursor.execute("""
                            WITH available_agent AS (
                                SELECT a.agent_id
                                FROM agents a
                                LEFT JOIN complaints c ON a.agent_id = c.assigned_agent
                                WHERE a.status = 'available'
                                GROUP BY a.agent_id
                                HAVING COUNT(c.complaint_id) < (
                                    SELECT AVG(complaint_count) 
                                    FROM (
                                        SELECT COUNT(*) as complaint_count
                                        FROM complaints
                                        WHERE status = 'pending'
                                        GROUP BY assigned_agent
                                    ) as counts
                                )
                                ORDER BY COUNT(c.complaint_id) ASC
                                LIMIT 1
                            )
                            UPDATE complaints
                            SET assigned_agent = (SELECT agent_id FROM available_agent)
                            WHERE complaint_id IN (
                                SELECT complaint_id
                                FROM complaints
                                WHERE assigned_agent = %s
                                AND status = 'pending'
                                ORDER BY priority_score ASC
                                LIMIT 2
                            )
                        """, (agent[0],))
                
                conn.commit()
            finally:
                conn.close()