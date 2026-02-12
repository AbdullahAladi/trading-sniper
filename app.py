import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import io
from datetime import datetime

# إعدادات واجهة المنصة الاحترافية
st.set_page_config(page_title="منصة رادار النخبة Pro", layout="wide")
st.markdown("<style>main { background-color: #0e1117; }</style>", unsafe_allow_html=True)

# جلب المفاتيح بأمان
try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("⚠️ يرجى ضبط Secrets في الإعدادات أولاً.")
    st.stop()

# وظائف التنبيه
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def get_clean_data(ticker):
    try:
        df = yf.download(ticker, period="10d", interval="15m", progress=False)
        if df.empty or len(df) < 25: return None
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
        return df
    except: return None

# واجهة المنصة الرئيسية
st.title("🏹 منصة رادار النخبة - تداول مباشر 24/7")

if 'signals' not in st.session_state:
    st.session_state.signals = []

# قائمة المراقبة المقترحة
WATCHLIST = ['NVDA', 'TSLA', 'AAPL', 'AMD', 'META', 'PLTR', 'MARA', 'COIN', 'MSFT', 'AMZN']

# شريط التحكم
col_btn, col_test = st.columns([1, 1])
with col_btn:
    if st.button("🚀 ابدأ مسح السوق الفوري", use_container_width=True):
        with st.spinner("جاري قنص السيولة والزخم..."):
            for ticker in WATCHLIST:
                df = get_clean_data(ticker)
                if df is not None:
                    last = df.iloc[-1]
                    # معالجة مشكلة المقارنة (أرقام مجردة)
                    l_price, l_rsi, l_vol, a_vol, l_ema = float(last['Close']), float(last['RSI']), float(last['Volume']), float(last['Vol_Avg']), float(last['EMA20'])
                    
                    if l_rsi > 60 and l_price > l_ema and l_vol > (a_vol * 1.3):
                        if not any(d['Symbol'] == ticker for d in st.session_state.signals):
                            st.session_state.signals.append({"Symbol": ticker, "Price": l_price, "RSI": l_rsi, "Time": datetime.now().strftime("%H:%M")})
                            send_telegram(f"🔥 *ترند صاعد:* {ticker}\n💰 السعر: ${l_price:.2f}")

with col_test:
    if st.button("🧪 اختبار ربط تليجرام", use_container_width=True):
        send_telegram("🔔 نظام الرادار متصل وجاهز للعمل!")
        st.toast("تم إرسال رسالة الاختبار")

# عرض المنصة الرسومية
if st.session_state.signals:
    tab1, tab2 = st.tabs(["📈 الرسم البياني التفاعلي", "📋 سجل الفرص"])
    
    with tab1:
        selected = st.selectbox("اختر سهم للعرض:", [s['Symbol'] for s in st.session_state.signals])
        df_chart = get_clean_data(selected)
        
        # رسم الشموع اليابانية الاحترافية
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
                                     low=df_chart['Low'], close=df_chart['Close'], name="السعر"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA20'], line=dict(color='#00ffcc', width=1), name="EMA 20"), row=1, col=1)
        fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], name="السيولة", marker_color='#30363d'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_final = pd.DataFrame(st.session_state.signals)
        st.table(df_final)
        
        # تصدير التقرير (تصحيح خطأ الصورة e15a97)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)
        
        st.download_button(label="📥 تحميل التقرير (Excel)", data=buffer.getvalue(), file_name="radar_report.xlsx")
else:
    st.info("المنصة بانتظار بدء المسح لرصد الترند والسيولة.")
