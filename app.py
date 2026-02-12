import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- إعدادات المنصة ---
st.set_page_config(page_title="رادار النخبة 24/7", layout="wide")
st.title("🏹 رادار قناص السيولة (يدعم التداول الليلي وما قبل الافتتاح)")

# التحقق من المفاتيح
try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("⚠️ يرجى ضبط TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID في Secrets")
    st.stop()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

# --- محرك رصد الأسهم الأكثر نشاطاً ---
def get_extended_market_movers():
    # قائمة بأسهم الزخم العالي التي تتحرك غالباً خارج أوقات العمل الرسمية
    return ['NVDA', 'TSLA', 'AAPL', 'AMD', 'MSFT', 'META', 'PLTR', 'SMCI', 'MARA', 'COIN', 'RIOT', 'MSTR', 'AMD', 'GOOGL']

def analyze_extended_market(ticker):
    try:
        # الميزة الجوهرية: prepost=True تتيح جلب بيانات التداول خارج ساعات العمل
        df = yf.download(ticker, period="3d", interval="15m", progress=False, prepost=True)
        
        if df.empty or len(df) < 10: return None
        
        # حساب المؤشرات الفنية للزحم الحالي
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA10'] = ta.ema(df['Close'], length=10) # متوسط أسرع للمضاربة اللحظية
        
        last = df.iloc[-1]
        
        # شرط الرصد (مرن جداً لضمان التقاط الحركة في هذه اللحظة)
        if float(last['RSI']) > 50 and float(last['Close']) > float(last['EMA10']):
            return {
                "Ticker": ticker,
                "Price": round(float(last['Close']), 2),
                "RSI": round(float(last['RSI']), 1),
                "Status": "🔥 زخم صاعد" if last['RSI'] > 60 else "✅ بداية صعود"
            }
    except:
        return None

# --- واجهة التحكم ---
if 'live_hits' not in st.session_state:
    st.session_state.live_hits = []

st.info(f"الوقت الحالي (GMT): {datetime.utcnow().strftime('%H:%M')} | الرادار يراقب التداول الليلي الآن.")

col_run, col_clear = st.columns(2)
with col_run:
    if st.button("🚀 ابدأ المسح اللحظي (24/7)", use_container_width=True):
        st.session_state.live_hits = []
        tickers = get_extended_market_movers()
        
        with st.spinner("جاري قنص التحركات اللحظية..."):
            for ticker in tickers:
                res = analyze_extended_market(ticker)
                if res:
                    st.session_state.live_hits.append(res)
                    # إرسال تنبيه تليجرام فوراً
                    send_telegram(f"🔔 *إشارة رادار (خارج السوق):* {ticker}\n💰 السعر الحالي: ${res['Price']}\n📈 قوة الزخم: {res['RSI']}")

with col_clear:
    if st.button("🗑️ مسح النتائج", use_container_width=True):
        st.session_state.live_hits = []
        st.rerun()

# عرض النتائج في جدول احترافي
if st.session_state.live_hits:
    st.subheader("📋 الأسهم النشطة صعوداً في هذه اللحظة")
    df_results = pd.DataFrame(st.session_state.live_hits)
    st.dataframe(df_results, use_container_width=True)
else:
    st.warning("لا توجد أسهم تحقق شروط الصعود حالياً. قد يكون السعر مستقراً في هذه الساعة.")
