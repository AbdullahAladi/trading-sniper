import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import streamlit.components.v1 as components

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="منصة الفرص - الرادار الموقوت", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; }
    .stDataFrame div { font-size: 1.6rem !important; font-weight: 700 !important; }
    
    /* تصميم صندوق العد التنازلي */
    .timer-container {
        display: flex; justify-content: center; align-items: center; 
        background: rgba(0, 255, 204, 0.1); border: 1px solid #00ffcc;
        border-radius: 15px; padding: 10px; margin: 10px auto; width: 300px;
    }
    .timer-text { font-family: 'Orbitron', sans-serif; font-size: 1.5rem; color: #00ffcc; margin-right: 15px; }
    .timer-value { font-family: 'Orbitron', sans-serif; font-size: 2.2rem; color: #ffffff; text-shadow: 0 0 10px #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إضافة العد التنازلي (JavaScript) ---
def countdown_timer(seconds):
    components.html(f"""
        <div style="display: flex; justify-content: center; align-items: center; font-family: 'Orbitron', sans-serif; color: #00ffcc; background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; border-radius: 10px; padding: 10px;">
            <span style="font-size: 1.2rem; margin-right: 20px;">تحديث البيانات خلال:</span>
            <span id="timer" style="font-size: 2rem; font-weight: bold; color: #fff;">{seconds}</span>
            <span style="font-size: 1.2rem; margin-left: 10px;">ثانية</span>
        </div>
        <script>
            var count = {seconds};
            var timer = setInterval(function() {{
                count--;
                document.getElementById('timer').innerHTML = count;
                if (count <= 0) {{
                    clearInterval(timer);
                    window.parent.location.reload();
                }}
            }}, 1000);
        </script>
    """, height=100)

# --- 3. إدارة التنبيهات الذكية ---
TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {} 

def send_telegram_msg(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=5)
        except: pass

# --- 4. محرك الأفضلية والزخم النهائي ---
def run_priority_engine():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(50)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات (Pre-market & Live)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 2: continue
            
            live_price = df_t['Close'].iloc[-1]
            momentum_15m = ((live_price - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100 if len(df_t) > 15 else 0
            daily_change = ((live_price - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            rel_vol = df_t['Volume'].iloc[-1] / df_t['Volume'].mean() if df_t['Volume'].mean() > 0 else 1
            
            # معادلة الأفضلية المتفق عليها
            priority_score = (momentum_15m * 50) + (rel_vol * 30) + (abs(daily_change) * 10)
            priority_score = min(max(priority_score, 0), 99.9)

            # التنبيهات الذكية (5% Rule)
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score > 75 and last_p is None:
                send_telegram_msg(f"🎯 *إشارة أولوية: #{ticker}*\nالسعر: ${live_price:.2f}\nالقوة: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_price
            elif last_p is not None and abs((live_price - last_p) / last_p) * 100 >= 5.0:
                send_telegram_msg(f"⚠️ *تحرك 5%: #{ticker}*\nالسعر الآن: ${live_price:.2f}")
                st.session_state.alert_prices[ticker] = live_price

            if priority_score > 5:
                results.append({
                    "الرمز": ticker,
                    "السعر الحي ⚡": f"${live_price:.2f}",
                    "قوة الأفضلية %": round(priority_score, 1),
                    "الزخم (15د)": f"{momentum_15m:+.2f}%",
                    "الحالة": "🔥 انفجار سيولة" if priority_score > 80 else "📈 صعود نشط" if momentum_1h > 0 else "👀 مراقبة",
                    "السيولة": f"{rel_vol:.1f}x"
                })
        
        return pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
    except: return pd.DataFrame()

# --- 5. العرض النهائي ---
st.title("🛰️ رادار الأفضلية المباشر")

# استدعاء العد التنازلي (30 ثانية)
countdown_timer(30)

df_final = run_priority_engine()

if not df_final.empty:
    def style_status(val):
        color = '#00ffcc' if '🔥' in str(val) or '📈' in str(val) else '#ffcc00'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        df_final.style.applymap(style_status, subset=['الحالة']),
        use_container_width=True, hide_index=True, height=850
    )
else:
    st.info("🔎 الرادار يمسح تدفق السيولة... يرجى الانتظار")
