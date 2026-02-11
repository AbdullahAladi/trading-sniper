import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية وإعدادات المخاطر ---
st.set_page_config(page_title="🛰️ رادار النخبة V42.1 - التصحيح النهائي", layout="wide")
st.sidebar.header("💰 إدارة المحفظة")
capital = st.sidebar.number_input("رأس المال ($)", min_value=1000, value=10000)
risk_usd = st.sidebar.number_input("أقصى خسارة للصفقة ($)", min_value=10, value=100)

# --- 2. معالج البيانات (إصلاح أخطاء str و KeyError) ---
def robust_load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        col_map = {col: 'Symbol' if 'Symbol' in col else 'Price' if any(x in col for x in ['Price', 'Last', 'Close']) else 'Volume' if 'Volume' in col else col for col in df.columns}
        df = df.rename(columns=col_map)
        df['Price'] = pd.to_numeric(df['Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        return df.dropna(subset=['Symbol', 'Price'])
    except: return None

# --- 3. المحرك المصحح ---
st_autorefresh(interval=60 * 1000, key="v42_1_fix")
st.title("🛰️ رادار النخبة V42.1")

try:
    df_raw = robust_load_data('nasdaq_screener_1770731394680.csv')
    if df_raw is not None:
        watchlist = df_raw[(df_raw['Price'] > 0.5)].sort_values(by='Volume', ascending=False).head(30)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            live_p = df_t['Close'].iloc[-1]
            
            # --- التصحيح الاستراتيجي الحاسم ---
            t1 = live_p * 1.03  # الهدف (سعر الدخول + 3%)
            sl = live_p * 0.97  # الوقف (سعر الدخول - 3%)
            
            qty = int(risk_usd / (live_p - sl)) if (live_p - sl) > 0 else 0
            score = min((((live_p - df_t['Open'].iloc[0])/df_t['Open'].iloc[0])*400) + 20, 99.9)

            results.append({
                "الرمز": ticker, "السعر⚡": f"${live_p:.2f}",
                "قوة الأفضلية %": round(score, 1),
                "الكمية 📦": qty,
                "الهدف 🎯": f"${t1:.2f}",  # تأكيد رياضي: دائماً أكبر من السعر
                "الوقف 🛑": f"${sl:.2f}"    # تأكيد رياضي: دائماً أصغر من السعر
            })

        st.dataframe(pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False), use_container_width=True, hide_index=True)
except:
    st.info("🔎 الرادار يعالج إحداثيات الأهداف... يرجى الانتظار")
