# app.py
import streamlit as st
from database import DatabaseManager
from ai_analyzer import ComplaintAnalyzer
import plotly.graph_objects as go
import pandas as pd
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

# Initialize database and analyzer
db = DatabaseManager()
analyzer = ComplaintAnalyzer()

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
                        success = db.submit_complaint(
                            name, phone, description,
                            sentiment, urgency, politeness, priority
                        )

                        if success:
                            st.balloons()
                            st.success("Thank you! Your complaint has been registered successfully!")
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
    total, pending, avg_priority = db.get_dashboard_metrics()

    c1, c2, c3 = st.columns(3)
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
                <div class="metric-title">Avg Priority</div>
                <div class="metric-value">{avg_priority:.2f}</div>
            </div>
        """, unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Resolved"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
    with col3:
        search = st.text_input("Search", placeholder="Search by name or description...")

    # Get complaints from database
    df = db.get_complaints()

    # Apply filters
    if status_filter != "All":
        df = df[df['status'].str.lower() == status_filter.lower()]

    if priority_filter != "All":
        if priority_filter == "High":
            df = df[df['priority_score'] >= 0.7]
        elif priority_filter == "Medium":
            df = df[(df['priority_score'] >= 0.4) & (df['priority_score'] < 0.7)]
        else:
            df = df[df['priority_score'] < 0.4]

    if search:
        df = df[
            df['customer_name'].str.contains(search, case=False) |
            df['complaint_description'].str.contains(search, case=False)
        ]

    # Display complaints
    for _, row in df.iterrows():
        with st.expander(
            f"#{row['complaint_id']} - {row['customer_name']} "
            f"(Priority: {row['priority_score']:.2f})"
        ):
            st.markdown(f"""
                **Phone:** {row['customer_phone_number']}  
                **Status:** {row['status']}  
                **Description:** {row['complaint_description']}  
                **Created:** {row['created_at']}
            """)

            if row['status'] != 'resolved':
                if st.button("Resolve", key=f"resolve_{row['complaint_id']}"):
                    # Pass the phone number to resolve function
                    resolve(row['customer_phone_number'])  # Pass phone number here
                    if db.resolve_complaint(row['complaint_id']):
                        st.success("Complaint resolved successfully!")
                        time.sleep(1)
                        st.experimental_rerun()

    # Add analytics and graphs
    st.markdown("### Analytics")
    priority_distribution = df['priority_score'].value_counts(bins=3, sort=False)
    fig = go.Figure(
        go.Bar(
            x=["Low", "Medium", "High"],
            y=priority_distribution.values,
            marker_color=['green', 'orange', 'red']
        )
    )
    fig.update_layout(
        title="Priority Distribution",
        xaxis_title="Priority",
        yaxis_title="Count",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

    resolved_status = df['status'].value_counts()
    pie_chart = go.Figure(
        go.Pie(
            labels=resolved_status.index,
            values=resolved_status.values,
            hole=0.4
        )
    )
    pie_chart.update_layout(title="Status Distribution", template="plotly_white")
    st.plotly_chart(pie_chart, use_container_width=True)

def main():
    role = st.sidebar.radio("Select Role", ["Client", "Admin"])

    if role == "Client":
        client_interface()
    else:
        admin_interface()

if __name__ == "__main__":
    main()
