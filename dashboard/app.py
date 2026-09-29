import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page configuration
st.set_page_config(layout="wide", page_title="Financial Fraud Detector")

# Title and Header
st.title("Automated Financial Fraud & Anomaly Detector")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    # Load both datasets
    transactions_df = pd.read_csv("data/transactions.csv")
    flagged_df = pd.read_csv("data/flagged_transactions.csv")
    
    # Convert timestamp to datetime
    transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'])
    flagged_df['timestamp'] = pd.to_datetime(flagged_df['timestamp'])
    
    return transactions_df, flagged_df

transactions_df, flagged_df = load_data()

# KPI Metrics
total_transactions = len(transactions_df)
total_flagged = len(flagged_df)
high_risk_count = len(flagged_df[flagged_df['risk_score'] == 'High'])
medium_risk_count = len(flagged_df[flagged_df['risk_score'] == 'Medium'])
total_fraud_volume = flagged_df['amount'].sum()

st.subheader("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Transactions Processed",
        value=f"{total_transactions:,}"
    )

with col2:
    st.metric(
        label="Total Flagged Anomalies",
        value=f"{total_flagged}",
        delta=f"{(total_flagged/total_transactions)*100:.1f}% of total"
    )

with col3:
    st.metric(
        label="High Risk Count",
        value=f"{high_risk_count}",
        delta=f"Medium Risk: {medium_risk_count}"
    )

with col4:
    st.metric(
        label="Total Fraud Volume ($)",
        value=f"${total_fraud_volume:,.2f}"
    )

st.markdown("---")

# Visualizations
st.subheader("Fraud Detection Visualizations")

# Row 1: Bar chart and Scatter plot
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Flagged Transactions by Risk Level")
    risk_counts = flagged_df['risk_score'].value_counts().reset_index()
    risk_counts.columns = ['Risk Level', 'Count']
    
    # Define color map
    color_map = {'High': '#e74c3c', 'Medium': '#f39c12', 'Low': '#27ae60'}
    
    fig_bar = px.bar(
        risk_counts,
        x='Risk Level',
        y='Count',
        color='Risk Level',
        color_discrete_map=color_map,
        text='Count'
    )
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.markdown("### Normal vs Flagged Transactions Over Time")
    
    # Create a combined dataset for visualization
    transactions_df['status'] = 'Normal'
    flagged_df_copy = flagged_df.copy()
    flagged_df_copy['status'] = 'Flagged'
    
    combined_df = pd.concat([transactions_df, flagged_df_copy], ignore_index=True)
    
    fig_scatter = px.scatter(
        combined_df,
        x='timestamp',
        y='amount',
        color='status',
        color_discrete_map={'Normal': '#3498db', 'Flagged': '#e74c3c'},
        hover_data=['transaction_id', 'user_id', 'risk_score'],
        opacity=0.7
    )
    fig_scatter.update_layout(
        xaxis_title="Timestamp",
        yaxis_title="Amount ($)"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# Row 2: Donut chart and Interactive Data Viewer
col_donut, col_filter = st.columns([1, 2])

with col_donut:
    st.markdown("### Suspicious Activity by Merchant Category")
    merchant_counts = flagged_df['merchant_category'].value_counts().reset_index()
    merchant_counts.columns = ['Merchant Category', 'Count']
    
    fig_donut = px.pie(
        merchant_counts,
        values='Count',
        names='Merchant Category',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_donut, use_container_width=True)

# Interactive Data Viewer with Sidebar Filters
st.markdown("---")
st.subheader("Interactive Data Viewer")

# Sidebar filters
st.sidebar.header("Filters")

# Risk Level filter
risk_options = ['All'] + list(flagged_df['risk_score'].unique())
selected_risk = st.sidebar.selectbox("Risk Level", risk_options)

# Merchant Category filter
merchant_options = ['All'] + list(flagged_df['merchant_category'].unique())
selected_merchant = st.sidebar.selectbox("Merchant Category", merchant_options)

# Apply filters
filtered_df = flagged_df.copy()

if selected_risk != 'All':
    filtered_df = filtered_df[filtered_df['risk_score'] == selected_risk]

if selected_merchant != 'All':
    filtered_df = filtered_df[filtered_df['merchant_category'] == selected_merchant]

st.write(f"Showing {len(filtered_df)} of {len(flagged_df)} flagged transactions")

# Display interactive table with key columns
display_columns = [
    'transaction_id', 'user_id', 'amount', 'timestamp', 
    'location', 'merchant_category', 'risk_score'
]

st.dataframe(
    filtered_df[display_columns],
    use_container_width=True,
    hide_index=True
)

# Download filtered data
if len(filtered_df) > 0:
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download Filtered Data",
        data=csv,
        file_name="filtered_flagged_transactions.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("*Data generated for demonstration purposes*")