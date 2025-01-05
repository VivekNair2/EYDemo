from openai import OpenAI
import os
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()

class ComplaintAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4"

    def analyze_complaint(self, complaint_text: str) -> Tuple[float, float, float, float]:
        """
        Analyze complaint text and return sentiment, urgency, politeness, and priority scores
        """
        try:
            # Analyze sentiment
            sentiment = self._analyze_sentiment(complaint_text)
            
            # Evaluate urgency
            urgency = self._evaluate_urgency(complaint_text)
            
            # Assess politeness
            politeness = self._assess_politeness(complaint_text)
            
            # Calculate overall priority
            priority = self._calculate_priority(sentiment, urgency, politeness)
            
            return sentiment, urgency, politeness, priority
        except Exception as e:
            print(f"Error analyzing complaint: {e}")
            return 0.5, 0.5, 0.5, 0.5

    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of the complaint text"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """
                        You are a sentiment analyzer for customer complaints.
                        Rate the sentiment on a scale of 0 to 1, where:
                        0 = extremely negative
                        0.5 = neutral
                        1 = positive
                        Return only the numeric score.
                    """},
                    {"role": "user", "content": text}
                ]
            )
            return float(completion.choices[0].message.content.strip())
        except:
            return 0.5

    def _evaluate_urgency(self, text: str) -> float:
        """Evaluate the urgency of the complaint"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """
                        You are an urgency evaluator for customer complaints.
                        Rate the urgency on a scale of 0 to 1, where:
                        0 = not urgent at all
                        0.5 = moderately urgent
                        1 = extremely urgent
                        Consider factors like:
                        - Time sensitivity
                        - Potential impact
                        - Customer's expressed urgency
                        Return only the numeric score.
                    """},
                    {"role": "user", "content": text}
                ]
            )
            return float(completion.choices[0].message.content.strip())
        except:
            return 0.5

    def _assess_politeness(self, text: str) -> float:
        """Assess the politeness level of the complaint"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """
                        You are a politeness assessor for customer complaints.
                        Rate the politeness on a scale of 0 to 1, where:
                        0 = extremely rude
                        0.5 = neutral
                        1 = very polite
                        Consider:
                        - Language used
                        - Tone
                        - Respect shown
                        Return only the numeric score.
                    """},
                    {"role": "user", "content": text}
                ]
            )
            return float(completion.choices[0].message.content.strip())
        except:
            return 0.5

    def _calculate_priority(self, sentiment: float, urgency: float, politeness: float) -> float:
        """
        Calculate overall priority score based on sentiment, urgency, and politeness
        
        Weights:
        - Urgency: 50% (most important)
        - Sentiment: 30% (negative sentiment increases priority)
        - Politeness: 20% (rudeness slightly increases priority)
        """
        sentiment_factor = 1 - sentiment  # Invert sentiment so negative increases priority
        politeness_factor = 1 - politeness  # Invert politeness so rudeness increases priority
        
        priority = (
            (urgency * 0.5) +
            (sentiment_factor * 0.3) +
            (politeness_factor * 0.2)
        )
        
        return round(priority, 2)