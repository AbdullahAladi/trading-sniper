import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import io
from datetime import datetime

# --- إعدادات المظهر الاحترافي ---
st.set_page_config(page_title="منصة رادار النخبة Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- التحقق من الربط ---
try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("⚠️ يرجى ضبط Secrets في الإعدادات أولاً.")
    st.stop()

# --- وظائف النظام ---
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def get_data(ticker):
    try:
        df = yf.download(ticker, period="10d", interval="15m", progress=False)
        if df.empty or len(df) < 20: return None
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
        return df
    except: return None

# --- واجهة المنصة ---
st.title("🏹 منصة رادار النخبة - تداول مباشر")

if 'signals' not in st.session_state:
    st.session_state.signals = []

# قائمة المراقبة
WATCHLIST = ['NVDA', 'TSLA', 'AAPL', 'AMD', 'META', 'PLTR', 'MARA', 'COIN', 'MSFT', 'AMZN']

# زر المسح العلوي
if st.button("🚀 ابدأ مسح السوق الفوري", use_container_width=True):
    with st.spinner("جاري قنص السيولة والزخم..."):
        for ticker in WATCHLIST:
            df = get_data(ticker)
            if df is not None:
                last = df.iloc[-1]
                # شرط الترند القوي (زخم + سيولة + سعر فوق المتوسط)
                if last['RSI'] > 60 and last['Close'] > last['EMA20'] and last['Volume'] > (last['Vol_Avg'] * 1.3):
                    if not any(d['Symbol'] == ticker for d in st.session_state.signals):
                        entry = {"Symbol": ticker, "Price": last['Close'], "RSI": last['RSI'], "Time": datetime.now().strftime("%H:%M")}
                        st.session_state.signals.append(entry)
                        send_telegram(f"🔥 *إشارة ترند صاعد:* {ticker}\n💰 السعر: ${last['Close']:.2f}\n📊 الزخم: {last['RSI']:.1f}")

# عرض الرسم البياني الاحترافي
if st.session_state.signals:
    cols = st.columns([1, 3])
    with cols[0]:
        st.subheader("🎯 الفرص المرصودة")
        df_display = pd.DataFrame(st.session_state.signals)
        selected_symbol = st.selectbox("اختر سهم للعرض:", df_display['Symbol'])
    
    with cols[1]:
        df_chart = get_data(selected_symbol)
        # رسم الشموع اليابانية
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
                                     low=df_chart['Low'], close=df_chart['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA20'], line=dict(color='#00ffcc', width=1), name="EMA 20"), row=1, col=1)
        fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], name="Volume", marker_color='#30363d'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # عرض عدادات القوة
    m1, m2, m3 = st.columns(3)
    m1.metric("السعر الحالي", f"${df_chart['Close'].iloc[-1]:.2f}")
    m2.metric("قوة الزخم RSI", f"{df_chart['RSI'].iloc[-1]:.1f}")
    m3.metric("حالة السيولة", "🔥 انفجارية" if df_chart['Volume'].iloc[-1] > df_chart['Vol_Avg'].iloc[-1] else "⚖️ طبيعية")
else:
    st.info("المنصة بانتظار بدء المسح لرصد الترند والسيولة.")
