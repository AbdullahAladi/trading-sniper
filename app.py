import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="رادار التنبؤ والأفضلية الذكي", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    .status-bar { background: rgba(0, 255, 204, 0.1); padding: 12px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; font-size: 1.3rem; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات الذكية ---
if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {} 

if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "سعر التنبيه", "تنبؤ الحركة", "الحالة"])

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_priority(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
        except: pass

# --- 3. المحرك المطور (Prediction & Accuracy Engine) ---
st_autorefresh(interval=60 * 1000, key="v25_refresh")

tab1, tab2 = st.tabs(["🛰️ رادار التنبؤ المباشر", "📊 سجل الجودة والأداء"])

with tab1:
    st.title("🛰️ رادار الأفضلية والتنبؤ الذكي")
    st.markdown('<div class="status-bar">📡 المحرك يحلل الآن (السيولة + الزخم + اتجاه الشموع) لتقديم أدق التوقعات</div>', unsafe_allow_html=True)

    try:
        # تحميل البيانات
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(50)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 20: continue
            
            live_p = df_t['Close'].iloc[-1]
            # 1. حساب الزخم (آخر 15 دقيقة)
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            # 2. حساب السيولة النسبية
            rel_vol = df_t['Volume'].iloc[-1] / df_t['Volume'].mean()
            # 3. محرك التنبؤ (تحليل اتجاه آخر 5 شموع)
            price_trend = live_p - df_t['Close'].iloc[-5]
            if price_trend > 0 and rel_vol > 1.5:
                prediction = "🚀 صعود وشيك"
                pred_score = 20 # إضافة نقاط قوة
            elif price_trend <= 0 and rel_vol > 2:
                prediction = "📦 تجميع خفي"
                pred_score = 10
            else:
                prediction = "⚖️ استقرار"
                pred_score = 0
            
            # معادلة الأفضلية النهائية (مع دمج التنبؤ)
            priority_score = (mom_15m * 40) + (rel_vol * 30) + (pred_score * 2) + (abs(((live_p - df_t['Open'].iloc[0])/df_t['Open'].iloc[0])*100) * 10)
            priority_score = min(max(priority_score, 0), 99.9)

            # --- منطق التنبيهات النخبة ---
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 80 and last_p is None:
                msg = (f"🔥 *انفجار وتنبؤ صعود: #{ticker}*\n"
                       f"السعر: ${live_p:.2f}\n"
                       f"التنبؤ: {prediction}\n"
                       f"القوة: {priority_score:.1f}%")
                send_telegram_priority(msg)
                st.session_state.alert_prices[ticker] = live_p
                # تسجيل السجل
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "سعر التنبيه": live_p, "تنبؤ الحركة": prediction, "الحالة": "✅ إشارة انفجار"}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            if priority_score > 5:
                results.append({
                    "الرمز": ticker, 
                    "السعر⚡": f"${live_p:.2f}",
                    "قوة الأفضلية %": round(priority_score, 1),
                    "تنبؤ الحركة": prediction,
                    "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 نشط",
                    "السيولة": f"{rel_vol:.1f}x"
                })

        df_display = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=800)
    except:
        st.info("🔎 جاري تحليل تدفق السيولة ومزامنة التوقعات...")

with tab2:
    st.title("📊 سجل الجودة والتحليل")
    log_df = st.session_state.performance_log
    if not log_df.empty:
        # زر التحميل
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            log_df.to_excel(writer, index=False)
        st.download_button("📥 تحميل تقرير الجودة (Excel)", output.getvalue(), f"Quality_Report_{datetime.now().date()}.xlsx")
        st.table(log_df)
    else:
        st.info("🔎 بانتظار أول إشارة 'انفجار' لتسجيل دقة التنبؤ.")
