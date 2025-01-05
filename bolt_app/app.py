import streamlit as st
from database import DatabaseManager
from ai_analyzer import ComplaintAnalyzer
from call_analytics import CallAnalytics
from workload_distributor import WorkloadDistributor
from knowledge_base import KnowledgeBase
from callback_scheduler import CallbackScheduler
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import time
from styles import load_css
from call_agent import resolve

st.set_page_config(
    page_title="Resolvr",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(load_css(), unsafe_allow_html=True)

# Initialize components
db = DatabaseManager()
analyzer = ComplaintAnalyzer()
analytics = CallAnalytics(db)
kb = KnowledgeBase()
scheduler = CallbackScheduler()
distributor = WorkloadDistributor(db)

def client_interface():
    col1, col2 = st.columns([5, 5])

    with col1:
        st.markdown(f"""
            <div class="form-container">
                <div class="logo-header">
                    <img src="resolvr.jpg" class="company-logo" style="width: 100%; height: auto;">
                </div>
                <div class="form-title">Submit Your Complaint</div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("complaint_form", clear_on_submit=True):
            name = st.text_input("Full Name", placeholder="Enter your name")
            phone = st.text_input("Phone Number", placeholder="Enter your phone number")
            description = st.text_area(
                "Complaint Description",
                height=150,
                placeholder="Please describe your issue in detail..."
            )

            submitted = st.form_submit_button("Submit Complaint")

            if submitted:
                if name and phone and description:
                    with st.spinner("Analyzing your complaint..."):
                        # Analyze complaint using AI
                        sentiment, urgency, politeness, priority = analyzer.analyze_complaint(description)

                        # Submit to database
                        complaint_id = db.submit_complaint(
                            name, phone, description,
                            sentiment, urgency, politeness, priority
                        )

                        if complaint_id:
                            # Schedule callback based on priority
                            callback_time = scheduler.schedule_callback(complaint_id, priority)
                            
                            # Assign to best available agent
                            agent_id = distributor.assign_complaint(complaint_id)
                            
                            st.balloons()
                            st.success(f"""
                                Thank you! Your complaint has been registered successfully!
                                Callback scheduled for: {callback_time.strftime('%Y-%m-%d %H:%M')}
                            """)
                        else:
                            st.error("There was an error submitting your complaint. Please try again.")
                else:
                    st.error("Please fill in all required fields.")

def admin_interface():
    st.markdown("""
        <div class="admin-header">
            <h1>Admin Dashboard</h1>
        </div>
    """, unsafe_allow_html=True)

    # Dashboard Metrics
    metrics = analytics.get_team_metrics()
    total = metrics['total_calls']
    pending = db.get_pending_complaints_count()
    avg_satisfaction = metrics['satisfaction_rate']

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Cases</div>
                <div class="metric-value">{total}</div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Pending Cases</div>
                <div class="metric-value">{pending}</div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Avg Satisfaction</div>
                <div class="metric-value">{avg_satisfaction:.2f}%</div>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Callback Rate</div>
                <div class="metric-value">{metrics['callback_rate']:.2f}%</div>
            </div>
        """, unsafe_allow_html=True)

    # Insights
    st.subheader("AI Insights")
    insights = analytics.generate_insights()
    for insight in insights:
        st.info(insight)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Resolved"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
    with col3:
        search = st.text_input("Search", placeholder="Search by name or description...")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Complaints", "Callbacks", "Knowledge Base"])

    with tab1:
        display_complaints(status_filter, priority_filter, search)

    with tab2:
        display_callbacks()

    with tab3:
        manage_knowledge_base()

def display_complaints(status_filter, priority_filter, search):
    df = db.get_complaints(status_filter, priority_filter, search)
    
    for _, row in df.iterrows():
        with st.expander(
            f"#{row['complaint_id']} - {row['customer_name']} "
            f"(Priority: {row['priority_score']:.2f})"
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                    **Phone:** {row['customer_phone_number']}  
                    **Status:** {row['status']}  
                    **Description:** {row['complaint_description']}  
                    **Created:** {row['created_at']}
                """)
                
                if row['status'] != 'resolved':
                    if st.button("Resolve", key=f"resolve_{row['complaint_id']}"):
                        resolve(row['customer_phone_number'])
                        if db.resolve_complaint(row['complaint_id']):
                            st.success("Complaint resolved successfully!")
                            time.sleep(1)
                            st.experimental_rerun()
            
            with col2:
                st.markdown("### Quick Actions")
                if st.button("Schedule Callback", key=f"callback_{row['complaint_id']}"):
                    callback_time = scheduler.schedule_callback(
                        row['complaint_id'],
                        row['priority_score']
                    )
                    st.success(f"Callback scheduled for {callback_time}")

def display_callbacks():
    callbacks = scheduler.get_pending_callbacks()
    
    if not callbacks:
        st.info("No pending callbacks")
        return
        
    for callback in callbacks:
        with st.expander(
            f"Callback for {callback['customer_name']} at "
            f"{callback['scheduled_time'].strftime('%Y-%m-%d %H:%M')}"
        ):
            st.markdown(f"""
                **Priority:** {callback['priority']:.2f}  
                **Original Complaint:** {callback['complaint_description']}
            """)
            
            if st.button("Mark Complete", key=f"complete_{callback['id']}"):
                scheduler.mark_callback_completed(callback['id'])
                st.success("Callback marked as completed")
                time.sleep(1)
                st.experimental_rerun()

def manage_knowledge_base():
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("Add New Article")
        with st.form("kb_form"):
            title = st.text_input("Title")
            content = st.text_area("Content")
            tags = st.text_input("Tags (comma-separated)")
            
            if st.form_submit_button("Add Article"):
                if title and content:
                    kb.add_article(
                        title,
                        content,
                        [tag.strip() for tag in tags.split(",") if tag.strip()]
                    )
                    st.success("Article added successfully!")
    
    with col2:
        st.subheader("Knowledge Base Search")
        search_query = st.text_input("Search Knowledge Base")
        if search_query:
            results = kb.search(search_query)
            for article in results:
                with st.expander(article['title']):
                    st.write(article['content'])
                    st.caption(f"Tags: {', '.join(article['tags'])}")

def main():
    role = st.sidebar.radio("Select Role", ["Client", "Admin"])

    if role == "Client":
        client_interface()
    else:
        admin_interface()

if __name__ == "__main__":
    main()