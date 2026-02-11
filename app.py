import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="رادار الأفضلية والزخم المستمر", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.2rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; margin-top: -20px; }
    .stDataFrame div { font-size: 1.6rem !important; font-weight: 700 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة التنبيهات الذكية ---
TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {} 

def send_telegram_msg(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=10)
        except: pass

# --- 3. محرك الأفضلية المصحح (التعامل مع التداول المستمر) ---
st_autorefresh(interval=60 * 1000, key="v16_1_refresh")

def run_ultimate_stable_engine():
    try:
        # تحميل قائمة الأسهم
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # فلترة لضمان جودة الأسهم الممسوحة
        watchlist = df_raw[df_raw['Volume'] > 300000].sort_values(by='Volume', ascending=False).head(50)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات (تمت إزالة include_postpre من download لتفادي الخطأ)
        data = yf.download(symbols, period="2d", interval="15m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 5: continue
            
            # السعر الحالي (يعمل لحظياً أثناء السوق)
            live_price = df_t['Close'].iloc[-1]
            
            # حساب الزخم اللحظي (آخر ساعة)
            momentum_1h = ((live_price - df_t['Close'].iloc[-4]) / df_t['Close'].iloc[-4]) * 100
            # التغير اليومي
            daily_change = ((live_price - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            # السيولة النسبية
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            rel_vol = vol_now / vol_avg
            
            # معادلة الأفضلية المطورة (ترتيب حقيقي بناءً على الحركة)
            priority_score = (momentum_1h * 45) + (rel_vol * 35) + (abs(daily_change) * 5)
            priority_score = min(max(priority_score, 0), 99.9)

            # التنبيهات الذكية
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score > 75 and last_p is None:
                send_telegram_msg(f"🎯 *إشارة حية: #{ticker}*\nزخم شرائي قوي مكتشف!\nالسعر: ${live_price:.2f}\nالقوة: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_price
            elif last_p is not None:
                if abs((live_price - last_p) / last_p) * 100 >= 5.0:
                    send_telegram_msg(f"⚠️ *تحرك 5%: #{ticker}*\nتغير سعري كبير!\nالسعر الحالي: ${live_price:.2f}")
                    st.session_state.alert_prices[ticker] = live_price

            if priority_score > 2:
                results.append({
                    "الرمز": ticker,
                    "السعر": f"${live_price:.2f}",
                    "قوة الأفضلية %": round(priority_score, 1),
                    "الزخم (1h)": f"{momentum_1h:+.2f}%",
                    "الحالة": "🔥 انفجار زخم" if priority_score > 80 else "📈 صعود نشط" if momentum_1h > 0 else "👀 مراقبة",
                    "السيولة": f"{rel_vol:.1f}x"
                })
        
        return pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
    except Exception as e:
        st.error(f"خطأ في النظام: {e}")
        return pd.DataFrame()

# --- 4. العرض ---
st.title("🛰️ رادار الأفضلية والزخم المستمر")

st.markdown("""
<div class="ticker-tape">
    📡 الرادار يراقب الآن نبض السوق والسيولة | التنبيهات ذكية ومفعلة على تحركات الـ 5%
</div>
""", unsafe_allow_html=True)

df_final = run_ultimate_stable_engine()

if not df_final.empty:
    st.dataframe(
        df_final.style.applymap(lambda x: 'color: #00ffcc; font-weight: bold;' if '🔥' in str(x) or '📈' in str(x) else 'color: #ffcc00;', subset=['الحالة']),
        use_container_width=True, hide_index=True, height=850
    )
else:
    st.info("🔎 جاري تحليل تدفق السيولة... يرجى الانتظار ثوانٍ.")
