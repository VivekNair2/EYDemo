from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
from database import DatabaseManager

class CallbackScheduler:
    def __init__(self):
        self.db = DatabaseManager()

    def schedule_callback(self, complaint_id: int, priority: float) -> datetime:
        """Schedule a callback based on priority and current workload"""
        current_time = datetime.now()
        
        # Calculate callback time based on priority
        if priority >= 0.8:  # High priority
            delay = timedelta(hours=1)
        elif priority >= 0.5:  # Medium priority
            delay = timedelta(hours=3)
        else:  # Low priority
            delay = timedelta(hours=6)
            
        callback_time = current_time + delay
        
        # Update database with callback time
        self.db.update_callback_time(complaint_id, callback_time)
        return callback_time

    def get_pending_callbacks(self) -> List[Dict]:
        """Get all pending callbacks sorted by priority"""
        return self.db.get_pending_callbacks()

    def mark_callback_completed(self, complaint_id: int):
        """Mark a callback as completed"""
        self.db.update_callback_status(complaint_id, "completed")