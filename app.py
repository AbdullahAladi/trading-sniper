import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. التصميم والتنسيق ---
st.set_page_config(page_title="🛰️ رادار النخبة V34 - السرعة والدقة", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 10px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "السعر", "بصمة السيولة", "RSI"])

def send_telegram_smart(msg):
    TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
    CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if TOKEN and CHAT_ID:
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. المحرك التوربيني والمؤشرات ---
st_autorefresh(interval=60 * 1000, key="v34_refresh")
tab1, tab2 = st.tabs(["🛰️ الرادار الذكي السريع", "📊 سجل الجودة"])

with tab1:
    st.title("🛰️ رادار النخبة V34")
    st.markdown('<div class="ticker-tape">📡 محرك RSI نشط | الجلب الجماعي السريع مفعل | فلتر الانفجارات الذكي</div>', unsafe_allow_html=True)

    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # --- الجلب الجماعي (Multithreading) ---
        all_data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True, threads=True)
        
        results = []
        for ticker in symbols:
            if ticker not in all_data or all_data[ticker].empty: continue
            df_t = all_data[ticker].dropna()
            if len(df_t) < 20: continue
            
            live_p = df_t['Close'].iloc[-1]
            
            # --- حساب RSI (صمام الأمان) ---
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # --- بصمة السيولة ---
            recent_mf = (df_t['Close'].diff().tail(5) * df_t['Volume'].tail(5)).mean()
            mf_status = "✅ تجميع" if recent_mf > 0 else "⚠️ تصريف"
            
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            
            # --- معادلة الأفضلية (مع خصم التضخم) ---
            priority_score = (mom_15m * 40) + (rel_vol * 30) + (20 if recent_mf > 0 else -10)
            if rsi > 75: priority_score -= 25  # خصم نقاط إذا كان السهم متضخماً
            
            priority_score = min(max(priority_score, 0), 99.9)

            # --- التنبيهات الذكية (انفجار + تجميع + RSI سليم) ---
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 80 and mf_status == "✅ تجميع" and rsi < 70 and last_p is None:
                msg = (f"💎 *فرصة عالية الجودة: #{ticker}*\n💰 السعر: ${live_p:.2f}\n⚡ القوة: {priority_score:.1f}%\n📉 RSI: {rsi:.1f}\n📊 السيولة: {mf_status}")
                send_telegram_smart(msg)
                st.session_state.alert_prices[ticker] = live_p
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "السعر": live_p, "بصمة السيولة": mf_status, "RSI": round(rsi, 1)}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker, "السعر⚡": f"${live_p:.2f}",
                "قوة الأفضلية %": round(priority_score, 1),
                "RSI": round(rsi, 1),
                "بصمة السيولة": mf_status,
                "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 صعود"
            })

        df_final = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
        
        avg_mkt = df_final["قوة الأفضلية %"].head(10).mean()
        st.write(f"### 🌡️ مقياس الزخم العام: {avg_mkt:.1f}%")
        st.progress(float(avg_mkt / 100))
        
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=700)
            
    except:
        st.info("🔎 الرادار يمسح السوق بالخيوط المتوازية... يرجى الانتظار ثوانٍ")

with tab2:
    st.header("📊 سجل الجودة التاريخي")
    if not st.session_state.performance_log.empty:
        csv = st.session_state.performance_log.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل سجل النخبة (Excel)", csv, "Report.csv", "text/csv")
        st.table(st.session_state.performance_log)
    else:
        st.info("🔎 بانتظار فرصة تجمع بين (انفجار + تجميع + RSI منخفض).")
