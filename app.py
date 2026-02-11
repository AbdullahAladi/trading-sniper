import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية ---
st.set_page_config(page_title="🛰️ رادار النخبة V35 - إدارة الأهداف", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.4rem !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "الدخول", "الهدف", "الوقف", "RSI"])

def send_telegram_strategy(ticker, entry, t1, t2, sl, score, rsi):
    TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
    CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if TOKEN and CHAT_ID:
        msg = (f"🎯 *استراتيجية دخول: #{ticker}*\n"
               f"━━━━━━━━━━━━━━\n"
               f"💰 سعر الدخول: ${entry:.2f}\n"
               f"✅ هدف 1: ${t1:.2f}\n"
               f"🚀 هدف 2: ${t2:.2f}\n"
               f"🛑 وقف الخسارة: ${sl:.2f}\n"
               f"━━━━━━━━━━━━━━\n"
               f"⚡ القوة: {score:.1f}% | 📉 RSI: {rsi:.1f}")
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. المحرك الاستراتيجي ---
st_autorefresh(interval=60 * 1000, key="v35_refresh")
tab1, tab2 = st.tabs(["🛰️ رادار الأهداف اللحظي", "📊 سجل الاستراتيجيات"])

with tab1:
    st.title("🛰️ رادار النخبة V35")
    
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        all_data = yf.download(symbols, period="2d", interval="1m", group_by='ticker', progress=False, prepost=True, threads=True)
        
        results = []
        for ticker in symbols:
            if ticker not in all_data or all_data[ticker].empty: continue
            df_t = all_data[ticker].dropna()
            if len(df_t) < 30: continue
            
            live_p = df_t['Close'].iloc[-1]
            
            # --- حساب ATR للهدف والوقف ---
            high_low = df_t['High'] - df_t['Low']
            high_cp = np.abs(df_t['High'] - df_t['Close'].shift())
            low_cp = np.abs(df_t['Low'] - df_t['Close'].shift())
            tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            # مستويات الاستراتيجية
            stop_loss = live_p - (atr * 1.5)
            target1 = live_p + (atr * 2)
            target2 = live_p + (atr * 4)
            
            # مؤشر RSI
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / (loss + 1e-9)))).iloc[-1]
            
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            
            priority_score = (mom_15m * 40) + (rel_vol * 30) - (20 if rsi > 75 else 0)
            priority_score = min(max(priority_score, 0), 99.9)

            # التنبيهات مع قاعدة الـ 5% والاهداف
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 80 and rsi < 72 and last_p is None:
                send_telegram_strategy(ticker, live_p, target1, target2, stop_loss, priority_score, rsi)
                st.session_state.alert_prices[ticker] = live_p
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "الدخول": round(live_p, 2), "الهدف": round(target1, 2), "الوقف": round(stop_loss, 2), "RSI": round(rsi, 1)}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker, "السعر⚡": f"${live_p:.2f}",
                "الأفضلية %": round(priority_score, 1),
                "الهدف 🎯": f"${target1:.2f}",
                "الوقف 🛑": f"${stop_loss:.2f}",
                "RSI": round(rsi, 1),
                "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 مراقبة"
            })

        df_final = pd.DataFrame(results).sort_values(by="الأفضلية %", ascending=False)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=750)
            
    except:
        st.info("🔎 الرادار يحسب مستويات الدخول والأهداف الآن...")

with tab2:
    st.header("📊 سجل الصفقات المنفذة")
    if not st.session_state.performance_log.empty:
        st.table(st.session_state.performance_log)
