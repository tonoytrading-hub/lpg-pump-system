import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Tonoy & Farida LPG", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("⛽ LPG 24h Daily Report")
pump_name = st.selectbox("Select Station", ["Tonoy LPG", "Farida LPG"])

menu = ["Daily Entry", "Monthly Reports"]
choice = st.sidebar.radio("Navigation", menu)

if choice == "Daily Entry":
    st.header(f"Data Entry: {pump_name}")
    rate = st.number_input("Selling Rate (BDT/L)", min_value=0.0, step=0.1)

    st.subheader("🔢 Nozzle Meters")
    total_meter_l = 0.0
    for n in range(1, 5):
        with st.expander(f"Nozzle {n}", expanded=(n==1)):
            c1, c2 = st.columns(2)
            op = c1.number_input(f"Opening N{n}", min_value=0.0, key=f"op{n}")
            cl = c2.number_input(f"Closing N{n}", min_value=0.0, key=f"cl{n}")
            total_meter_l += max(0.0, cl - op)

    # MAINTENANCE / TEST BOX
    st.subheader("🛠️ Maintenance & Testing")
    test_l = st.number_input("Litre used for Testing", min_value=0.0)
    
    # CALCULATED SALES
    actual_sales_l = max(0.0, total_meter_l - test_l)
    total_cash_sales = actual_sales_l * rate
    
    col1, col2 = st.columns(2)
    col1.metric("Meter Total (L)", f"{total_meter_l:,.2f}")
    col2.metric("Actual Sales (L)", f"{actual_sales_l:,.2f}")

    st.header("💰 Cash & Expenses")
    cash_cf = st.number_input("Cash C/F (Yesterday)", min_value=0.0)
    expenses = st.number_input("Today's Expenses", min_value=0.0)
    bank_dep = st.number_input("Bank Deposit", min_value=0.0)
    
    cash_in_hand = (cash_cf + total_cash_sales) - (expenses + bank_dep)
    st.metric("Total Cash Sales", f"{total_cash_sales:,.2f} BDT")
    st.metric("Final Cash in Hand", f"{cash_in_hand:,.2f} BDT")

    st.header("📝 Notes")
    user_comments = st.text_area("Add comments (Optional)")

    if st.button(f"🚀 Submit {pump_name} Report", use_container_width=True):
        try:
            # 1. READ existing data
            df = conn.read(worksheet="LPG_Logs", ttl=0)
            
            # 2. CREATE the new row
            new_row = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Month": datetime.now().strftime("%Y-%m"),
                "Station": pump_name,
                "Total_L": total_meter_l,
                "Sales_L": actual_sales_l,
                "Test_L": test_l,
                "Total_Sales": total_cash_sales,
                "Expenses": expenses,
                "Bank_Deposit": bank_dep,
                "Cash_Hand": cash_in_hand,
                "Comments": user_comments
            }])
            
            # 3. COMBINE and UPDATE
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="LPG_Logs", data=updated_df)
            
            st.success("✅ Success! Data synced to Google Sheets.")
            st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")

elif choice == "Monthly Reports":
    st.header(f"📊 {pump_name} Monthly Summary")
    df = conn.read(worksheet="LPG_Logs", ttl=0)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        m_df = df[(df['Station'] == pump_name) & (df['Month'] == datetime.now().strftime("%Y-%m"))]
        st.metric("Mtd Sales (L)", f"{m_df['Sales_L'].sum():,.2f}")
        st.metric("Mtd Revenue", f"{m_df['Total_Sales'].sum():,.2f} BDT")
        st.dataframe(m_df)
