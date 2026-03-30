import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="LPG Smart Ledger", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. FETCH DATA (SAFE READ) ---
try:
    # Read the sheet to get the last closing values
    df = conn.read(worksheet="LPG_Logs", ttl=0)
    pump = st.sidebar.selectbox("Select Station", ["Tonoy LPG", "Farida LPG"])
    
    # Filter for the specific station to get accurate Carry-Forward
    station_history = df[df['Station'] == pump]
    if not station_history.empty:
        last_row = station_history.iloc[-1]
        prev_stock = float(last_row['Closing_Stock'])
        prev_cash = float(last_row['Cash_Hand'])
    else:
        prev_stock, prev_cash = 0.0, 0.0
except Exception:
    prev_stock, prev_cash, pump = 0.0, 0.0, "Tonoy LPG"
    df = pd.DataFrame()

# --- 2. THE ENTRY FORM ---
st.title(f"⛽ {pump} Online Entry")
st.info(f"Carry Forward: Stock {prev_stock}L | Cash {prev_cash} BDT")

with st.form("lpg_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    rate = col1.number_input("Rate (BDT/L)", min_value=0.0, step=0.1)
    st_pur = col2.number_input("New Stock Purchase (L)", min_value=0.0)

    st.subheader("🔢 Nozzle Readings")
    n_op = st.number_input("Opening Meter (Total)", min_value=0.0)
    n_cl = st.number_input("Closing Meter (Total)", min_value=0.0)
    test_l = st.number_input("Test/Maintenance (L)", min_value=0.0)

    st.subheader("💰 Expenses & Bank")
    exp = st.number_input("Daily Expenses", min_value=0.0)
    dep = st.number_input("Bank Deposit", min_value=0.0)
    
    submit_btn = st.form_submit_button("🚀 Submit to Online Ledger")

    if submit_btn:
        # --- 3. AUTO CALCULATIONS ---
        total_l = max(0.0, n_cl - n_op)
        actual_sales_l = total_l - test_l
        sales_value = actual_sales_l * rate
        
        # New Closing Totals
        new_stock = (prev_stock + st_pur) - total_l
        new_cash = (prev_cash + sales_value) - (exp + dep)

        # --- 4. THE SAFE APPEND (Protects Old Data) ---
        new_entry = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Station": pump,
            "Sales_L": actual_sales_l,
            "Total_Sales_Value": sales_value,
            "Expenses": exp,
            "Bank_Deposit": dep,
            "Cash_Hand": new_cash,
            "Closing_Stock": new_stock,
            "Comments": f"Rate: {rate}"
        }])

        try:
            # We ONLY add the new row to the end of the existing data
            updated_df = pd.concat([df, new_entry], ignore_index=True)
            conn.update(worksheet="LPG_Logs", data=updated_df)
            
            st.success(f"✅ Data for {pump} saved! New Stock: {new_stock}L")
            st.balloons()
        except Exception as e:
            st.error(f"Sync Failed: {e}")
            st.info("Ensure your Google Sheet tab is named 'LPG_Logs' and shared as 'Editor'.")

    
