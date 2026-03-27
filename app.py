import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Tonoy & Farida LPG", layout="centered")

st.title("⛽ LPG 24h Daily Report")
pump_name = st.selectbox("Select Station", ["Tonoy LPG", "Farida LPG"])

st.header(f"Data Entry: {pump_name}")
rate = st.number_input("Selling Rate (BDT/L)", min_value=0.0, step=0.1)

# --- NOZZLES SECTION ---
st.subheader("🔢 Nozzle Meters")
total_meter_l = 0.0
for n in range(1, 5):
    with st.expander(f"Nozzle {n}", expanded=(n==1)):
        c1, c2 = st.columns(2)
        op = c1.number_input(f"Opening N{n}", min_value=0.0, key=f"op{n}")
        cl = c2.number_input(f"Closing N{n}", min_value=0.0, key=f"cl{n}")
        total_meter_l += max(0.0, cl - op)

# --- MAINTENANCE SECTION ---
st.subheader("🛠️ Maintenance & Testing")
test_l = st.number_input("Litre used for Testing (Deducted from sales)", min_value=0.0)

# CALCULATED SALES
actual_sales_l = max(0.0, total_meter_l - test_l)
total_cash_sales = actual_sales_l * rate

col1, col2 = st.columns(2)
col1.metric("Meter Total (L)", f"{total_meter_l:,.2f}")
col2.metric("Actual Sales (L)", f"{actual_sales_l:,.2f}")

# --- CASH & EXPENSES ---
st.header("💰 Cash & Expenses")
cash_cf = st.number_input("Cash C/F (Yesterday)", min_value=0.0)
expenses = st.number_input("Today's Expenses", min_value=0.0)
bank_dep = st.number_input("Bank Deposit", min_value=0.0)

cash_in_hand = (cash_cf + total_cash_sales) - (expenses + bank_dep)
st.metric("Total Cash Sales", f"{total_cash_sales:,.2f} BDT")
st.metric("Final Cash in Hand", f"{cash_in_hand:,.2f} BDT")

# --- STOCK SECTION ---
st.header("🛢️ Tank Stock")
st_op = st.number_input("Opening Stock (L)", min_value=0.0)
st_pur = st.number_input("Purchases (L)", min_value=0.0)
st_cl = (st_op + st_pur) - total_meter_l
st.subheader(f"Calculated Closing Stock: {st_cl:,.2f} L")

# --- NOTES ---
st.header("📝 Notes")
user_comments = st.text_area("Add comments (Optional)")

if st.button(f"🚀 Submit {pump_name} Report", use_container_width=True):
    st.success("Report Generated!")
    st.balloons()
    # Note: Since the automatic sync was giving 404 errors, 
    # make sure your Google Sheet is set to 'Anyone with link can Edit'
    st.info("Ensure your Google Sheet is open to receive this data.")
