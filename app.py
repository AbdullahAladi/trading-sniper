import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="منصة الفرص الأسطورية - النسخة المعتمدة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.2rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; margin-top: -20px; }
    .stDataFrame div { font-size: 1.6rem !important; font-weight: 700 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة التنبيهات الذكية (تنبيه واحد + قاعدة الـ 5%) ---
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

# --- 3. المحرك الأسطوري (Live Momentum + Accuracy) ---
st_autorefresh(interval=60 * 1000, key="v18_stable_refresh")

def run_ultimate_stable_engine():
    try:
        # تحميل الداتا الأساسية
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(50)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات اللحظية (Pre-market & Post-market)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 2: continue
            
            # السعر الحي المباشر (أدق سعر في آخر دقيقة تداول)
            live_price = df_t['Close'].iloc[-1]
            
            # حساب الزخم اللحظي (آخر 15 دقيقة)
            momentum_15m = ((live_price - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100 if len(df_t) > 15 else 0
            
            # التغير اليومي (مقارنة بالفتح الفعلي)
            daily_change = ((live_price - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            # السيولة النسبية (حجم التداول اللحظي)
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            rel_vol = vol_now / vol_avg if vol_avg > 0 else 1
            
            # معادلة "الأفضلية المطلقة" (تطارد الصعود الحي والسيولة)
            priority_score = (momentum_15m * 50) + (rel_vol * 30) + (abs(daily_change) * 10)
            priority_score = min(max(priority_score, 0), 99.9)

            # --- نظام التنبيهات الذكي (5% Rule) ---
            last_p = st.session_state.alert_prices.get(ticker)
            should_alert = False
            
            if priority_score > 75 and last_p is None:
                should_alert = True
                msg_type = "🚀 انفجار زخم مباشر"
            elif last_p is not None:
                move_pct = abs((live_price - last_p) / last_p) * 100
                if move_pct >= 5.0:
                    should_alert = True
                    msg_type = f"⚠️ تحرك كبير ({move_pct:.1f}%)"

            if should_alert:
                send_telegram_msg(f"🎯 *إشارة حية: #{ticker}*\nنوع التنبيه: {msg_type}\nالسعر الحالي: ${live_price:.2f}\nقوة الأفضلية: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_price

            # فلترة العرض لضمان الجودة
            if priority_score > 5:
                results.append({
                    "الرمز": ticker,
                    "السعر الحي ⚡": f"${live_price:.2f}",
                    "قوة الأفضلية %": round(priority_score, 1),
                    "الزخم (15د)": f"{momentum_15m:+.2f}%",
                    "الحالة": "🔥 انفجار سيولة" if priority_score > 80 else "📈 صعود نشط" if momentum_15m > 0 else "👀 مراقبة",
                    "السيولة اللحظية": f"{rel_vol:.1f}x"
                })
        
        # الترتيب بالأفضلية (الأقوى في القمة)
        return pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
    except Exception as e:
        return pd.DataFrame()

# --- 4. العرض النهائي ---
st.title("🛰️ منصة الفرص الأسطورية")

st.markdown(f"""
<div class="ticker-tape">
    📡 الرادار يراقب الآن نبض السوق والسيولة | الوقت الحالي: {datetime.now().strftime('%H:%M:%S')} | التنبيهات نشطة ✅
</div>
""", unsafe_allow_html=True)

df_final = run_ultimate_stable_engine()

if not df_final.empty:
    def style_status(val):
        color = '#00ffcc' if '🔥' in str(val) or '📈' in str(val) else '#ffcc00'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        df_final.style.applymap(style_status, subset=['الحالة']),
        use_container_width=True, hide_index=True, height=900
    )
else:
    st.info("🔎 الرادار يمسح تدفق السيولة الآن... يرجى الانتظار ثوانٍ.")
