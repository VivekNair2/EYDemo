import pandas as pd
from typing import List, Dict
from datetime import datetime
import json
import os

class KnowledgeBase:
    def __init__(self):
        self.kb_file = "knowledge_base.json"
        self.kb_data = self._load_kb()

    def _load_kb(self) -> Dict:
        if os.path.exists(self.kb_file):
            with open(self.kb_file, 'r') as f:
                return json.load(f)
        return {
            "articles": [],
            "solutions": [],
            "frequently_used": {}
        }

    def add_article(self, title: str, content: str, tags: List[str]):
        article = {
            "id": len(self.kb_data["articles"]) + 1,
            "title": title,
            "content": content,
            "tags": tags,
            "created_at": str(datetime.now()),
            "usage_count": 0
        }
        self.kb_data["articles"].append(article)
        self._save_kb()

    def search(self, query: str) -> List[Dict]:
        query = query.lower()
        results = []
        
        for article in self.kb_data["articles"]:
            if (query in article["title"].lower() or 
                query in article["content"].lower() or 
                any(query in tag.lower() for tag in article["tags"])):
                results.append(article)
                article["usage_count"] += 1
                
        self._update_frequently_used()
        self._save_kb()
        return sorted(results, key=lambda x: x["usage_count"], reverse=True)

    def _update_frequently_used(self):
        self.kb_data["frequently_used"] = {
            "articles": sorted(
                self.kb_data["articles"], 
                key=lambda x: x["usage_count"], 
                reverse=True
            )[:5]
        }

    def _save_kb(self):
        with open(self.kb_file, 'w') as f:
            json.dump(self.kb_data, f, indent=2)

    def get_frequently_used(self) -> List[Dict]:
        return self.kb_data["frequently_used"]["articles"]