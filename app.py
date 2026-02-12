import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime

# --- الإعدادات ---
st.set_page_config(page_title="رادار النخبة المباشر", layout="wide")
st.title("🛰️ رادار النخبة - مسح السوق اللحظي")

# جلب المفاتيح من السيكرتس
try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("⚠️ يرجى التأكد من ضبط TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID في Secrets")
    st.stop()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

# --- وظيفة جلب الأسهم الأكثر نشاطاً ---
def get_active_stocks():
    # نستخدم قائمة واسعة ومباشرة لضمان وجود بيانات
    tickers = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT', 'META', 'PLTR', 'SMCI', 'MARA', 'COIN', 
               'AMZN', 'GOOGL', 'NFLX', 'BRK-B', 'UNH', 'JNJ', 'XOM', 'JPM', 'V', 'PG']
    return tickers

# --- محرك التحليل المرن (لضمان ظهور نتائج) ---
def analyze_stock_flexible(ticker):
    try:
        # جلب بيانات 5 أيام بفاصل 15 دقيقة
        df = yf.download(ticker, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 15: return None
        
        # حساب المؤشرات
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        last = df.iloc[-1]
        
        # --- شروط مرنة للرصد ---
        # سنكتفي بأن يكون RSI فوق 50 والسعر فوق المتوسط لضمان ظهور الأسهم الصاعدة حالياً
        if float(last['RSI']) > 50 and float(last['Close']) > float(last['EMA20']):
            return {
                "Ticker": ticker,
                "Price": round(float(last['Close']), 2),
                "RSI": round(float(last['RSI']), 1),
                "Signal": "📈 صعود مستقر" if last['RSI'] < 65 else "🔥 زخم عالي"
            }
    except:
        return None

# --- الواجهة ---
if 'results' not in st.session_state:
    st.session_state.results = []

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🔍 ابدأ مسح النشاط الآن", use_container_width=True):
        st.session_state.results = [] # تفريغ النتائج السابقة
        tickers = get_active_stocks()
        st.write(f"جاري فحص {len(tickers)} سهم نشط...")
        
        for ticker in tickers:
            res = analyze_stock_flexible(ticker)
            if res:
                st.session_state.results.append(res)
                send_telegram(f"✅ *سهم نشط صاعد:* {ticker}\n💰 السعر: ${res['Price']}\n📈 الزخم: {res['RSI']}")

with col2:
    if st.button("🗑️ مسح النتائج", use_container_width=True):
        st.session_state.results = []
        st.rerun()

# عرض النتائج
if st.session_state.results:
    st.subheader("📊 الأسهم الصاعدة المرصودة حالياً")
    df_res = pd.DataFrame(st.session_state.results)
    st.dataframe(df_res, use_container_width=True)
else:
    st.info("لا توجد نتائج حالياً. اضغط على 'ابدأ مسح النشاط'. إذا لم تظهر نتائج، تأكد أن السوق الأمريكي مفتوح حالياً.")
