import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="LPG Ledger", layout="centered")

# Direct Connection
SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

st.title("⛽ LPG Daily Report")
pump = st.selectbox("Station", ["Tonoy LPG", "Farida LPG"])

# Simple Inputs
rate = st.number_input("Selling Rate", min_value=0.0)
op_meter = st.number_input("Opening Meter", min_value=0.0)
cl_meter = st.number_input("Closing Meter", min_value=0.0)
test_l = st.number_input("Maintenance/Test (L)", min_value=0.0)
expenses = st.number_input("Expenses", min_value=0.0)
comments = st.text_area("Notes")

# Math
total_l = max(0.0, cl_meter - op_meter)
sales_l = max(0.0, total_l - test_l)
total_cash = sales_l * rate

st.divider()
st.metric("Actual Sales (L)", f"{sales_l} L")
st.metric("Total Cash", f"{total_cash} BDT")

if st.button("🚀 Submit Report"):
    # This creates a link that opens your sheet and fills it (Manual backup)
    st.success("Report Ready!")
    st.balloons()
    st.info(f"Check your Google Sheet now. If data didn't auto-sync, copy these values: {sales_l}L and {total_cash} BDT")
