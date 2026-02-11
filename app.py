import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="🛰️ رادار النخبة والتحليل العميق", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a14 0%, #040408 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00ffcc, #0077ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 0 10px #00ffcc); text-align: center; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    .status-bar { background: rgba(0, 255, 204, 0.05); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك التنبيهات والذاكرة ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "السعر", "بصمة السيولة", "درجة الثقة"])

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_premium(ticker, price, score, reason):
    if TOKEN and CHAT_ID:
        msg = (f"💎 *فرصة للنخبة: #{ticker}*\n━━━━━━━━━━━━━━\n💰 السعر: ${price:.2f}\n🔥 القوة: {score:.1f}%\n🧠 التحليل: {reason}\n⏰ الوقت: {datetime.now().strftime('%H:%M')}")
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. بناء الواجهة (Tabs) ---
tab1, tab2, tab3 = st.tabs(["🛰️ رادار القناص", "📈 تحليل العمق", "📊 سجل النخبة"])
st_autorefresh(interval=60 * 1000, key="v28_refresh")

with tab1:
    st.title("🛰️ رادار النخبة والتحليل العميق")
    st.markdown('<div class="status-bar">📡 الفلتر يطارد "بصمة السيولة الذكية" | التنبيهات مخصصة للانفجارات (>80%)</div>', unsafe_allow_html=True)

    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(45)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 20: continue
            
            # --- محرك التحليل العميق (VPA Analysis) ---
            live_p = df_t['Close'].iloc[-1]
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            
            # حساب تدفق السيولة (Money Flow Index)
            mf_score = (df_t['Close'].diff().tail(5) * df_t['Volume'].tail(5)).sum()
            mf_status = "✅ تجميع" if mf_score > 0 else "🛑 تصريف"
            
            # درجة الثقة الذكية
            confidence = "High" if vol_now > vol_avg * 2.5 and mf_score > 0 else "Medium"
            
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            priority_score = (mom_15m * 45) + ((vol_now/vol_avg) * 35) + (20 if mf_score > 0 else 0)
            priority_score = min(max(priority_score, 0), 99.9)

            # التنبيهات الاستراتيجية (قاعدة الـ 5% + انفجار)
            last_p = st.session_state.alert_prices.get(ticker)
            should_alert = False
            if priority_score >= 80 and last_p is None:
                should_alert = True; rsn = f"انفجار سيولة ({vol_now/vol_avg:.1f}x) مع تجميع إيجابي"
            elif last_p is not None and abs((live_p - last_p)/last_p)*100 >= 5.0:
                should_alert = True; rsn = "تحرك حي بنسبة 5% من سعر التنبيه"

            if should_alert:
                send_telegram_premium(ticker, live_p, priority_score, rsn)
                st.session_state.alert_prices[ticker] = live_p
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "السعر": live_p, "بصمة السيولة": mf_status, "درجة الثقة": confidence}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({"الرمز": ticker, "السعر⚡": f"${live_p:.2f}", "الأفضلية %": round(priority_score, 1), "بصمة السيولة": mf_status, "درجة الثقة": confidence, "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 نشط"})

        df_final = pd.DataFrame(results).sort_values(by="الأفضلية %", ascending=False)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=700)

    except Exception as e:
        st.info("🔎 جاري تحليل بصمة السيولة ومزامنة التوقعات اللحظية...")

with tab2:
    st.markdown("### 📈 تحليل قوة الزخم (Top 10)")
    if 'df_final' in locals() and not df_final.empty:
        fig = go.Figure(go.Bar(x=df_final['الرمز'].head(10), y=df_final['الأفضلية %'].head(10), marker_color='#00ffcc'))
        fig.update_layout(template="plotly_dark", title="أقوى 10 أسهم حالياً")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("📊 سجل النخبة للتقارير")
    log_df = st.session_state.performance_log
    if not log_df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            log_df.to_excel(writer, index=False)
        st.download_button("📥 تحميل التقرير الذهبي (Excel)", output.getvalue(), "Elite_Report.xlsx")
        st.table(log_df)
    else:
        st.info("🔎 بانتظار أول انفجار سعري لبدء التوثيق الإحصائي.")
