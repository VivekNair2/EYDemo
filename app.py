import streamlit as st
import psycopg2
from openai import OpenAI
import os
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

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
            messages=[{"role": "system", "content": "You are a helpful assistant that analyzes sentiment of complaints."},
                      {"role": "user", "content": f"Analyze the sentiment of the following complaint and classify and give a sentiment score on a scale from 0 to 1 ,0 being very positive and 1 being very negative:\n\n{complaint_text}. Just return the sentiment score value and nothing else"}]
        )
        sentiment = completion.choices[0].message.content.lower()
        return sentiment
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return 'neutral'

# Evaluate urgency
def evaluate_urgency(complaint_text):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a helpful assistant that evaluates urgency of complaints."},
                      {"role": "user", "content": f"Evaluate the urgency of the following complaint on a scale from 0 (not urgent) to 1 (very urgent):\n\n{complaint_text}.Just return the score and nothing else"}]
        )
        urgency_score = completion.choices[0].message.content
        return urgency_score
    except Exception as e:
        print(f"Error in urgency evaluation: {e}")
        return 0.0

# Assess politeness
def assess_politeness(complaint_text):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a helpful assistant that assesses politeness of complaints."},
                      {"role": "user", "content": f"Assess the politeness of the following complaint on a scale from 0 (rude) to 1 (polite):\n\n{complaint_text}. just return the score and nothing else"}]
        )
        politeness_score = float(completion.choices[0].message.content)
        return politeness_score
    except Exception as e:
        print(f"Error in politeness assessment: {e}")
        return 0.5

# Calculate priority score
def calculate_priority(sentiment, urgency, politeness):
    sentiment_score = 1 if 'negative' in sentiment else 0
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
    except Exception as e:
        print(f"Error updating the complaint: {e}")

# Client-side interface for submitting complaints
def submit_complaint(name, phone, description):
    sentiment = analyze_sentiment(description)
    urgency = evaluate_urgency(description)
    politeness = assess_politeness(description)
    priority_score = calculate_priority(sentiment, urgency, politeness)

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO complaints (customer_name, customer_phone_number, complaint_description, sentiment_score, urgency_score, priority_score, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, phone, description, sentiment, urgency, priority_score, 'pending'))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

# Admin-side interface for viewing and resolving complaints
def get_complaints():
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT complaint_id, customer_name, customer_phone_number, complaint_description, sentiment_score, urgency_score, priority_score, status FROM complaints ORDER BY priority_score DESC")
        complaints = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(complaints, columns=["complaint_id", "customer_name", "customer_phone_number", "complaint_description", "sentiment_score", "urgency_score", "priority_score", "status"])
    return pd.DataFrame()

def resolve_complaint(complaint_id):
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE complaints
            SET status = 'resolved'
            WHERE complaint_id = %s;
        """, (complaint_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

# Streamlit UI
def main():
    st.title("Complaint Management System")
    
    option = st.sidebar.selectbox("Select Role", ["Client", "Admin"])

    if option == "Client":
        st.header("Submit Your Complaint")
        
        name = st.text_input("Enter Your Name")
        phone = st.text_input("Enter Your Phone Number")
        description = st.text_area("Enter Your Complaint Description")
        
        if st.button("Submit Complaint"):
            if name and phone and description:
                if submit_complaint(name, phone, description):
                    st.success("Your complaint has been submitted successfully!")
                else:
                    st.error("Error submitting your complaint.")
            else:
                st.error("Please fill in all fields.")
    
    elif option == "Admin":
        st.header("Admin Dashboard")
        
        df = get_complaints()
        st.dataframe(df)
        
        complaint_id = st.number_input("Enter Complaint ID to resolve", min_value=1, step=1)
        if st.button("Resolve Complaint"):
            if resolve_complaint(complaint_id):
                st.success(f"Complaint ID {complaint_id} has been resolved!")
            else:
                st.error("Error resolving the complaint.")

if __name__ == "__main__":
    main()
