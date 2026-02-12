import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import requests
import io

# --- الإعدادات وجلب المفاتيح ---
TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

st.set_page_config(page_title="رادار ناسداك الشامل", layout="wide")
st.title("🛰️ رادار النخبة: ماسح سوق ناسداك الشامل")

# --- وظيفة جلب قائمة الأسهم من GitHub ---
@st.cache_data # تخزين القائمة مؤقتاً لتسريع التطبيق
def get_nasdaq_list():
    # رابط افتراضي لملف ناسداك على قيت هوب (يمكنك استبداله برابط ملفك الخاص)
    url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_tickers.txt"
    try:
        response = requests.get(url)
        # تحويل النص إلى قائمة رموز
        tickers = response.text.split('\n')
        return [t.strip() for t in tickers if t.strip()][:100] # نحدد أول 100 سهم كمرحلة تجريبية لسرعة الأداء
    except:
        return ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT']

# --- وظيفة التنبيه ---
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# --- محرك الرصد الذكي ---
def analyze_trend(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 20: return None
        
        # حساب المؤشرات الفنية للزخم
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
        
        last = df.iloc[-1]
        
        # --- فلتر الصعود الحقيقي (جميع الأسهم الصاعدة بسيولة) ---
        if last['RSI'] > 60 and last['Close'] > last['EMA20'] and last['Volume'] > (last['Vol_Avg'] * 1.5):
            return {
                "Symbol": ticker,
                "Price": round(float(last['Close']), 2),
                "RSI": round(float(last['RSI']), 1),
                "Volume_Increase": round(float(last['Volume'] / last['Vol_Avg']), 2)
            }
    except:
        return None

# --- واجهة التحكم ---
if 'all_hits' not in st.session_state:
    st.session_state.all_hits = []

if st.button("🔍 ابدأ المسح الشامل لناسداك"):
    tickers = get_nasdaq_list()
    st.write(f"جاري فحص {len(tickers)} سهم من قائمة ناسداك...")
    
    progress_bar = st.progress(0)
    for i, ticker in enumerate(tickers):
        res = analyze_trend(ticker)
        if res:
            if not any(d['Symbol'] == ticker for d in st.session_state.all_hits):
                st.session_state.all_hits.append(res)
                send_telegram(f"🔥 *سهم صاعد مرصود:* {ticker}\n💰 السعر: ${res['Price']}\n📈 الزخم: {res['RSI']}")
        progress_bar.progress((i + 1) / len(tickers))

# عرض النتائج في جدول احترافي
if st.session_state.all_hits:
    st.subheader("📋 قائمة الأسهم الصاعدة حالياً")
    df_results = pd.DataFrame(st.session_state.all_hits)
    st.dataframe(df_results, use_container_width=True)
    
    # رسم شارت لأول سهم صاعد تم رصده كنموذج
    selected = st.selectbox("اختر سهم لمشاهدة الشارت:", df_results['Symbol'])
    # (هنا نضع كود الرسم البياني Plotly الذي استخدمناه سابقاً)
