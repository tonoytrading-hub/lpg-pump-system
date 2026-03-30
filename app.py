import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Tonoy & Farida LPG", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. FETCH & PROTECT DATA ---
try:
    df = conn.read(worksheet="LPG_Logs", ttl=0)
    pump = st.sidebar.selectbox("Select Station", ["Tonoy LPG", "Farida LPG"])
    
    # Get last closing values for the specific pump
    station_history = df[df['Station'] == pump]
    if not station_history.empty:
        last_row = station_history.iloc[-1]
        prev_stock = float(last_row['Closing_Stock'])
        prev_cash = float(last_row['Cash_Hand'])
    else:
        prev_stock, prev_cash = 0.0, 0.0
except:
    prev_stock, prev_cash, pump = 0.0, 0.0, "Tonoy LPG"
    df = pd.DataFrame()

tab1, tab2 = st.tabs(["📝 Daily Entry", "📊 Monthly Report"])

# --- TAB 1: DAILY ENTRY (4 NOZZLES & RATE CHANGE) ---
with tab1:
    st.header(f"⛽ {pump} - Daily Sales")
    st.sidebar.metric("Yesterday's Stock", f"{prev_stock} L")
    st.sidebar.metric("Yesterday's Cash", f"{prev_cash} BDT")

    # Rate Change Logic
    is_rate_change = st.checkbox("🚨 Did the rate change today?")
    col_r1, col_r2 = st.columns(2)
    r1 = col_r1.number_input("Current Rate (BDT/L)", min_value=0.0, value=120.0)
    r2 = col_r2.number_input("New Rate (BDT/L)", min_value=0.0, disabled=not is_rate_change)

    st.subheader("🔢 Meter Readings (4 Nozzles)")
    total_l = 0.0
    total_money = 0.0

    # 4 Nozzle Layout
    cols = st.columns(2)
    for n in range(1, 5):
        with cols[(n-1)%2].expander(f"Nozzle {n}", expanded=True):
            o = st.number_input(f"Opening N{n}", key=f"o{n}")
            cl = st.number_input(f"Closing N{n}", key=f"cl{n}")
            diff = max(0.0, cl - o)
            total_l += diff
            # Apply Rate Change math if checked
            total_money += (diff * r2 if is_rate_change else diff * r1)

    st.divider()
    
    # Other Inputs
    col_a, col_b = st.columns(2)
    test_l = col_a.number_input("Test/Maintenance (L)", min_value=0.0)
    st_pur = col_b.number_input("New Stock Load (L)", min_value=0.0)
    
    exp = col_a.number_input("Daily Expenses", min_value=0.0)
    dep = col_b.number_input("Bank Deposit", min_value=0.0)

    # AUTO CALCULATIONS
    actual_sales = total_l - test_l
    new_stock = (prev_stock + st_pur) - total_l
    new_cash = (prev_cash + total_money) - (exp + dep)

    if st.button("🚀 SUBMIT & SYNC ONLINE", use_container_width=True):
        new_entry = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Station": pump,
            "Sales_L": actual_sales,
            "Total_Sales_Value": total_money,
            "Expenses": exp,
            "Bank_Deposit": dep,
            "Cash_Hand": new_cash,
            "Closing_Stock": new_stock,
            "Comments": f"Rate: {r2 if is_rate_change else r1}"
        }])

        # SAFE APPEND: Combine old data with new entry
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        conn.update(worksheet="LPG_Logs", data=updated_df)
        st.success("✅ Success! Online Ledger Updated.")
        st.balloons()

# --- TAB 2: MONTHLY REPORT (HISTORY) ---
with tab2:
    st.header("📊 Transaction History")
    if not df.empty:
        # Show only selected pump history
        view_df = df[df['Station'] == pump].sort_values(by="Date", ascending=False)
        st.dataframe(view_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No data found in 'LPG_Logs' sheet.")
