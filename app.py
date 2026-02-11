import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية ---
st.set_page_config(page_title="رادار الأفضلية - التداول المستمر", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.2rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; margin-top: -20px; }
    .stDataFrame div { font-size: 1.6rem !important; font-weight: 700 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 12px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 20px; }
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

# --- 3. محرك الأفضلية والسعر المباشر (24/5) ---
st_autorefresh(interval=60 * 1000, key="v15_2_refresh")

def run_live_priority_engine():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # تصفية الأسهم النشطة
        active_pool = df_raw[df_raw['Volume'] > 500000]
        watchlist = active_pool.sort_values(by='Volume', ascending=False).head(60)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات مع تفعيل التداول المسبق واللاحق (include_postpre=True)
        data = yf.download(symbols, period="2d", interval="15m", group_by='ticker', progress=False, include_postpre=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 5: continue
            
            # --- جلب السعر المباشر بدقة ---
            # نأخذ آخر سعر متاح سواء كان في السوق النظامي أو التداول الملحق
            live_price = df_t['Close'].iloc[-1]
            
            # حساب الزخم اللحظي (آخر ساعة تداول متاحة)
            momentum_1h = ((live_price - df_t['Close'].iloc[-4]) / df_t['Close'].iloc[-4]) * 100
            # التغير اليومي الفعلي (مقارنة بفتح السوق)
            daily_change = ((live_price - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            # السيولة النسبية
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            rel_vol = vol_now / vol_avg
            
            # معادلة الأفضلية المطورة
            priority_score = (momentum_1h * 40) + (rel_vol * 30) + (daily_change * 10)
            priority_score = min(max(priority_score, 0), 99.9)

            # التنبيهات الذكية (بناءً على السعر الحي)
            last_price = st.session_state.alert_prices.get(ticker)
            should_alert = False
            
            if priority_score > 70 and last_price is None:
                should_alert = True
                reason = "🚀 زخم شرائي مباشر"
            elif last_price is not None:
                p_diff = abs((live_price - last_price) / last_price) * 100
                if p_diff >= 5.0:
                    should_alert = True
                    reason = f"⚠️ تحرك حي مفاجئ ({p_diff:.1f}%)"

            if should_alert:
                send_telegram_msg(f"🎯 *تنبيه مباشر: #{ticker}*\nالحالة: {reason}\nالسعر الحالي: ${live_price:.2f}\nالزخم: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_price

            if priority_score > 5:
                results.append({
                    "الرمز": ticker,
                    "السعر الحي": f"${live_price:.2f}",
                    "قوة الأفضلية %": round(priority_score, 1),
                    "الزخم (1h)": f"{momentum_1h:+.2f}%",
                    "الحالة": "🔥 انفجار حي" if priority_score > 80 else "📈 نشاط مستمر" if momentum_1h > 0 else "👀 مراقبة",
                    "السيولة": f"{rel_vol:.1f}x"
                })
        
        return pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
    except: return pd.DataFrame()

# --- 4. العرض ---
st.title("🛰️ رادار الأفضلية والسعر المباشر")

st.markdown("""
<div class="ticker-tape">
    📡 الرادار يراقب الآن التداول (المباشر، المسبق، واللاحق) | تحديث تلقائي للأسعار والزخم كل دقيقة
</div>
""", unsafe_allow_html=True)

df_live = run_live_priority_engine()

if not df_live.empty:
    st.dataframe(
        df_live.style.applymap(lambda x: 'color: #00ffcc; font-weight: bold;' if '🔥' in str(x) or '📈' in str(x) else 'color: #ffcc00;', subset=['الحالة']),
        use_container_width=True, hide_index=True, height=850
    )
else:
    st.info("🔎 الرادار يمسح السوق الآن بحثاً عن أسعار مباشرة... يرجى الانتظار")
