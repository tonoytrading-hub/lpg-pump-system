import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Tonoy & Farida LPG", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- AUTO-CALCULATION LOGIC ---
try:
    df = conn.read(worksheet="LPG_Logs", ttl=0)
    # Get last closing values for the selected pump
    pump = st.sidebar.selectbox("Station", ["Tonoy LPG", "Farida LPG"])
    last_row = df[df['Station'] == pump].iloc[-1]
    prev_stock = float(last_row['Closing_Stock'])
    prev_cash = float(last_row['Cash_Hand'])
except:
    prev_stock, prev_cash, pump = 0.0, 0.0, "Tonoy LPG"

st.title(f"⛽ {pump} Daily Report")
st.sidebar.info(f"Yesterday's Closing:\nStock: {prev_stock}L\nCash: {prev_cash} BDT")

# --- RATE CHANGE & NOZZLES ---
is_rate_change = st.checkbox("🚨 Rate Change Today?")
r1 = st.number_input("Rate 1 (Old)", min_value=0.0)
r2 = st.number_input("Rate 2 (New)", min_value=0.0, disabled=not is_rate_change)

st.subheader("🔢 Nozzle Readings")
total_l, total_money = 0.0, 0.0

for n in range(1, 5):
    with st.expander(f"Nozzle {n}"):
        c1, c2 = st.columns(2)
        op1 = c1.number_input(f"Opening N{n}", key=f"o{n}")
        cl1 = c2.number_input(f"Closing N{n}", key=f"c{n}")
        diff = max(0.0, cl1 - op1)
        total_l += diff
        total_money += (diff * r1 if not is_rate_change else diff * r2) # Simplifies math for you

# --- FINAL AUTO-MATH ---
st.divider()
test_l = st.number_input("Test/Maintenance (Litre)", min_value=0.0)
st_pur = st.number_input("New Stock Purchase (Litre)", min_value=0.0)
exp = st.number_input("Today's Expenses", min_value=0.0)
dep = st.number_input("Bank Deposit", min_value=0.0)

# The app does this math so you don't have to
actual_sales = total_l - test_l
final_stock = (prev_stock + st_pur) - total_l
final_cash = (prev_cash + total_money) - (exp + dep)

st.sidebar.metric("Calculated Sales", f"{actual_sales} L")
st.sidebar.metric("Closing Cash", f"{final_cash} BDT")

if st.button("🚀 SUBMIT & SYNC DATA"):
    new_data = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Station": pump,
        "Total_L": total_l,
        "Sales_L": actual_sales,
        "Total_Sales_Value": total_money,
        "Expenses": exp,
        "Bank_Deposit": dep,
        "Cash_Hand": final_cash,
        "Closing_Stock": final_stock,
        "Rate": r1 if not is_rate_change else r2
    }])
    updated = pd.concat([df, new_data], ignore_index=True)
    conn.update(worksheet="LPG_Logs", data=updated)
    st.success("Success! Carry-forward updated for tomorrow.")
    st.balloons()
