import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go # للتميز البصري

# --- 1. التصميم الملكي المطور ---
st.set_page_config(page_title="🛰️ رادار النخبة - العمق والتميز", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a14 0%, #040408 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00ffcc, #0077ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 0 10px #00ffcc); }
    .metric-card { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; border-radius: 15px; padding: 20px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك الذكاء السياقي ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "السعر", "بصمة السيولة", "درجة الثقة"])

def send_telegram_premium(ticker, price, score, reason):
    TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
    CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if TOKEN and CHAT_ID:
        msg = (f"💎 *فرصة للنخبة: #{ticker}*\n"
               f"━━━━━━━━━━━━━━\n"
               f"💰 السعر: ${price:.2f}\n"
               f"🔥 القوة: {score:.1f}%\n"
               f"🧠 السبب: {reason}\n"
               f"⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}")
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        except: pass

# --- 3. بناء الواجهة المتميزة ---
st_autorefresh(interval=60 * 1000, key="v27_refresh")
tab1, tab2, tab3 = st.tabs(["🎯 رادار القناص", "📈 تحليل العمق", "📊 سجل النخبة"])

with tab1:
    st.title("🛰️ رادار النخبة الذكي")
    
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 20: continue
            
            # --- محرك العمق (بصمة السيولة) ---
            live_p = df_t['Close'].iloc[-1]
            vol_last = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            
            # حساب تدفق السيولة (Money Flow Trend)
            mf_ratio = (df_t['Close'].diff().tail(5) * df_t['Volume'].tail(5)).sum()
            mf_status = "✅ تدفق إيجابي" if mf_ratio > 0 else "🛑 خروج سيولة"
            
            # معيار "درجة الثقة" (Confidence Score)
            confidence = "High" if vol_last > vol_avg * 2 and mf_ratio > 0 else "Medium"
            
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            priority_score = (mom_15m * 40) + ((vol_last/vol_avg) * 40) + (15 if mf_ratio > 0 else 0)
            priority_score = min(max(priority_score, 0), 99.9)

            # --- التنبيهات المتميزة ---
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 85 and last_p is None:
                reason = f"انفجار سيولة ({vol_last/vol_avg:.1f}x) مع {mf_status}"
                send_telegram_premium(ticker, live_p, priority_score, reason)
                st.session_state.alert_prices[ticker] = live_p
                # تسجيل البيانات العميقة
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "السعر": live_p, "بصمة السيولة": mf_status, "درجة الثقة": confidence}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker,
                "السعر ⚡": f"${live_p:.2f}",
                "قوة النخبة %": round(priority_score, 1),
                "بصمة السيولة": mf_status,
                "درجة الثقة": confidence,
                "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 نشط"
            })

        df_final = pd.DataFrame(results).sort_values(by="قوة النخبة %", ascending=False)
        
        # عرض مقياس حرارة السوق الإجمالي (تميز بصري)
        avg_market_strength = df_final["قوة النخبة %"].head(10).mean()
        st.write(f"### 🌡️ مقياس قوة الزخم الحالي: {avg_market_strength:.1f}%")
        st.progress(avg_market_strength / 100)

        st.dataframe(df_final, use_container_width=True, hide_index=True, height=600)

    except Exception as e:
        st.info("🔎 جاري تحليل بصمة السيولة ومزامنة الرادار...")

with tab2:
    st.markdown("### 📈 تحليل عمق الاتجاه")
    st.write("هذا القسم يحلل الروابط الخفية بين السعر والكمية (Volume-Price Analysis)")
    if 'df_final' in locals():
        fig = go.Figure(go.Bar(
            x=df_final['الرمز'].head(15),
            y=df_final['قوة النخبة %'].head(15),
            marker_color='#00ffcc'
        ))
        fig.update_layout(title="أقوى 15 سهم من حيث جودة التداول", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("📊 سجل النخبة للتقارير")
    # ... (نفس كود الإكسل السابق مع إضافة عمود بصمة السيولة)
