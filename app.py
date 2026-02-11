import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية (تصميم الرادار الفائق) ---
st.set_page_config(page_title="رادار الزخم والنشاط", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.2rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 600 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 12px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; font-size: 1.3rem; margin-bottom: 20px; }
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

# --- 3. محرك الزخم والنشاط (النسخة المطورة) ---
st_autorefresh(interval=60 * 1000, key="v15_refresh")

def run_pro_momentum_engine():
    try:
        # 1. جلب قائمة أكبر للأسهم لضمان عدم خلو الرادار
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # تصفية الأسهم التي تمتلك حجم تداول معقول (أكثر من 500 ألف سهم)
        active_pool = df_raw[df_raw['Volume'] > 500000]
        watchlist = active_pool.sort_values(by='Volume', ascending=False).head(60)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="3d", interval="15m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 5: continue
            
            price = df_t['Close'].iloc[-1]
            # حساب التغير في آخر 4 ساعات (الزخم اللحظي)
            momentum_change = ((price - df_t['Close'].iloc[-4]) / df_t['Close'].iloc[-4]) * 100
            # التغير اليومي
            daily_change = ((price - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            # حساب السيولة النسبية (Relative Volume)
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            rel_vol = vol_now / vol_avg
            
            # --- معادلة قوة الزخم الجديدة (تطارد الارتفاع والسيولة) ---
            # إذا كان السهم يرتفع وبسيولة عالية، يحصل على درجة مرتفعة جداً
            momentum_score = (momentum_change * 5) + (rel_vol * 15) + (daily_change * 2)
            momentum_score = min(max(momentum_score, 0), 100)

            # منطق التنبيه (تنبيه واحد + قاعدة الـ 5%)
            last_price = st.session_state.alert_prices.get(ticker)
            should_alert = False
            
            if momentum_score > 75 and last_price is None:
                should_alert = True
                reason = "🚀 اختراق وزخم شرائي!"
            elif last_price is not None:
                p_diff = abs((price - last_price) / last_price) * 100
                if p_diff >= 5.0:
                    should_alert = True
                    reason = "⚠️ تحرك سعري كبير (>5%)"

            if should_alert:
                send_telegram_msg(f"🎯 *إشارة نشاط: #{ticker}*\nالسبب: {reason}\nالسعر: ${price:.2f}\nالزخم: {momentum_score:.1f}%")
                st.session_state.alert_prices[ticker] = price

            # فلترة العرض: لا تظهر إلا الأسهم التي تتحرك فعلياً (زخم > 10%)
            if momentum_score > 10:
                results.append({
                    "الرمز": ticker,
                    "السعر": f"${price:.2f}",
                    "قوة الزخم %": round(momentum_score, 1),
                    "التغير اللحظي": f"{momentum_change:+.2f}%",
                    "الحالة": "🔥 انفجار سعري" if momentum_score > 80 else "📈 صعود نشط" if momentum_change > 0 else "👀 مراقبة",
                    "السيولة": f"{rel_vol:.1f}x"
                })
        
        return pd.DataFrame(results).sort_values(by="قوة الزخم %", ascending=False)
    except: return pd.DataFrame()

# --- 4. واجهة العرض ---
st.title("🏹 رادار الزخم واقتناص السيولة")

st.markdown("""
<div class="ticker-tape">
    ⚡ الرادار يركز الآن على الأسهم التي "ترتفع بقوة" وبسيولة عالية | التنبيهات ذكية (قاعدة الـ 5%)
</div>
""", unsafe_allow_html=True)

df_mom = run_pro_momentum_engine()

if not df_mom.empty:
    st.dataframe(
        df_mom.style.applymap(lambda x: 'color: #00ffcc; font-weight: bold;' if '🔥' in str(x) or '📈' in str(x) else 'color: #ffcc00;', subset=['الحالة']),
        use_container_width=True, hide_index=True, height=850
    )
else:
    st.info("🔎 بانتظار رصد تحركات سعرية قوية في السوق...")
