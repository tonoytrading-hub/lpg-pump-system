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

st.write(f"**Date:** {datetime.now().strftime('%d %b, %Y')}")

menu = ["Daily Entry", "Monthly Reports"]
choice = st.sidebar.radio("Navigation", menu)

# --- 1. DAILY ENTRY ---
if choice == "Daily Entry":
    st.header(f"Data Entry: {pump_name}")
    rate = st.number_input("Selling Rate (BDT/L)", min_value=0.0, step=0.1, format="%.2f")

    # Nozzle Readings
    st.subheader("🔢 Nozzle Meters")
    total_l_sold = 0.0
    for n in range(1, 5):
        with st.expander(f"Nozzle {n}", expanded=(n==1)):
            c1, c2 = st.columns(2)
            op = c1.number_input(f"Opening N{n}", min_value=0.0, key=f"op{n}")
            cl = c2.number_input(f"Closing N{n}", min_value=0.0, key=f"cl{n}")
            total_l_sold += max(0, cl - op)

    # Cash Management
    st.header("💰 Cash & Expenses")
    total_cash_sales = total_l_sold * rate
    cash_cf = st.number_input("Cash C/F (Yesterday)", min_value=0.0)
    expenses = st.number_input("Today's Expenses", min_value=0.0)
    bank_dep = st.number_input("Bank Deposit", min_value=0.0)
    
    cash_in_hand = (cash_cf + total_cash_sales) - (expenses + bank_dep)
    st.metric("Total Sales", f"{total_cash_sales:,.2f} BDT")
    st.metric("Cash in Hand", f"{cash_in_hand:,.2f} BDT")

    # Stock (Simplified)
    st.header("🛢️ Tank Stock")
    st_op = st.number_input("Opening Stock (L)", min_value=0.0)
    st_pur = st.number_input("Purchases (L)", min_value=0.0)
    st_cl = (st_op + st_pur) - total_l_sold
    st.metric("Calculated Closing Stock", f"{st_cl:,.2f} L")

    if st.button(f"🚀 Submit {pump_name} Report", use_container_width=True):
        new_data = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Month": datetime.now().strftime("%Y-%m"),
            "Station": pump_name,
            "Total_L": total_l_sold,
            "Total_Sales": total_cash_sales,
            "Expenses": expenses,
            "Bank_Deposit": bank_dep,
            "Cash_Hand": cash_in_hand,
            "Closing_Stock": st_cl
        }])
        existing = conn.read(worksheet="LPG_Logs")
        updated = pd.concat([existing, new_data], ignore_index=True)
        conn.update(worksheet="LPG_Logs", data=updated)
        st.success("Synced to Cloud!")

# --- 2. MONTHLY REPORTS ---
elif choice == "Monthly Reports":
    st.header(f"📊 {pump_name} Monthly Summary")
    df = conn.read(worksheet="LPG_Logs")
    
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        # Filter by selected pump
        df = df[df['Station'] == pump_name]
        
        current_month = datetime.now().strftime("%Y-%m")
        m_df = df[df['Month'] == current_month]
        
        col1, col2 = st.columns(2)
        col1.metric("Mtd Sales (BDT)", f"{m_df['Total_Sales'].sum():,.2f}")
        col2.metric("Mtd Bank Deposits", f"{m_df['Bank_Deposit'].sum():,.2f}")
        
        st.metric("Mtd Total Expenses", f"{m_df['Expenses'].sum():,.2f}")
        
        st.subheader("Daily History (This Month)")
        st.dataframe(m_df[['Date', 'Total_L', 'Total_Sales', 'Expenses', 'Bank_Deposit']], use_container_width=True)
    else:
        st.info("No data found in Google Sheets.")
