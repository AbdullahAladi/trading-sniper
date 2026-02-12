import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import io

# --- محاولة جلب الإعدادات بأمان ---
try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception:
    st.error("⚠️ خطأ: يرجى إضافة التوكن والآيدي في Secrets")
    st.stop()

st.title("🏹 رادار قناص السيولة (السوق الأمريكي)")

if 'history' not in st.session_state:
    st.session_state.history = []

WATCHLIST = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT', 'META', 'PLTR', 'SMCI']

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try: requests.get(url)
    except: pass

def analyze_momentum(ticker):
    try:
        data = yf.download(ticker, period="15d", interval="1h", progress=False)
        if data.empty or len(data) < 20: return None

        # حساب المؤشرات
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['EMA20'] = ta.ema(data['Close'], length=20)
        # استخدام .values لتجنب خطأ التسمية (الصورة الثالثة)
        vol_avg = data['Volume'].rolling(window=20).mean()
        
        last_price = float(data['Close'].iloc[-1])
        last_rsi = float(data['RSI'].iloc[-1])
        last_vol = float(data['Volume'].iloc[-1])
        avg_vol = float(vol_avg.iloc[-1])
        last_ema = float(data['EMA20'].iloc[-1])

        # شروط الاختراق
        if last_rsi > 60 and last_price > last_ema and last_vol > (avg_vol * 1.5):
            return {
                "Time": pd.Timestamp.now().strftime("%H:%M"),
                "Symbol": ticker,
                "Price": round(last_price, 2),
                "RSI": round(last_rsi, 1),
                "Vol_Ratio": round(last_vol / avg_vol, 2)
            }
    except:
        return None
    return None

# --- الواجهة البرمجية ---
if st.button("🚀 فحص الأسهم الآن"):
    with st.spinner("جاري تحليل السيولة..."):
        for ticker in WATCHLIST:
            res = analyze_momentum(ticker)
            if res:
                if not any(d['Symbol'] == ticker for d in st.session_state.history):
                    st.session_state.history.append(res)
                    send_telegram(f"✅ *فرصة:* {ticker}\n💰 السعر: ${res['Price']}\n📊 السيولة: {res['Vol_Ratio']}x")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.write("### الفرص المرصودة")
    st.dataframe(df, use_container_width=True)
    
    # تحويل للتحميل
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button("📥 تحميل تقرير Excel", data=buffer.getvalue(), file_name="radar_report.xlsx")
else:
    st.info("لا توجد فرص حالياً. تأكد من أن السوق الأمريكي مفتوح.")
