import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. التنسيق البصري ---
st.set_page_config(page_title="رادار الأفضلية - نسخة الاستقرار", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة ---
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "سعر التنبيه", "تنبؤ الحركة", "الحالة"])
if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {}

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_priority(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. المحرك المطور المستقر ---
st_autorefresh(interval=45 * 1000, key="v25_1_refresh")
tab1, tab2 = st.tabs(["🛰️ الرادار المباشر", "📊 سجل الجودة"])

with tab1:
    st.title("🛰️ رادار الأفضلية والتنبؤ")
    
    try:
        # تقليل العدد لضمان سرعة التحميل وظهور النتائج
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 1000000].sort_values(by='Volume', ascending=False).head(30)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 10: continue
            
            live_p = df_t['Close'].iloc[-1]
            mom_15m = ((live_p - df_t['Close'].iloc[-10]) / df_t['Close'].iloc[-10]) * 100
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            
            # --- منطق تنبؤ الحركة البسيط والدقيق ---
            trend = live_p - df_t['Close'].iloc[-3]
            if trend > 0 and rel_vol > 1.2:
                prediction = "🚀 صعود وشيك"
                score_extra = 15
            elif rel_vol > 2:
                prediction = "📦 تجميع خفي"
                score_extra = 10
            else:
                prediction = "⚖️ استقرار"
                score_extra = 0
            
            priority_score = (mom_15m * 40) + (rel_vol * 30) + score_extra
            priority_score = min(max(priority_score, 0), 99.9)

            # التنبيهات (قاعدة الـ 5% + انفجار)
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 80 and last_p is None:
                send_telegram_priority(f"🔥 *انفجار وتنبؤ: #{ticker}*\nالسعر: ${live_p:.2f}\nالتنبؤ: {prediction}")
                st.session_state.alert_prices[ticker] = live_p
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "سعر التنبيه": live_p, "تنبؤ الحركة": prediction, "الحالة": "✅ إشارة حية"}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker, 
                "السعر⚡": f"${live_p:.2f}",
                "قوة الأفضلية %": round(priority_score, 1),
                "تنبؤ الحركة": prediction,
                "السيولة": f"{rel_vol:.1f}x"
            })

        if results:
            df_display = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
            st.dataframe(df_display, use_container_width=True, hide_index=True, height=700)
        else:
            st.warning("🔎 لا توجد أسهم تحقق شروط النشاط حالياً.. الرادار يستمر في المسح")
            
    except Exception as e:
        st.info("🔎 جاري جلب الأسعار المباشرة من السوق الأمريكي... يرجى الانتظار ثوانٍ.")

with tab2:
    st.title("📊 سجل الجودة")
    if not st.session_state.performance_log.empty:
        csv = st.session_state.performance_log.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل التقرير (CSV/Excel)", csv, "Trading_Report.csv", "text/csv")
        st.table(st.session_state.performance_log)
    else:
        st.info("السجل فارغ. سيتم تسجيل أول 'انفجار' هنا آلياً.")
