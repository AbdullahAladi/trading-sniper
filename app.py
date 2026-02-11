import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="🛰️ رادار النخبة V37 - حماية الأرباح", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.4rem !important; font-weight: 700 !important; }
    .status-bar { background: rgba(0, 255, 204, 0.1); padding: 10px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات الاستراتيجية ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "الدخول", "الهدف 1", "الوقف المتحرك"])

def send_telegram_strategy(ticker, entry, t1, t2, sl, score):
    TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
    CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if TOKEN and CHAT_ID:
        msg = (f"🎯 *توصية الفرص: #{ticker}*\n"
               f"━━━━━━━━━━━━━━\n"
               f"💰 سعر الدخول: ${entry:.2f}\n"
               f"✅ هدف 1: ${t1:.2f} (تأمين الربح)\n"
               f"🚀 هدف 2: ${t2:.2f} (انفجار)\n"
               f"🛑 وقف متحرك: ${sl:.2f}\n"
               f"━━━━━━━━━━━━━━\n"
               f"⚠️ تم استبعاد الأسهم تحت $1 لضمان الجودة")
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. المحرك الاستراتيجي المطور ---
st_autorefresh(interval=60 * 1000, key="v37_refresh")
tab1, tab2 = st.tabs(["🛰️ رادار الفرص الذكي", "📊 سجل النخبة"])

with tab1:
    st.title("🛰️ رادار النخبة V37")
    st.markdown('<div class="status-bar">📡 فلتر جودة الأسعار نشط (> $1) | نظام الوقف المتحرك مفعل</div>', unsafe_allow_html=True)

    try:
        # قراءة الملف مع تطبيق فلاتر الجودة قبل البدء
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # فلترة: السعر > 1 دولار والسيولة > مليون سهم لضمان الجودة
        watchlist = df_raw[(df_raw['Last Price'] > 1.0) & (df_raw['Volume'] > 1000000)].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # الجلب الجماعي السريع
        all_data = yf.download(symbols, period="2d", interval="1m", group_by='ticker', progress=False, prepost=True, threads=True)
        
        results = []
        for ticker in symbols:
            if ticker not in all_data or all_data[ticker].empty: continue
            df_t = all_data[ticker].dropna()
            if len(df_t) < 20: continue
            
            live_p = df_t['Close'].iloc[-1]
            daily_high = df_t['High'].max()
            
            # --- نظام الأهداف والوقف المتحرك الذكي ---
            target1 = live_p * 1.02  # هدف 1 عند 2%
            target2 = live_p * 1.05  # هدف 2 عند 5%
            
            # الوقف المتحرك: إذا حقق السهم 1% صعوداً من السعر الحالي، يرتفع الوقف لسعر الدخول تلقائياً
            initial_sl = live_p * 0.97
            is_profit_secured = (live_p >= live_p * 1.01)
            trailing_sl = live_p if is_profit_secured else initial_sl
            
            # حساب الأفضلية
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100 if len(df_t) >= 15 else 0
            
            priority_score = (mom_15m * 50) + (rel_vol * 50)
            priority_score = min(max(priority_score, 0), 99.9)

            # إرسال التنبيهات (تم رفع المعيار لـ 88% لضمان جودة استثنائية)
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 88 and last_p is None:
                send_telegram_strategy(ticker, live_p, target1, target2, trailing_sl, priority_score)
                st.session_state.alert_prices[ticker] = live_p
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "الدخول": round(live_p, 2), "الهدف 1": round(target1, 2), "الوقف المتحرك": round(trailing_sl, 2)}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker, 
                "السعر⚡": f"${live_p:.2f}",
                "الأفضلية %": round(priority_score, 1),
                "هدف 1 ✅": f"${target1:.2f}",
                "الوقف 🛑": f"${trailing_sl:.2f}",
                "الحالة": "🔥 انفجار" if priority_score > 85 else "📈 مراقبة"
            })

        if results:
            df_final = pd.DataFrame(results).sort_values(by="الأفضلية %", ascending=False)
            st.dataframe(df_final, use_container_width=True, hide_index=True, height=750)
        else:
            st.warning("🔎 لا توجد أسهم تحقق معايير الجودة حالياً (سعر > $1 وسيولة عالية).")
            
    except Exception as e:
        st.info("🔎 الرادار يطبق فلاتر الجودة ويحسب الوقف المتحرك... يرجى الانتظار ثوانٍ.")

with tab2:
    st.header("📊 سجل التوصيات الذهبية")
    if not st.session_state.performance_log.empty:
        st.table(st.session_state.performance_log)
    else:
        st.info("🔎 بانتظار صيد أول فرصة تجمع بين 'الانفجار السعري' ومعايير النخبة.")
