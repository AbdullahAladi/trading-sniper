import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية (نفس هيكلك المفضل) ---
st.set_page_config(page_title="منصة الفرص الأسطورية - النسخة الاحترافية", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.2rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; margin-top: -20px; }
    .stDataFrame div { font-size: 1.6rem !important; font-weight: 700 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات الذكية ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "سعر التنبيه", "بصمة السيولة", "درجة الثقة"])

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_priority(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
        except: pass

# --- 3. بناء الواجهة (Tabs) ---
st_autorefresh(interval=60 * 1000, key="v31_refresh")
tab1, tab2 = st.tabs(["🛰️ الرادار المباشر", "📊 لوحة التحكم والتقارير"])

with tab1:
    st.title("🛰️ رادار الأفضلية والزخم")
    st.markdown('<div class="ticker-tape">📡 تحليل بصمة السيولة نشط | التنبيهات للانفجارات (>80) وقاعدة الـ 5%</div>', unsafe_allow_html=True)

    try:
        # جلب البيانات الأساسية
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات اللحظية (Live Accuracy)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 15: continue
            
            live_price = df_t['Close'].iloc[-1]
            mom_15m = ((live_price - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            daily_change = ((live_price - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            # --- إضافة مميزات العمق (بصمة السيولة) ---
            mf_raw = (df_t['Close'].diff().tail(5) * df_t['Volume'].tail(5)).sum()
            mf_status = "✅ تجميع" if mf_raw > 0 else "🛑 تصريف"
            confidence = "High" if rel_vol > 2 and mf_raw > 0 else "Medium"
            
            # معادلة الأفضلية المطورة (دمج التجميع)
            priority_score = (mom_15m * 45) + (rel_vol * 30) + (abs(daily_change) * 15) + (10 if mf_raw > 0 else 0)
            priority_score = min(max(priority_score, 0), 99.9)

            # --- منطق التنبيهات (انفجار + 5%) ---
            last_alert_price = st.session_state.alert_prices.get(ticker)
            should_send = False
            msg_type = ""

            if priority_score >= 80 and last_alert_price is None:
                should_send = True; msg_type = "🔥 انفجار أسطوري"
            elif last_alert_price is not None:
                price_diff = ((live_price - last_alert_price) / last_alert_price) * 100
                if abs(price_diff) >= 5.0:
                    should_send = True; msg_type = f"⚠️ تحرك حي ({price_diff:+.1f}%)"

            if should_send:
                msg = (f"🎯 *تنبيه النخبة: #{ticker}*\n"
                       f"الحالة: {msg_type}\n"
                       f"السعر: ${live_price:.2f} | السيولة: {mf_status}")
                send_telegram_priority(msg)
                st.session_state.alert_prices[ticker] = live_price
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "سعر التنبيه": live_price, "بصمة السيولة": mf_status, "درجة الثقة": confidence}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker, "السعر⚡": f"${live_price:.2f}",
                "قوة الأفضلية %": round(priority_score, 1),
                "بصمة السيولة": mf_status,
                "درجة الثقة": confidence,
                "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 نشط"
            })

        if results:
            df_display = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
            
            # ميزة التميز البصري: مقياس السوق
            avg_mkt = df_display["قوة الأفضلية %"].head(10).mean()
            st.write(f"### 🌡️ مقياس قوة الزخم الحالي: {avg_mkt:.1f}%")
            st.progress(float(avg_mkt / 100))
            
            st.dataframe(df_display, use_container_width=True, hide_index=True, height=750)
        else:
            st.warning("🔎 لا توجد بيانات مطابقة حالياً.. الرادار يستمر في المسح")
            
    except:
        st.info("🔎 جاري تحليل تدفق السيولة ومزامنة التوقعات...")

with tab2:
    st.title("📊 لوحة الأداء والتقارير")
    log_df = st.session_state.performance_log
    if not log_df.empty:
        c1, c2 = st.columns(2)
        c1.metric("إجمالي الفرص المكتشفة", len(log_df))
        c2.metric("دقة الرادار", "High Quality ✅")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            log_df.to_excel(writer, index=False)
        st.download_button("📥 تحميل التقرير الذهبي (Excel)", output.getvalue(), "Elite_Report.xlsx")
        st.table(log_df)
    else:
        st.info("🔎 السجل فارغ. سيتم تسجيل أول 'انفجار' هنا آلياً.")
