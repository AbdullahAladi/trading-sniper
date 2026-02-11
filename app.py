import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. التصميم الملكي ---
st.set_page_config(page_title="منصة الفرص الأسطورية V26", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    .status-bar { background: rgba(0, 255, 204, 0.1); padding: 10px; border-radius: 8px; border: 1px solid #00ffcc; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "السعر", "التنبؤ", "القوة"])

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram(msg):
    if TOKEN and CHAT_ID:
        try: url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"; requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. بناء الواجهة (Tabs) ---
tab1, tab2 = st.tabs(["🛰️ رادار الأفضلية والزخم", "📊 سجل الأداء والتقارير"])

# تحديث تلقائي كل 60 ثانية لضمان الاستقرار
st_autorefresh(interval=60 * 1000, key="v26_refresh")

with tab1:
    st.title("🛰️ رادار الأفضلية والتنبؤ")
    st.markdown('<div class="status-bar">📡 التنبيهات مخصصة لـ "الانفجارات" فقط (>80%) | مراقبة تحركات الـ 5% نشطة</div>', unsafe_allow_html=True)

    try:
        # جلب البيانات الأساسية
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب الأسعار اللحظية (يشمل التداول المسبق واللاحق)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 15: continue
            
            live_p = df_t['Close'].iloc[-1]
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            
            # محرك التنبؤ الذكي
            trend_3m = live_p - df_t['Close'].iloc[-3]
            if trend_3m > 0 and rel_vol > 1.5: prediction = "🚀 صعود وشيك"; p_bonus = 15
            elif rel_vol > 2.5: prediction = "📦 تجميع خفي"; p_bonus = 10
            else: prediction = "⚖️ استقرار"; p_bonus = 0
            
            # قوة الأفضلية (المعيار المعتمد)
            priority_score = (mom_15m * 50) + (rel_vol * 30) + p_bonus
            priority_score = min(max(priority_score, 0), 99.9)

            # --- منطق التنبيهات (انفجار + قاعدة الـ 5%) ---
            last_p = st.session_state.alert_prices.get(ticker)
            should_alert = False
            
            if priority_score >= 80 and last_p is None:
                should_alert = True; m_type = "🔥 انفجار أسطوري"
            elif last_p is not None:
                diff = ((live_p - last_p) / last_p) * 100
                if abs(diff) >= 5.0:
                    should_alert = True; m_type = f"⚠️ تحرك حي ({diff:+.1f}%)"

            if should_alert:
                send_telegram(f"🎯 *تنبيه النخبة: #{ticker}*\nالحالة: {m_type}\nالسعر: ${live_p:.2f}\nالتنبؤ: {prediction}")
                st.session_state.alert_prices[ticker] = live_p
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "السعر": live_p, "التنبؤ": prediction, "القوة": round(priority_score, 1)}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({"الرمز": ticker, "السعر": f"${live_p:.2f}", "الأفضلية %": round(priority_score, 1), "تنبؤ الحركة": prediction, "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 نشط", "السيولة": f"{rel_vol:.1f}x"})

        df_final = pd.DataFrame(results).sort_values(by="الأفضلية %", ascending=False)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=750)

    except Exception as e:
        st.info("🔎 جاري مزامنة نبض السوق وجلب الأسعار اللحظية...")

with tab2:
    st.header("📊 لوحة الأداء والتقارير")
    log_df = st.session_state.performance_log
    if not log_df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            log_df.to_excel(writer, index=False)
        st.download_button("📥 تحميل سجل الانفجارات (Excel)", output.getvalue(), "Daily_Report.xlsx")
        st.table(log_df)
    else:
        st.info("السجل فارغ. سيتم تسجيل أول 'انفجار' هنا آلياً.")
