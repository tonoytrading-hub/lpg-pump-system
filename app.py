import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="LPG Smart Ledger", layout="centered")

# --- 1. SETUP & CALCULATIONS ---
st.title("⛽ LPG Daily Report")
pump = st.selectbox("Select Station", ["Tonoy LPG", "Farida LPG"])

st.subheader("🔢 Meter Readings")
rate = st.number_input("Today's Rate (BDT/L)", min_value=0.0, step=0.1)
op = st.number_input("Opening Meter", min_value=0.0)
cl = st.number_input("Closing Meter", min_value=0.0)

# Automatic Math
total_l = max(0.0, cl - op)
total_cash = total_l * rate

st.divider()
st.metric("Total Litres Sold", f"{total_l:,.2f} L")
st.metric("Total Sales Value", f"{total_cash:,.2f} BDT")

# --- 2. EXPENSES & STOCK ---
st.subheader("💰 Cash & Stock")
col1, col2 = st.columns(2)
exp = col1.number_input("Expenses", min_value=0.0)
dep = col2.number_input("Bank Deposit", min_value=0.0)

st_op = st.number_input("Opening Stock (L)", min_value=0.0)
st_pur = st.number_input("New Purchase (L)", min_value=0.0)
final_stock = (st_op + st_pur) - total_l

st.info(f"Tonight's Closing Stock: {final_stock:,.2f} L")

# --- 3. THE "SAFE" SUBMIT ---
if st.button("🚀 Generate Final Report", use_container_width=True):
    report_data = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Station": pump,
        "Total_L": total_l,
        "Sales_Value": total_cash,
        "Expenses": exp,
        "Bank_Deposit": dep,
        "Closing_Stock": final_stock
    }
    
    st.success("✅ Report Generated!")
    st.table(pd.DataFrame([report_data]))
    
    # Since the Google Connection is giving us trouble, 
    # Use this button to save the data to your phone instantly.
    csv = pd.DataFrame([report_data]).to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download & Save to Phone",
        data=csv,
        file_name=f"LPG_{pump}_{datetime.now().strftime('%d_%m')}.csv",
        mime='text/csv',
    )
