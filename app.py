import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="🛰️ رادار النخبة V36.1 - توصية الفرص", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.4rem !important; font-weight: 700 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 10px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات الاستراتيجية ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "الدخول", "الهدف 1", "الهدف 2", "الوقف"])

def send_telegram_strategy(ticker, entry, t1, t2, sl, score):
    TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
    CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if TOKEN and CHAT_ID:
        msg = (f"🎯 *توصية الفرص: #{ticker}*\n"
               f"━━━━━━━━━━━━━━\n"
               f"💰 دخول: ${entry:.2f}\n"
               f"✅ هدف 1: ${t1:.2f} (+1.5%)\n"
               f"🚀 هدف 2: ${t2:.2f} (+3.0%)\n"
               f"🛑 وقف: ${sl:.2f}\n"
               f"━━━━━━━━━━━━━━\n"
               f"⚡ قوة الانفجار: {score:.1f}%")
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. المحرك الاستراتيجي المطور ---
st_autorefresh(interval=60 * 1000, key="v36_1_refresh")
tab1, tab2 = st.tabs(["🛰️ رادار الأهداف الذكية", "📊 سجل العمليات"])

with tab1:
    st.title("🛰️ رادار النخبة V36.1")
    st.markdown('<div class="ticker-tape">📡 نظام "توصية الفرص" نشط | تم تأمين فارق الأهداف بنسبة 1.5% كحد أدنى</div>', unsafe_allow_html=True)

    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        all_data = yf.download(symbols, period="2d", interval="1m", group_by='ticker', progress=False, prepost=True, threads=True)
        
        results = []
        for ticker in symbols:
            if ticker not in all_data or all_data[ticker].empty: continue
            df_t = all_data[ticker].dropna()
            if len(df_t) < 20: continue
            
            live_p = df_t['Close'].iloc[-1]
            daily_high = df_t['High'].max()
            
            # --- نظام الأهداف الذكي (حل مشكلة التطابق) ---
            # نستخدم 1.5% كحد أدنى فوق السعر الحالي أو أعلى سعر يومي لضمان الربحية
            base_reference = max(live_p, daily_high)
            target1 = base_reference * 1.015
            target2 = base_reference * 1.030
            stop_loss = live_p * 0.97 # وقف عند 3%
            
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100 if len(df_t) >= 15 else 0
            
            priority_score = (mom_15m * 50) + (rel_vol * 50)
            priority_score = min(max(priority_score, 0), 99.9)

            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 85 and last_p is None:
                send_telegram_strategy(ticker, live_p, target1, target2, stop_loss, priority_score)
                st.session_state.alert_prices[ticker] = live_p
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "الدخول": round(live_p, 2), "الهدف 1": round(target1, 2), "الهدف 2": round(target2, 2), "الوقف": round(stop_loss, 2)}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker, 
                "السعر⚡": f"${live_p:.2f}",
                "الأفضلية %": round(priority_score, 1),
                "الهدف 1 🎯": f"${target1:.2f}",
                "الهدف 2 🚀": f"${target2:.2f}",
                "الوقف 🛑": f"${stop_loss:.2f}",
                "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 مراقبة"
            })

        df_final = pd.DataFrame(results).sort_values(by="الأفضلية %", ascending=False)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=750)
            
    except:
        st.info("🔎 جاري تحديث رادار الفرص وحساب المستويات الاستراتيجية...")

with tab2:
    st.header("📊 سجل توصيات الفرص")
    if not st.session_state.performance_log.empty:
        st.table(st.session_state.performance_log)
