import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="LPG Smart Ledger", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- TABS FOR NAVIGATION ---
tab1, tab2 = st.tabs(["📝 Daily Data Entry", "📊 Monthly Reports"])

# --- LOAD DATA FOR CARRY FORWARD ---
try:
    all_data = conn.read(worksheet="LPG_Logs", ttl=0)
except:
    all_data = pd.DataFrame()

# ==========================================
# TAB 1: DAILY DATA ENTRY
# ==========================================
with tab1:
    st.title("⛽ LPG Daily Entry")
    pump_name = st.selectbox("Station", ["Tonoy LPG", "Farida LPG"])
    
    # Carry Forward Logic
    if not all_data.empty:
        station_data = all_data[all_data['Station'] == pump_name]
        prev_cash = float(station_data.iloc[-1]['Cash_Hand']) if not station_data.empty else 0.0
        prev_stock = float(station_data.iloc[-1]['Closing_Stock']) if not station_data.empty else 0.0
    else:
        prev_cash, prev_stock = 0.0, 0.0

    is_rate_change = st.checkbox("🚨 Rate Change Today?")
    
    c_r1, c_r2 = st.columns(2)
    rate1 = c_r1.number_input("Rate 1 (BDT/L)", min_value=0.0)
    rate2 = c_r2.number_input("Rate 2 (New)", min_value=0.0, disabled=not is_rate_change)

    st.subheader("🔢 Nozzle Meters")
    total_sales_l = 0.0
    total_money = 0.0

    for n in range(1, 5):
        with st.expander(f"Nozzle {n}", expanded=(n==1)):
            col1, col2, col3, col4 = st.columns(4)
            op1 = col1.number_input(f"Opening N{n}", key=f"op1_{n}")
            cl1 = col2.number_input(f"Closing (at Rate 1) N{n}", key=f"cl1_{n}")
            
            s1 = max(0.0, cl1 - op1)
            total_sales_l += s1
            total_money += (s1 * rate1)
            
            if is_rate_change:
                op2 = col3.number_input(f"Opening (New Rate) N{n}", key=f"op2_{n}")
                cl2 = col4.number_input(f"Final Closing N{n}", key=f"cl2_{n}")
                s2 = max(0.0, cl2 - op2)
                total_sales_l += s2
                total_money += (s2 * rate2)

    st.divider()
    test_l = st.number_input("Maintenance/Test (L)", min_value=0.0)
    st_pur = st.number_input("New Purchase (L)", min_value=0.0)
    
    # Final Calculations
    closing_stock = (prev_stock + st_pur) - total_sales_l
    expenses = st.number_input("Expenses", min_value=0.0)
    bank_dep = st.number_input("Bank Deposit", min_value=0.0)
    final_cash = (prev_cash + total_money) - (expenses + bank_dep)

    st.metric("Cash in Hand", f"{final_cash:,.2f} BDT")
    
    if st.button("🚀 Submit Report"):
        new_row = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Station": pump_name,
            "Total_L": total_sales_l,
            "Sales_L": total_sales_l - test_l,
            "Total_Sales_Value": total_money,
            "Expenses": expenses,
            "Bank_Deposit": bank_dep,
            "Cash_Hand": final_cash,
            "Closing_Stock": closing_stock,
            "Comments": "Rate Change" if is_rate_change else ""
        }])
        updated = pd.concat([all_data, new_row], ignore_index=True)
        conn.update(worksheet="LPG_Logs", data=updated)
        st.success("✅ Data Saved!")

# ==========================================
# TAB 2: MONTHLY REPORTS
# ==========================================
with tab2:
    st.title("📊 Monthly Reports")
    if not all_data.empty:
        # Filter by Station
        rep_station = st.selectbox("Filter Report By:", ["Tonoy LPG", "Farida LPG"])
        report_df = all_data[all_data['Station'] == rep_station].copy()
        
        # Totals
        c1, c2 = st.columns(2)
        c1.metric("Total Sales (L)", f"{report_df['Sales_L'].sum():,.2f}")
        c2.metric("Total Revenue", f"{report_df['Total_Sales_Value'].sum():,.2f} BDT")
        
        st.dataframe(report_df.sort_values(by="Date", ascending=False), use_container_width=True)
    else:
        st.write("No data available yet.")
