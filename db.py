import psycopg2
from openai import OpenAI
import os 
from dotenv import load_dotenv
load_dotenv()
os.environ['OPENAI_API_KEY']=os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
client = OpenAI()

# Database connection setup
def connect_to_db():
    try:
        connection = psycopg2.connect(
            dbname="BPO",
            user="postgres",
            password="Vivek@2004",
            host="localhost",
            port="5432"
        )
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Analyze sentiment
def analyze_sentiment(complaint_text):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes sentiment of complaints."},
                {"role": "user", "content": f"Analyze the sentiment of the following complaint and classify and give a sentiment score on a scale from 0 to 1 ,0 being very  positive and 1 being very negative:\n\n{complaint_text}. Just return the sentiment score value and nothing else"}
            ]
        )
        sentiment = completion.choices[0].message.content.lower()
        print(f"the sentiment for the text is {sentiment}")
        return sentiment
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return 'neutral'

# Evaluate urgency
def evaluate_urgency(complaint_text):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that evaluates urgency of complaints."},
                {"role": "user", "content": f"Evaluate the urgency of the following complaint on a scale from 0 (not urgent) to 1 (very urgent):\n\n{complaint_text}.Just return the score and nothing else"}
            ]
        )
        urgency_score = completion.choices[0].message.content
        print(f"the urgenccess for the text is :{ urgency_score}")
        return urgency_score
    except Exception as e:
        print(f"Error in urgency evaluation: {e}")
        return 0.0

# Assess politeness
def assess_politeness(complaint_text):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that assesses politeness of complaints."},
                {"role": "user", "content": f"Assess the politeness of the following complaint on a scale from 0 (rude) to 1 (polite):\n\n{complaint_text}. just return the score and nothing else"}
            ]
        )
        politeness_score = float(completion.choices[0].message.content)
        print(f"the politeness score: {politeness_score}")
        return politeness_score
    except Exception as e:
        print(f"Error in politeness assessment: {e}")
        return 0.5

# Calculate priority score
def calculate_priority(sentiment, urgency, politeness):
    sentiment_score = 1 if 'negative' in sentiment else 0
    print(f"sentiment score: {sentiment_score}")
    priority_score = (float(sentiment_score) * 0.5) + (float(urgency) * 0.3) + ((1 - float(politeness)) * 0.2)
    return priority_score

# Update complaint in the database
def update_complaint_in_db(connection, complaint_id, sentiment, urgency, politeness, priority):
    try:
        cursor = connection.cursor()
        query = """
        UPDATE complaints
        SET sentiment_score = %s,
            urgency_score = %s,
            priority_score = %s,
            status = 'pending'
        WHERE complaint_id = %s;
        """
        cursor.execute(query, (sentiment, urgency, priority, complaint_id))
        connection.commit()
        cursor.close()
        print(f"Complaint ID {complaint_id} updated successfully.")
    except Exception as e:
        print(f"Error updating the complaint: {e}")

# Process a single complaint
def process_complaint(connection, complaint_id, complaint_text):
    sentiment = analyze_sentiment(complaint_text)
    urgency = evaluate_urgency(complaint_text)
    politeness = assess_politeness(complaint_text)
    priority = calculate_priority(sentiment, urgency, politeness)
    update_complaint_in_db(connection, complaint_id, sentiment, urgency, politeness, priority)

# Process all pending complaints
def process_all_complaints():
    connection = connect_to_db()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        query = "SELECT complaint_id, complaint_description FROM complaints WHERE status = 'pending';"
        cursor.execute(query)
        complaints = cursor.fetchall()

        for complaint_id, complaint_text in complaints:
            process_complaint(connection, complaint_id, complaint_text)

        cursor.close()
    except Exception as e:
        print(f"Error fetching complaints: {e}")
    finally:
        connection.close()

# Main execution
if __name__ == "__main__":
    process_all_complaints()
