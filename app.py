import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import requests
import io

# --- 1. جلب الإعدادات بأمان ---
try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception:
    st.error("⚠️ خطأ: المفاتيح غير موجودة في Secrets. تأكد من إضافة TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID.")
    st.stop()

st.set_page_config(page_title="رادار النخبة المطور", layout="wide")
st.title("🏹 رادار قناص السيولة والزخم")

# --- وظائف التليجرام ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"خطأ في الاتصال بتليجرام: {e}")
        return False

# --- 2. زر الاختبار (Test Connection) ---
st.sidebar.header("أدوات الفحص")
if st.sidebar.button("🧪 اختبار ربط تليجرام"):
    success = send_telegram("🔔 *رسالة اختبار:* الربط مع رادار النخبة يعمل بنجاح!")
    if success:
        st.sidebar.success("✅ تم إرسال رسالة الاختبار بنجاح!")
    else:
        st.sidebar.error("❌ فشل الإرسال. تحقق من التوكن والآيدي.")

# --- 3. منطق التحليل الفني ---
if 'history' not in st.session_state:
    st.session_state.history = []

WATCHLIST = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT', 'META', 'PLTR', 'SMCI', 'MARA', 'COIN']

def analyze_momentum(ticker):
    try:
        # جلب البيانات (استخدام فترة أطول لضمان استقرار المتوسطات)
        data = yf.download(ticker, period="30d", interval="1h", progress=False)
        if data.empty or len(data) < 25: return None

        # تجريد البيانات من الفهارس لتجنب أخطاء pandas (ValueError)
        close_np = data['Close'].values.flatten()
        vol_np = data['Volume'].values.flatten()

        # حساب المؤشرات باستخدام pandas_ta
        rsi = ta.rsi(pd.Series(close_np), length=14).values
        ema20 = ta.ema(pd.Series(close_np), length=20).values
        vol_avg = pd.Series(vol_np).rolling(window=20).mean().values

        # جلب القيم الأخيرة
        last_price = float(close_np[-1])
        last_rsi = float(rsi[-1])
        last_vol = float(vol_np[-1])
        current_vol_avg = float(vol_avg[-1])
        current_ema = float(ema20[-1])

        # شروط الرادار (زخم عالي + سيولة انفجارية + اتجاه صاعد)
        if last_rsi > 60 and last_price > current_ema and last_vol > (current_vol_avg * 1.5):
            return {
                "Time": pd.Timestamp.now().strftime("%H:%M"),
                "Symbol": ticker,
                "Price": f"${last_price:.2f}",
                "RSI": round(last_rsi, 1),
                "Vol_Ratio": f"{round(last_vol / current_vol_avg, 2)}x"
            }
    except:
        return None
    return None

# --- 4. تشغيل الرادار ---
if st.button("🚀 ابدأ فحص الأسهم الآن"):
    with st.spinner("جاري مسح السوق ورصد السيولة..."):
        found = False
        for ticker in WATCHLIST:
            res = analyze_momentum(ticker)
            if res:
                if not any(d['Symbol'] == ticker for d in st.session_state.history):
                    st.session_state.history.append(res)
                    msg = f"✅ *فرصة صاعدة:* {res['Symbol']}\n💰 السعر: {res['Price']}\n📈 الزخم: {res['RSI']}\n📊 تضاعف السيولة: {res['Vol_Ratio']}"
                    send_telegram(msg)
                    found = True
        
        if found:
            st.success("تم رصد فرص جديدة وإرسال التنبيهات!")
        else:
            st.info("لا توجد فرص تحقق الشروط حالياً. حاول مجدداً عند افتتاح السوق الأمريكي.")

# عرض النتائج وتصدير التقرير
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.subheader("📋 سجل الفرص المكتشفة")
    st.table(df)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Signals')
    
    st.download_button("📥 تحميل سجل
