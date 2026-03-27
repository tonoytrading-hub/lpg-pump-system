import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="LPG Smart Ledger", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. AUTOMATIC CARRY FORWARD ---
try:
    # Read last 5 rows to find the most recent data for this station
    all_data = conn.read(worksheet="LPG_Logs", ttl=0)
    last_entry = all_data[all_data['Station'] == st.session_state.get('pump', 'Tonoy LPG')].iloc[-1]
    prev_cash = last_entry['Cash_Hand']
    prev_stock = last_entry['Closing_Stock']
except:
    prev_cash = 0.0
    prev_stock = 0.0

st.title("⛽ LPG 24h Daily Report")
pump_name = st.selectbox("Select Station", ["Tonoy LPG", "Farida LPG"], key='pump')

# --- 2. RATE CHANGE LOGIC ---
st.sidebar.header("Settings")
is_rate_change = st.sidebar.checkbox("Is there a Rate Change today?")

st.header(f"Data Entry: {pump_name}")
col_r1, col_r2 = st.columns(2)
rate1 = col_r1.number_input("Current Selling Rate (BDT/L)", min_value=0.0)
rate2 = col_r2.number_input("New Rate (If changed)", min_value=0.0, disabled=not is_rate_change)

# --- 3. NOZZLE CALCULATIONS ---
st.subheader("🔢 Nozzle Meters")
total_sales_l = 0.0
total_money = 0.0

for n in range(1, 5):
    with st.expander(f"Nozzle {n}", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        op1 = c1.number_input(f"Opening N{n}", min_value=0.0, key=f"op1_{n}")
        cl1 = c2.number_input(f"Closing N{n} (at old rate)", min_value=0.0, key=f"cl1_{n}")
        
        # Calculate Shift 1
        s1_l = max(0.0, cl1 - op1)
        total_sales_l += s1_l
        total_money += (s1_l * rate1)
        
        if is_rate_change:
            op2 = c3.number_input(f"Opening N{n} (new rate)", min_value=cl1, key=f"op2_{n}")
            cl2 = c4.number_input(f"Final Closing N{n}", min_value=op2, key=f"cl2_{n}")
            s2_l = max(0.0, cl2 - op2)
            total_sales_l += s2_l
            total_money += (s2_l * rate2)

# --- 4. MAINTENANCE & STOCK ---
st.subheader("🛠️ Maintenance & Stock")
test_l = st.number_input("Litre used for Testing", min_value=0.0)
actual_sold_l = max(0.0, total_sales_l - test_l)

st.write(f"**Yesterday's Closing Stock:** {prev_stock} L")
st_pur = st.number_input("New Purchase/Load (L)", min_value=0.0)
closing_stock = (prev_stock + st_pur) - total_sales_l

# --- 5. CASH FLOW ---
st.header("💰 Cash Position")
st.write(f"**Cash Brought Forward:** {prev_cash} BDT")
expenses = st.number_input("Today's Expenses", min_value=0.0)
bank_dep = st.number_input("Bank Deposit", min_value=0.0)
final_cash = (prev_cash + total_money) - (expenses + bank_dep)

st.metric("Final Cash in Hand", f"{final_cash:,.2f} BDT")
st.metric("Closing Stock", f"{closing_stock:,.2f} L")

if st.button("🚀 Submit Final Report"):
    new_data = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Station": pump_name,
        "Total_L": total_sales_l,
        "Sales_L": actual_sold_l,
        "Total_Sales_Value": total_money,
        "Expenses": expenses,
        "Bank_Deposit": bank_dep,
        "Cash_Hand": final_cash,
        "Closing_Stock": closing_stock,
        "Comments": f"Rate Change Day" if is_rate_change else ""
    }])
    
    # Append to Sheet
    all_data = conn.read(worksheet="LPG_Logs", ttl=0)
    updated = pd.concat([all_data, new_data], ignore_index=True)
    conn.update(worksheet="LPG_Logs", data=updated)
    st.success("Data synced and Carry-Forward updated!")
    st.balloons()
