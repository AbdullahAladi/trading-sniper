import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية ---
st.set_page_config(page_title="🛰️ استرداد رادار النخبة", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #050505; color: #00ffcc; }
    h1 { text-align: center; text-shadow: 0 0 10px #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. معالج البيانات الفولاذي (لحل مشكلة الشاشة السوداء) ---
def emergency_data_loader(file_path):
    try:
        df = pd.read_csv(file_path)
        # البحث الذكي عن الأعمدة بغض النظر عن أسمائها في الملف
        col_map = {}
        for col in df.columns:
            if 'Symbol' in col: col_map['Symbol'] = col
            if any(x in col for x in ['Price', 'Last', 'Close']): col_map['Price'] = col
            if 'Volume' in col: col_map['Volume'] = col
        
        df = df.rename(columns=col_map)
        # تحويل البيانات إلى أرقام حصراً (إصلاح خطأ str vs float)
        df['Price'] = pd.to_numeric(df['Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        return df.dropna(subset=['Symbol', 'Price'])
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الملف: {e}")
        return None

# --- 3. المحرك ---
st_autorefresh(interval=30 * 1000, key="v44_emergency")
st.title("🛰️ رادار النخبة - استعادة البيانات")

try:
    df_raw = emergency_data_loader('nasdaq_screener_1770731394680.csv')
    
    if df_raw is not None:
        # تقليل القيود لضمان ظهور نتائج (سعر > 0.1$ وسيولة > 50 ألف)
        watchlist = df_raw[(df_raw['Price'] > 0.1) & (df_raw['Volume'] > 50000)].head(20)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات (Threads مفعل للسرعة)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True, threads=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 1: continue
            
            live_p = df_t['Close'].iloc[-1]
            
            # حساب الأهداف (تأكيد رياضي: الهدف > السعر ، الوقف < السعر)
            t1 = live_p * 1.03
            sl = live_p * 0.97
            
            results.append({
                "الرمز": ticker,
                "السعر⚡": f"${live_p:.2f}",
                "الهدف 🎯": f"${t1:.2f}",
                "الوقف 🛑": f"${sl:.2f}",
                "الحالة": "✅ متصل"
            })

        if results:
            st.success(f"🚀 تم استرداد البيانات! الرادار يراقب {len(results)} سهم الآن.")
            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        else:
            st.warning("🔎 الملف سليم ولكن لم يتم استلام بيانات حية من Yahoo Finance. تأكد من اتصال الإنترنت.")
    else:
        st.error("❌ فشل تحميل الملف. تأكد من وجود nasdaq_screener_1770731394680.csv")

except Exception as e:
    st.info("🔎 الرادار يعيد بناء جسور البيانات... يرجى الانتظار ثوانٍ.")
