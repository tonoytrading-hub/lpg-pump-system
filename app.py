import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- MOBILE SETUP ---
st.set_page_config(page_title="Tonoy & Farida LPG", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- STATION SELECTOR ---
st.title("⛽ LPG 24h Daily Report")
pump_name = st.selectbox("Select Station", ["Tonoy LPG", "Farida LPG"])
st.subheader(f"Unit: {pump_name}")
st.write(f"**Date:** {datetime.now().strftime('%d %b, %Y')}")

st.divider()

# --- 1. RATE ---
rate = st.number_input("Selling Rate (BDT/L)", min_value=0.0, step=0.1, format="%.2f")

# --- 2. NOZZLES (1 to 4) ---
st.header("🔢 Nozzle Readings")
total_l_sold = 0.0

for n in range(1, 5):
    with st.expander(f"Nozzle {n} Meter", expanded=(n==1)):
        c1, c2 = st.columns(2)
        op = c1.number_input(f"Opening N{n}", min_value=0.0, key=f"{pump_name}_op{n}")
        cl = c2.number_input(f"Closing N{n}", min_value=0.0, key=f"{pump_name}_cl{n}")
        
        diff = cl - op
        total_l_sold += max(0, diff)
        st.write(f"Volume: **{max(0, diff):,.2f} L**")

# --- 3. REVENUE & CASH ---
st.header("💰 Cash & Expenses")
total_cash_sales = total_l_sold * rate
st.metric("Total 24h Sales", f"{total_cash_sales:,.2f} BDT")

cash_cf = st.number_input("Cash C/F (from yesterday)", min_value=0.0)
expenses = st.number_input("Total Expenses", min_value=0.0)
bank_dep = st.number_input("Bank Deposit", min_value=0.0)

cash_in_hand = (cash_cf + total_cash_sales) - (expenses + bank_dep)
st.metric("Final Cash in Hand", f"{cash_in_hand:,.2f} BDT")

# --- 4. STOCK ---
st.header("🛢️ Tank Stock")
st_op = st.number_input("Opening Tank Stock (L)", min_value=0.0)
st_pur = st.number_input("Refills Received (L)", min_value=0.0)
gauge_val = st.number_input("Physical Gauge Reading (L)", min_value=0.0)

calc_cl = (st_op + st_pur) - total_l_sold
variance = gauge_val - calc_cl

if gauge_val > 0:
    st.write(f"Calc. Stock: {calc_cl:,.2f} L | Variance: **{variance:,.2f} L**")

# --- 5. SUBMIT ---
if st.button(f"🚀 Submit {pump_name} Report", use_container_width=True):
    new_data = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Station": pump_name,
        "Rate": rate,
        "Total_L": total_l_sold,
        "Total_Cash": total_cash_sales,
        "Cash_Hand": cash_in_hand,
        "Gauge_Stock": gauge_val,
        "Variance": variance
    }])
    
    # This pushes data to your Google Sheet
    existing = conn.read(worksheet="LPG_Logs")
    updated = pd.concat([existing, new_data], ignore_index=True)
    conn.update(worksheet="LPG_Logs", data=updated)
    st.success(f"Report for {pump_name} Synced!")
    st.balloons()
