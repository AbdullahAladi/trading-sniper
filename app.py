import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية وإعدادات المحفظة ---
st.set_page_config(page_title="🛰️ رادار النخبة V39 - مدير المحفظة", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.3rem !important; font-weight: 700 !important; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7d32,#004d40); color: white; }
    </style>
    """, unsafe_allow_html=True)

# إعدادات إدارة المخاطر في القائمة الجانبية
st.sidebar.header("💰 إعدادات المحفظة")
capital = st.sidebar.number_input("إجمالي رأس المال ($)", min_value=1000, value=10000, step=500)
risk_per_trade = st.sidebar.slider("المخاطرة لكل صفقة (%)", 0.5, 5.0, 1.0)
max_loss_usd = capital * (risk_per_trade / 100)

# --- 2. إدارة الذاكرة والتنبيهات ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "الكمية", "الدخول", "الربح المتوقع"])

def send_telegram_manager(ticker, entry, qty, t1, sl, score):
    TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
    CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if TOKEN and CHAT_ID:
        msg = (f"🎯 *توصية الفرص الذكية: #{ticker}*\n"
               f"━━━━━━━━━━━━━━\n"
               f"💰 سعر الدخول: ${entry:.2f}\n"
               f"📦 الكمية المقترحة: {qty} سهم\n"
               f"✅ هدف 1: ${t1:.2f} (تأمين)\n"
               f"🛑 وقف الخسارة: ${sl:.2f}\n"
               f"━━━━━━━━━━━━━━\n"
               f"⚡ القوة: {score:.1f}% | 💸 المخاطرة: ${max_loss_usd:.2f}")
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. المحرك الاستراتيجي المطور ---
st_autorefresh(interval=60 * 1000, key="v39_refresh")
tab1, tab2 = st.tabs(["🛰️ رادار إدارة الصفقات", "📊 سجل المحفظة"])

with tab1:
    st.title("🛰️ رادار النخبة V39")
    st.info(f"🛡️ نظام الحماية نشط: أقصى خسارة مسموح بها لكل صفقة هي **${max_loss_usd:.2f}**")

    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[(df_raw['Last Price'] > 1.0) & (df_raw['Volume'] > 1000000)].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        all_data = yf.download(symbols, period="2d", interval="1m", group_by='ticker', progress=False, prepost=True, threads=True)
        
        results = []
        for ticker in symbols:
            if ticker not in all_data or all_data[ticker].empty: continue
            df_t = all_data[ticker].dropna()
            if len(df_t) < 20: continue
            
            live_p = df_t['Close'].iloc[-1]
            
            # --- حساب إدارة الصفقة ---
            target1 = live_p * 1.02
            stop_loss = live_p * 0.98
            
            # حساب الكمية بناءً على المخاطرة بالدولار
            risk_per_share = live_p - stop_loss
            if risk_per_share > 0:
                shares_to_buy = int(max_loss_usd / risk_per_share)
                expected_profit = shares_to_buy * (target1 - live_p)
            else:
                shares_to_buy = 0; expected_profit = 0

            priority_score = (((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 500) + (df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1) * 20)
            priority_score = min(max(priority_score, 0), 99.9)

            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 88 and last_p is None and shares_to_buy > 0:
                send_telegram_manager(ticker, live_p, shares_to_buy, target1, stop_loss, priority_score)
                st.session_state.alert_prices[ticker] = live_p
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "الكمية": shares_to_buy, "الدخول": round(live_p, 2), "الربح المتوقع": round(expected_profit, 2)}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker, 
                "السعر⚡": f"${live_p:.2f}",
                "الأفضلية %": round(priority_score, 1),
                "الكمية 📦": shares_to_buy,
                "ربح الهدف 💰": f"${expected_profit:.2f}",
                "الهدف 🎯": f"${target1:.2f}",
                "الوقف 🛑": f"${stop_loss:.2f}"
            })

        df_final = pd.DataFrame(results).sort_values(by="الأفضلية %", ascending=False)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=750)
            
    except:
        st.info("🔎 الرادار يحسب أحجام الصفقات بناءً على محفظتك... يرجى الانتظار")

with tab2:
    st.header("📊 سجل إدارة صفقات المحفظة")
    if not st.session_state.performance_log.empty:
        st.table(st.session_state.performance_log)
