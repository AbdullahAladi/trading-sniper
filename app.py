import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import requests
import io

# --- جلب الإعدادات من Secrets ---
try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception:
    st.error("⚠️ تأكد من إضافة TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID في قائمة Secrets")
    st.stop()

st.set_page_config(page_title="رادار النخبة v3", layout="wide")
st.title("🏹 رادار قناص السيولة (الإصدار المستقر)")

if 'history' not in st.session_state:
    st.session_state.history = []

# قائمة الأسهم (يفضل البدء بقائمة صغيرة للتأكد من العمل)
WATCHLIST = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT', 'META', 'PLTR', 'SMCI']

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try: requests.get(url, timeout=5)
    except: pass

def analyze_momentum(ticker):
    try:
        # جلب البيانات والتأكد من أنها نظيفة
        data = yf.download(ticker, period="20d", interval="1h", progress=False)
        if data.empty or len(data) < 30: 
            return None

        # استخدام numpy لمعالجة القيم لتجنب خطأ Series Objects (الصورة 3)
        close_prices = data['Close'].values.flatten()
        volumes = data['Volume'].values.flatten()

        # حساب المؤشرات يدوياً عبر pandas_ta لضمان الدقة
        rsi = ta.rsi(pd.Series(close_prices), length=14).values
        ema20 = ta.ema(pd.Series(close_prices), length=20).values
        
        # حساب متوسط السيولة
        vol_series = pd.Series(volumes)
        vol_avg = vol_series.rolling(window=20).mean().values

        # جلب آخر قيم مسجلة (القيم الأخيرة في المصفوفة)
        last_price = close_prices[-1]
        last_rsi = rsi[-1]
        last_vol = volumes[-1]
        current_vol_avg = vol_avg[-1]
        current_ema = ema20[-1]

        # فحص الشروط باستخدام أرقام مجردة (Floats)
        is_bullish = float(last_rsi) > 60
        is_above_ema = float(last_price) > float(current_ema)
        is_high_volume = float(last_vol) > (float(current_vol_avg) * 1.5)

        if is_bullish and is_above_ema and is_high_volume:
            return {
                "Time": pd.Timestamp.now().strftime("%H:%M"),
                "Symbol": ticker,
                "Price": round(float(last_price), 2),
                "RSI": round(float(last_rsi), 1),
                "Vol_Ratio": round(float(last_vol / current_vol_avg), 2)
            }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None
    return None

# --- واجهة التحكم ---
if st.button("🚀 ابدأ المسح الآن"):
    with st.spinner(f"جاري فحص {len(WATCHLIST)} سهم..."):
        new_hits = 0
        for ticker in WATCHLIST:
            res = analyze_momentum(ticker)
            if res:
                # التحقق من عدم التكرار
                if not any(d['Symbol'] == ticker for d in st.session_state.history):
                    st.session_state.history.append(res)
                    msg = f"✅ *إشارة رادار:* {ticker}\n💰 السعر: ${res['Price']}\n📊 قوة السيولة: {res['Vol_Ratio']}x"
                    send_telegram(msg)
                    new_hits += 1
        
        if new_hits > 0:
            st.success(f"تم العثور على {new_hits} فرص جديدة!")
        else:
            st.info("لا توجد فرص تحقق الشروط حالياً. جرب سهم PLTR أو NVDA كاختبار.")

# عرض النتائج وتصديرها
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.table(df)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button("📥 تحميل التقرير (Excel)", data=buffer.getvalue(), file_name="radar_hits.xlsx")
