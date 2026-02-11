import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية ---
st.set_page_config(page_title="🛰️ فحص رادار النخبة", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #050505; color: #f0f0f0; }
    h1 { color: #00ffcc !important; text-align: center; text-shadow: 0 0 10px #00ffcc; }
    .stDataFrame div { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "السعر", "الهدف"])

# --- 3. المحرك (نسخة الاختبار) ---
st_autorefresh(interval=30 * 1000, key="v40_test")

st.title("🛰️ فحص تشغيل رادار النخبة")
st.sidebar.header("⚙️ إعدادات الفحص")
min_price = st.sidebar.slider("الحد الأدنى للسعر ($)", 0.0, 10.0, 0.5)

try:
    # جلب القائمة
    df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
    # فلتر مخفف للاختبار: أي سهم فوق السعر المختار وبسيولة معقولة
    watchlist = df_raw[(df_raw['Last Price'] >= min_price) & (df_raw['Volume'] > 100000)].sort_values(by='Volume', ascending=False).head(30)
    symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
    
    # جلب البيانات (تفعيل prepost=True لضمان ظهور نتائج في أي وقت)
    data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
    
    results = []
    for ticker in symbols:
        if ticker not in data or data[ticker].empty: continue
        df_t = data[ticker].dropna()
        if len(df_t) < 5: continue
        
        current_p = df_t['Close'].iloc[-1]
        vol_now = df_t['Volume'].iloc[-1]
        
        # حساب بسيط للأفضلية للتأكد من عمل المعادلة
        change = ((current_p - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
        score = (abs(change) * 20) + (vol_now / (df_t['Volume'].mean() + 1) * 10)
        score = min(score, 99.9)
        
        results.append({
            "الرمز": ticker,
            "السعر المباشر⚡": f"${current_p:.2f}",
            "التغير اليومي %": f"{change:+.2f}%",
            "قوة الإشارة %": round(score, 1),
            "الحالة": "✅ نشط" if score > 10 else "💤 خامل"
        })

    if results:
        df_final = pd.DataFrame(results).sort_values(by="قوة الإشارة %", ascending=False)
        st.success(f"✅ تم رصد {len(df_final)} سهم بنجاح!")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ لا توجد بيانات كافية حالياً. جرب تقليل 'الحد الأدنى للسعر' من القائمة الجانبية.")

except Exception as e:
    st.error(f"❌ حدث خطأ في جلب البيانات: {e}")
    st.info("تأكد من وجود ملف 'nasdaq_screener_1770731394680.csv' في نفس المجلد.")
