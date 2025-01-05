from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class CallAnalytics:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_agent_performance(self, agent_id: str, time_period: str = "daily") -> Dict:
        """Calculate agent performance metrics"""
        calls = self.db.get_agent_calls(agent_id, time_period)
        
        if not calls.empty:
            return {
                "total_calls": len(calls),
                "avg_duration": calls['duration'].mean(),
                "avg_satisfaction": calls['satisfaction_score'].mean(),
                "resolution_rate": (calls['resolved'].sum() / len(calls)) * 100,
                "avg_sentiment": calls['sentiment_score'].mean()
            }
        return {}

    def get_team_metrics(self) -> Dict:
        """Get overall team performance metrics"""
        all_calls = self.db.get_all_calls()
        
        return {
            "total_calls": len(all_calls),
            "avg_resolution_time": all_calls['resolution_time'].mean(),
            "satisfaction_rate": all_calls['satisfaction_score'].mean(),
            "callback_rate": (all_calls['required_callback'].sum() / len(all_calls)) * 100
        }

    def generate_insights(self) -> List[str]:
        """Generate actionable insights from call data"""
        metrics = self.get_team_metrics()
        insights = []
        
        if metrics['avg_resolution_time'] > timedelta(hours=24):
            insights.append("Resolution times are higher than target. Consider additional training.")
            
        if metrics['satisfaction_rate'] < 0.7:
            insights.append("Customer satisfaction is below target. Review call quality.")
            
        if metrics['callback_rate'] > 30:
            insights.append("High callback rate detected. Evaluate first-call resolution strategies.")
            
        return insights