import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية وإعدادات إدارة المخاطر ---
st.set_page_config(page_title="🛰️ رادار النخبة V43 - الدقة المطلقة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.3rem !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.header("💰 إدارة المحفظة الذكية")
capital = st.sidebar.number_input("إجمالي رأس المال ($)", min_value=1000, value=10000)
risk_usd = st.sidebar.number_input("أقصى خسارة مقبولة للصَفقة ($)", min_value=10, value=100)

# --- 2. معالج البيانات الاحترافي (إصلاح أخطاء KeyError و النوع) ---
def robust_data_processor(file_path):
    try:
        df = pd.read_csv(file_path)
        # البحث عن الأعمدة بغض النظر عن المسمى الدقيق
        col_map = {}
        for col in df.columns:
            if 'Symbol' in col: col_map['Symbol'] = col
            if any(x in col for x in ['Price', 'Last', 'Close']): col_map['Price'] = col
            if 'Volume' in col: col_map['Volume'] = col
        
        df = df.rename(columns=col_map)
        # تنظيف وتحويل قسري للأرقام لضمان صحة الحسابات
        df['Price'] = pd.to_numeric(df['Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        return df.dropna(subset=['Symbol', 'Price'])
    except: return None

# --- 3. المحرك الاستراتيجي ---
st_autorefresh(interval=60 * 1000, key="v43_stable")
st.title("🛰️ رادار النخبة V43")

try:
    df_raw = robust_data_processor('nasdaq_screener_1770731394680.csv')
    if df_raw is not None:
        # فلتر جودة الأسهم (تجنب الأسهم الراكدة)
        watchlist = df_raw[(df_raw['Price'] > 0.5) & (df_raw['Volume'] > 500000)].sort_values(by='Volume', ascending=False).head(35)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات اللحظية (دقة دقيقة واحدة)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True, threads=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 5: continue
            
            live_p = df_t['Close'].iloc[-1]
            
            # --- منطق الأهداف الفولاذي (إصلاح تداخل الأسعار) ---
            # الهدف: +3% ، الوقف: -2.5%
            target_p = live_p * 1.03
            stop_p = live_p * 0.975
            
            # حساب الكمية بناءً على المخاطرة المحددة (Risk Amount)
            risk_per_share = abs(live_p - stop_p)
            qty = int(risk_usd / risk_per_share) if risk_per_share > 0 else 0
            
            # حساب قوة الأفضلية (Score)
            daily_open = df_t['Open'].iloc[0]
            change_from_open = ((live_p - daily_open) / daily_open) * 100
            score = min((abs(change_from_open) * 40) + (qty * 0.05), 99.9)

            results.append({
                "الرمز": ticker, 
                "السعر⚡": f"${live_p:.2f}",
                "قوة الأفضلية %": round(score, 1),
                "الكمية 📦": qty,
                "الهدف 🎯": f"${target_p:.2f}",
                "الوقف 🛑": f"${stop_p:.2f}",
                "الحالة": "🔥 انفجار" if score > 85 else "📈 نشط"
            })

        if results:
            df_final = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
            st.dataframe(df_final, use_container_width=True, hide_index=True, height=750)
        else:
            st.warning("🔎 البيانات مستلمة ولكن لا توجد أسهم تطابق معايير الجودة حالياً.")

except Exception as e:
    st.info("🔎 الرادار يقوم بمزامنة الإحداثيات السعرية... يرجى الانتظار")
