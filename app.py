import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. التنسيق البصري ---
st.set_page_config(page_title="رادار الدقة المطلقة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; }
    .stDataFrame div { font-size: 1.6rem !important; font-weight: 700 !important; }
    .live-indicator { background: rgba(0, 255, 204, 0.1); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. نظام التنبيهات الذكي ---
TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {} 

def send_telegram_msg(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=10)
        except: pass

# --- 3. محرك الدقة الفائقة (Real-Time Pre-Market Engine) ---
st_autorefresh(interval=30 * 1000, key="v17_refresh") # تقليل وقت التحديث لـ 30 ثانية لزيادة الدقة

def get_real_time_data():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 300000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        results = []
        # جلب البيانات لكل سهم على حدة لضمان الدقة (Fast Info Access)
        for ticker in symbols:
            t_obj = yf.Ticker(ticker)
            
            # جلب بيانات تاريخية دقيقة جداً (دقيقة واحدة) تشمل التداول المسبق
            hist = t_obj.history(period="1d", interval="1m", prepost=True)
            
            if hist.empty: continue
            
            # السعر الفعلي الآن (Last Traded Price)
            live_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else live_price
            
            # حساب التغير اللحظي الفعلي
            momentum_10m = ((live_price - hist['Close'].iloc[-10]) / hist['Close'].iloc[-10]) * 100 if len(hist) > 10 else 0
            
            # حساب السيولة اللحظية
            vol_now = hist['Volume'].iloc[-1]
            rel_vol = vol_now / hist['Volume'].mean() if not hist['Volume'].mean() == 0 else 1

            # معادلة الأفضلية (وزن هائل للتغير اللحظي)
            priority_score = (momentum_10m * 60) + (rel_vol * 40)
            priority_score = min(max(priority_score, 0), 99.9)

            # منطق التنبيه (قاعدة الـ 5% بناءً على السعر الحقيقي الجديد)
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score > 70 and last_p is None:
                send_telegram_msg(f"🎯 *سعر حي ومباشر: #{ticker}*\nالسعر الآن: ${live_price:.2f}\nالزخم: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_price
            elif last_p is not None:
                if abs((live_price - last_p) / last_p) * 100 >= 5.0:
                    send_telegram_msg(f"⚠️ *تغير 5% حقيقي: #{ticker}*\nالسعر الجديد: ${live_price:.2f}")
                    st.session_state.alert_prices[ticker] = live_price

            results.append({
                "الرمز": ticker,
                "السعر المباشر ⚡": f"${live_price:.2f}",
                "قوة الأفضلية %": round(priority_score, 1),
                "تغير 10 دقائق": f"{momentum_10m:+.2f}%",
                "الحالة": "🔥 انفجار لحظي" if momentum_1h > 80 else "📈 نشاط ما قبل الافتتاح",
                "السيولة": f"{rel_vol:.1f}x"
            })
            
        return pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
    except: return pd.DataFrame()

# --- 4. العرض ---
st.title("🏹 رادار الدقة المطلقة والسعر اللحظي")

st.markdown("""
<div class="live-indicator">
    🔴 البث المباشر نشط | الرادار يجلب الآن أسعار "التداول المسبق" بدقة دقيقة واحدة | التحديث كل 30 ثانية
</div>
""", unsafe_allow_html=True)

df_final = get_real_time_data()

if not df_final.empty:
    st.dataframe(df_final, use_container_width=True, hide_index=True, height=800)
else:
    st.info("🔎 جاري مطابقة الأسعار مع السوق العالمي... يرجى الانتظار")
