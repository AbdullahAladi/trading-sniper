import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الفائقة (High-Contrast Cyber Design) ---
st.set_page_config(page_title="منصة الأفضلية والزخم المباشر", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.5rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; margin-top: -20px; }
    .stDataFrame div { font-size: 1.65rem !important; font-weight: 700 !important; }
    .status-bar { background: rgba(0, 255, 204, 0.1); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. نظام التنبيهات الذكي (Telegram Smart Alerts) ---
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

# --- 3. المحرك الأسطوري المطور (Live Momentum Engine) ---
st_autorefresh(interval=60 * 1000, key="v16_refresh")

def run_ultimate_live_engine():
    try:
        # تحميل الداتا الأساسية
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # فلترة الأسهم النشطة لضمان جودة الإشارات
        watchlist = df_raw[df_raw['Volume'] > 300000].sort_values(by='Volume', ascending=False).head(70)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات الحية شاملة التداول الليلي
        data = yf.download(symbols, period="2d", interval="15m", group_by='ticker', progress=False, include_postpre=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 5: continue
            
            # السعر الحالي المباشر
            live_price = df_t['Close'].iloc[-1]
            
            # حساب الزخم (آخر ساعة مقابل السعر الحالي)
            momentum_1h = ((live_price - df_t['Close'].iloc[-4]) / df_t['Close'].iloc[-4]) * 100
            # التغير منذ افتتاح آخر جلسة رسمية
            daily_change = ((live_price - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            # السيولة النسبية (Relative Volume)
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            rel_vol = vol_now / vol_avg
            
            # --- معادلة الأفضلية (الأوزان المحسنة) ---
            # تم رفع وزن السيولة والزخم اللحظي لضمان ظهور الأسهم النشطة
            priority_score = (momentum_1h * 45) + (rel_vol * 35) + (abs(daily_change) * 5)
            priority_score = min(max(priority_score, 0), 99.9)

            # --- إدارة التنبيهات (الشرط الذهبي) ---
            last_alert_p = st.session_state.alert_prices.get(ticker)
            should_alert = False
            
            # تنبيه دخول (زخم عالي لأول مرة)
            if priority_score > 75 and last_alert_p is None:
                should_alert = True
                msg_type = "🚀 انفجار زخم مباشر"
            # تنبيه حركة 5% (صعود أو هبوط)
            elif last_alert_p is not None:
                move_pct = ((live_price - last_alert_p) / last_alert_p) * 100
                if abs(move_pct) >= 5.0:
                    should_alert = True
                    msg_type = f"⚠️ تحرك كبير ({move_pct:+.1f}%)"

            if should_alert:
                send_telegram_msg(f"🎯 *إشارة حية: #{ticker}*\nنوع التنبيه: {msg_type}\nالسعر: ${live_price:.2f}\nالقوة: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_price

            # فلترة الأسهم الصامتة جداً للحفاظ على جودة الجدول
            if priority_score > 2:
                results.append({
                    "الرمز": ticker,
                    "السعر الحي": f"${live_price:.2f}",
                    "قوة الأفضلية %": round(priority_score, 1),
                    "الزخم (1h)": f"{momentum_1h:+.2f}%",
                    "الحالة": "🔥 انفجار سيولة" if priority_score > 80 else "📈 صعود نشط" if momentum_1h > 0 else "👀 مراقبة",
                    "السيولة": f"{rel_vol:.1f}x"
                })
        
        # الترتيب بالأفضلية (الأقوى في القمة)
        return pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
    except Exception as e:
        st.error(f"خطأ في المحرك: {e}")
        return pd.DataFrame()

# --- 4. العرض النهائي ---
st.title("🛰️ رادار الأفضلية والزخم المستمر")

st.markdown("""
<div class="status-bar">
    📡 الرادار يمسح الآن 70 سهماً قيادياً (مباشر، مسبق، ولاحق) | التنبيهات مفعلة على تحركات الـ 5%
</div>
""", unsafe_allow_html=True)

df_final = run_ultimate_live_engine()

if not df_final.empty:
    def style_rows(val):
        color = '#00ffcc' if '🔥' in str(val) or '📈' in str(val) else '#ffcc00'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        df_final.style.applymap(style_rows, subset=['الحالة']),
        use_container_width=True, hide_index=True, height=900
    )
else:
    st.info("🔎 جاري تحليل نبض السوق وجلب الأسعار الحية... يرجى الانتظار ثوانٍ.")
