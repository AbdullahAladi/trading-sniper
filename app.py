import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الأسطورية (CSS Pro) ---
st.set_page_config(page_title="منصة الفرص - نسخة الزخم والنشاط", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.5rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; margin-top: -20px; }
    
    /* تكبير نصوص الجدول */
    .stDataFrame div { font-size: 1.6rem !important; font-weight: 600 !important; }
    
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة التنبيهات الذكية (تنبيه مرة واحدة + تغير 5%) ---
TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

# تخزين السعر الأخير الذي تم التنبيه عنده في ذاكرة الجلسة
if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {} 

def send_telegram_msg(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=10)
        except: pass

# --- 3. محرك الزخم والنشاط الفائق ---
st_autorefresh(interval=60 * 1000, key="v14_refresh")

def run_momentum_engine():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # الفلترة: فقط الأسهم النشطة جداً (حجم تداول > مليون سهم)
        active_df = df_raw[df_raw['Volume'] > 1000000]
        watchlist = active_df.sort_values(by='Volume', ascending=False).head(35)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="5d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            
            price = df_t['Close'].iloc[-1]
            change_daily = ((price - df_t['Close'].iloc[0]) / df_t['Close'].iloc[0]) * 100
            
            # حساب السيولة النسبية (Relative Volume)
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            rel_vol = vol_now / vol_avg
            
            # استبعاد الأسهم الراكدة (يجب أن تكون السيولة أعلى من المتوسط بـ 20% على الأقل)
            if rel_vol < 1.2: continue 

            # حساب قوة الزخم المدمج (Slower price decay, higher volume weight)
            m_score = (change_daily * 1.5) + (rel_vol * 15)
            m_score = min(max(m_score, 0), 100)

            # --- منطق التنبيه الذكي الجديد ---
            should_alert = False
            last_alert_price = st.session_state.alert_prices.get(ticker)

            if last_alert_price is None:
                # التنبيه الأول: عند دخول السهم في منطقة زخم عالية (>70%)
                if m_score > 70:
                    should_alert = True
                    alert_reason = "بداية زخم نشط 🚀"
            else:
                # تنبيه لاحق فقط إذا تحرك السعر بـ 5% صعوداً أو هبوطاً عن آخر تنبيه
                price_diff_pct = abs((price - last_alert_price) / last_alert_price) * 100
                if price_diff_pct >= 5.0:
                    should_alert = True
                    alert_reason = f"تحرك سعري كبير ({price_diff_pct:.1f}%) ⚠️"

            if should_alert:
                msg = (f"🎯 *تنبيه نشاط: #{ticker}*\n"
                       f"السبب: {alert_reason}\n"
                       f"السعر الحالي: ${price:.2f}\n"
                       f"التغير اليومي: {change_daily:+.2f}%\n"
                       f"قوة الزخم: {round(m_score, 1)}%")
                send_telegram_msg(msg)
                st.session_state.alert_prices[ticker] = price

            status = "نشط جداً 🔥" if m_score > 75 else "صعود مستقر 📈" if change_daily > 0 else "مراقبة 👀"

            results.append({
                "الرمز": ticker,
                "السعر": f"${price:.2f}",
                "قوة الزخم %": f"{round(m_score, 1)}%",
                "التغير اليومي": f"{change_daily:+.2f}%",
                "الحالة": status,
                "السيولة": f"{rel_vol:.1f}x"
            })
        
        return pd.DataFrame(results).sort_values(by="قوة الزخم %", ascending=False)
    except: return pd.DataFrame()

# --- 4. واجهة العرض ---
st.title("🏹 رادار الزخم والنشاط الفائق")

st.markdown("""
<div class="ticker-tape">
    📡 الرادار يلاحق الأسهم الأكثر نشاطاً وصعوداً في السوق الآن | التنبيهات مبرمجة على تحركات الـ 5%
</div>
""", unsafe_allow_html=True)

df_final = run_momentum_engine()

if not df_final.empty:
    def style_status(val):
        color = '#00ffcc' if '🔥' in str(val) or '📈' in str(val) else '#ffcc00'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        df_final.style.applymap(style_status, subset=['الحالة']),
        use_container_width=True, hide_index=True, height=850
    )
else:
    st.info("🔎 بانتظار رصد أسهم تدخل في موجة صعود ونشاط سيولة عالية...")
