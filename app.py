import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية ---
st.set_page_config(page_title="رادار الانفجار السعري", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .status-bar { background: rgba(0, 255, 204, 0.1); padding: 10px; border-radius: 8px; border: 1px solid #00ffcc; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات ---
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "سعر الدخول", "القوة", "الحالة"])

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_explosion(ticker, price, score):
    """إرسال تنبيه فقط لحالات الانفجار الأسطورية"""
    if TOKEN and CHAT_ID:
        msg = (
            f"🔥 *فرصة أسطورية: انفجار الآن!*\n\n"
            f"🚀 الرمز: #{ticker}\n"
            f"💰 السعر الحالي: ${price:.2f}\n"
            f"⚡ قوة الأفضلية: {score:.1f}%\n"
            f"📊 الحالة: انفجار سيولة وزخم حاد"
        )
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. بناء الواجهة والتحديث ---
st_autorefresh(interval=60 * 1000, key="v23_refresh")
tab1, tab2 = st.tabs(["🛰️ الرادار المباشر", "📊 سجل الأداء والتقارير"])

with tab1:
    st.title("🏹 رادار النخبة")
    st.markdown('<div class="status-bar">📡 الفلتر نشط: يتم إرسال "الانفجارات" فقط إلى التليجرام</div>', unsafe_allow_html=True)

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
            rel_vol = df_t['Volume'].iloc[-1] / df_t['Volume'].mean() if df_t['Volume'].mean() > 0 else 1
            
            # معادلة الأفضلية المطورة
            priority_score = (mom_15m * 60) + (rel_vol * 40)
            priority_score = min(max(priority_score, 0), 99.9)

            # فلتر التليجرام: إرسال الانفجارات فقط (> 80)
            if priority_score >= 80:
                if ticker not in st.session_state.get('last_alerted', {}):
                    send_telegram_explosion(ticker, live_p, priority_score)
                    if 'last_alerted' not in st.session_state: st.session_state.last_alerted = {}
                    st.session_state.last_alerted[ticker] = live_p
                    
                    # تسجيل في لوحة الإحصائيات
                    new_log = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "سعر الدخول": live_p, "القوة": round(priority_score, 1), "الحالة": "🔥 انفجار"}])
                    st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_log], ignore_index=True)

            if priority_score > 5:
                results.append({"الرمز": ticker, "السعر": f"${live_p:.2f}", "الأفضلية %": round(priority_score, 1), "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 صعود"})

        df_display = pd.DataFrame(results).sort_values(by="الأفضلية %", ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    except:
        st.info("🔎 جاري تحليل تدفق السيولة... يرجى الانتظار")

with tab2:
    st.header("📊 سجل الجودة")
    log_df = st.session_state.performance_log
    if not log_df.empty:
        # تصدير Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            log_df.to_excel(writer, index=False)
        st.download_button("📥 تحميل تقرير الإكسل الكامل", output.getvalue(), "Daily_Report.xlsx")
        
        st.table(log_df)
    else:
        st.info("بانتظار حدوث أول 'انفجار سعري' لتسجيل البيانات.")
