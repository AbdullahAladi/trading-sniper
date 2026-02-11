import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. التنسيق البصري الملكي ---
st.set_page_config(page_title="منصة النخبة - ذكاء السيولة", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "السعر", "بصمة السيولة", "القرار"])

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_smart(msg):
    if TOKEN and CHAT_ID:
        try: url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"; requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. بناء الواجهة والتحديث التلقائي ---
st_autorefresh(interval=60 * 1000, key="v32_refresh")
tab1, tab2 = st.tabs(["🛰️ رادار الأفضلية الذكي", "📊 سجل الجودة والتقارير"])

with tab1:
    st.title("🛰️ رادار النخبة المتوازن")
    st.markdown('<p style="text-align:center;">📡 يتم تحليل "جودة الارتفاع" لحظياً لتمييز التجميع عن التصريف</p>', unsafe_allow_html=True)

    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 15: continue
            
            live_p = df_t['Close'].iloc[-1]
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            
            # --- محرك ذكاء السيولة (المعدل) ---
            mf_raw = (df_t['Close'].diff().tail(5) * df_t['Volume'].tail(5)).sum()
            if mf_raw > 0:
                mf_status = "✅ تجميع"
                bonus = 15 # مكافأة للأسهم التي يجمع فيها المحترفون
            else:
                mf_status = "⚠️ تصريف"
                bonus = -10 # خصم نقاط للأسهم التي ترتفع بدون سيولة حقيقية
            
            priority_score = (mom_15m * 45) + (rel_vol * 35) + bonus
            priority_score = min(max(priority_score, 0), 99.9)

            # --- التنبيه الذكي (انفجار + تجميع حصراً) ---
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 80 and mf_status == "✅ تجميع" and last_p is None:
                send_telegram_smart(f"💎 *انفجار عالي الجودة: #{ticker}*\n💰 السعر: ${live_p:.2f}\n📊 الحالة: تجميع مؤكد\n⚡ القوة: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_p
                # تسجيل السجل
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "السعر": live_p, "بصمة السيولة": mf_status, "القرار": "دخول آمن ✅"}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker,
                "السعر ⚡": f"${live_p:.2f}",
                "قوة الأفضلية %": round(priority_score, 1),
                "بصمة السيولة": mf_status,
                "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 نشط"
            })

        df_final = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=700)
        
    except:
        st.info("🔎 جاري تحليل نبض السوق ومطابقة البيانات... يرجى الانتظار")

with tab2:
    st.header("📊 سجل الأداء الذهبي")
    if not st.session_state.performance_log.empty:
        csv = st.session_state.performance_log.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل سجل الجودة (CSV)", csv, "Elite_Trading_Log.csv", "text/csv")
        st.table(st.session_state.performance_log)
    else:
        st.info("السجل بانتظار أول فرصة تجمع بين 'الانفجار السعري' و 'التجميع الحقيقي'.")
