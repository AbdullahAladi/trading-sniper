import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- إعدادات الواجهة والربط ---
st.set_page_config(page_title="رادار النشاط والارتفاع", layout="wide")
st.title("🚀 رادار النخبة: مسح الأسهم الأكثر نشاطاً وارتفاعاً")

try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("⚠️ يرجى ضبط Secrets (TOKEN & ID) أولاً.")
    st.stop()

# --- وظائف الجلب الذكي ---
def get_market_movers(type='most_active'):
    """
    جلب القوائم من ياهو فايننس تلقائياً
    أنواع البحث: 'most_active', 'day_gainers'
    """
    try:
        # استخدام سكرينر ياهو فايننس لجلب الأسهم اللحظية
        screener = yf.Screener()
        screener.set_predefined_body(type)
        results = screener.response['quotes']
        return [q['symbol'] for q in results]
    except:
        # قائمة احتياطية في حال فشل السكرينر
        return ['AAPL', 'NVDA', 'TSLA', 'AMD', 'PLTR', 'MARA']

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# --- محرك التحليل الفني ---
def analyze_stock(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 20: return None
        
        # مؤشرات الزخم والسيولة
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
        
        last = df.iloc[-1]
        
        # معايير "القناص": زخم عالي + سيولة انفجارية
        if float(last['RSI']) > 60 and float(last['Close']) > float(last['EMA20']):
            return {
                "Ticker": ticker,
                "Price": round(float(last['Close']), 2),
                "RSI": round(float(last['RSI']), 1),
                "Vol_Ratio": round(float(last['Volume'] / last['Vol_Avg']), 2)
            }
    except:
        return None

# --- واجهة المنصة ---
col1, col2 = st.columns(2)
with col1:
    scan_type = st.selectbox("اختر نوع الفحص:", 
                            ["الأسهم الأكثر نشاطاً (Most Active)", "الأعلى ارتفاعاً اليوم (Day Gainers)"])
with col2:
    st.write(" ")
    start_btn = st.button("🔍 ابدأ مسح السوق الآن", use_container_width=True)

if 'found_opportunities' not in st.session_state:
    st.session_state.found_opportunities = []

if start_btn:
    query_type = 'most_active' if "نشاطاً" in scan_type else 'day_gainers'
    tickers = get_market_movers(query_type)
    
    st.write(f"🔎 جاري فحص أفضل {len(tickers)} سهم من ياهو فايننس...")
    
    for ticker in tickers:
        res = analyze_stock(ticker)
        if res:
            if not any(d['Ticker'] == ticker for d in st.session_state.found_opportunities):
                st.session_state.found_opportunities.append(res)
                send_telegram(f"🔥 *فرصة نشطة:* {ticker}\n💰 السعر: ${res['Price']}\n📈 الزخم: {res['RSI']}\n📊 السيولة: {res['Vol_Ratio']}x")

# عرض النتائج في جدول تفاعلي
if st.session_state.found_opportunities:
    st.subheader("📋 الفرص المكتشفة بناءً على نشاط السوق")
    df_results = pd.DataFrame(st.session_state.found_opportunities)
    st.table(df_results)
    
    if st.button("🗑️ مسح السجل"):
        st.session_state.found_opportunities = []
        st.rerun()
else:
    st.info("الرادار جاهز. اختر نوع الفحص واضغط ابدأ.")
