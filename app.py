import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import io
from datetime import datetime

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="منصة رادار النخبة", layout="wide", initial_sidebar_state="collapsed")

# استدعاء التوكن من Secrets
try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("⚠️ يرجى ضبط مفاتيح التليجرام في Secrets")
    st.stop()

# تحسين المظهر العام (Dark Mode)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الوظائف المساندة ---
def play_sound():
    audio_html = """<audio autoplay><source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg"></audio>"""
    st.markdown(audio_html, unsafe_allow_html=True)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# --- 3. محرك الرصد والتحليل الفني ---
WATCHLIST = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT', 'META', 'PLTR', 'SMCI', 'MARA', 'COIN']

def get_live_data(ticker):
    # جلب بيانات 15 دقيقة لرصد الترند الحالي
    data = yf.download(ticker, period="5d", interval="15m", progress=False)
    if data.empty: return None
    
    # حساب المؤشرات
    data['RSI'] = ta.rsi(data['Close'], length=14)
    data['EMA20'] = ta.ema(data['Close'], length=20)
    data['EMA50'] = ta.ema(data['Close'], length=50)
    data['Vol_Avg'] = data['Volume'].rolling(window=20).mean()
    return data

# --- 4. واجهة المنصة الحقيقية ---
st.title("📊 منصة رادار النخبة - بث مباشر للترند")

if 'history' not in st.session_state:
    st.session_state.history = []

col_ctrl, col_status = st.columns([1, 4])
with col_ctrl:
    btn_scan = st.button("🚀 ابدأ المسح اللحظي", use_container_width=True)

if btn_scan:
    with st.spinner("جاري تحليل السيولة..."):
        for ticker in WATCHLIST:
            df = get_live_data(ticker)
            if df is None: continue
            
            last = df.iloc[-1]
            # شروط الترند القوي
            is_bullish = last['RSI'] > 60 and last['Close'] > last['EMA20'] and last['Volume'] > (last['Vol_Avg'] * 1.3)
            
            if is_bullish:
                # تحديث السجل والتنبيه
                if not any(d['Symbol'] == ticker for d in st.session_state.history):
                    st.session_state.history.append({"Symbol": ticker, "Price": last['Close'], "RSI": last['RSI']})
                    send_telegram(f"🔥 *ترند صاعد مرصود:* {ticker} \n💰 السعر: {last['Close']:.2f}")
                    play_sound()

# عرض الشاشة الرئيسية (Charts)
if st.session_state.history:
    selected_symbol = st.selectbox("اختر سهم من الرادار لعرض شاشة التداول:", [d['Symbol'] for d in st.session_state.history])
    
    df_plot = get_live_data(selected_symbol)
    
    # رسم المنصة الاحترافية
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # الشموع اليابانية
    fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], 
                                 low=df_plot['Low'], close=df_plot['Close'], name="السعر"), row=1, col=1)
    
    # المتوسطات المتحركة
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA20'], line=dict(color='yellow', width=1), name="EMA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA50'], line=dict(color='cyan', width=1), name="EMA 50"), row=1, col=1)
    
    # الحجم (Volume)
    fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['Volume'], name="السيولة", marker_color='rgba(100, 200, 100, 0.5)'), row=2, col=1)

    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, 
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # عرض ملخص البيانات أسفل الشاشة
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("السهم الحالي", selected_symbol)
    c2.metric("السعر اللحظي", f"${df_plot['Close'].iloc[-1]:.2f}")
    c3.metric("قوة النسبية RSI", f"{df_plot['RSI'].iloc[-1]:.1f}")
    c4.metric("حالة الترند", "🔥 صاعد قوي" if df_plot['RSI'].iloc[-1] > 60 else "⚖️ مستقر")

else:
    st.info("اضغط على 'ابدأ المسح' لرصد الأسهم التي تخترق الآن. الرادار يراقب الزخم والسيولة 24/7.")
