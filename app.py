import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import requests
import io
from datetime import datetime
import base64

# --- 1. إعدادات الصفحة وجلب المفاتيح ---
st.set_page_config(page_title="رادار النخبة 24/7", layout="wide")

try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception:
    st.error("⚠️ يرجى ضبط TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID في Secrets")
    st.stop()

# --- وظيفة التنبيه الصوتي ---
def play_sound():
    # ملف صوتي بسيط (Beep) بصيغة Base64
    audio_html = """
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# --- 2. واجهة المستخدم ---
st.title("🏹 رادار قناص السيولة (يعمل على مدار الساعة 24/7)")
st.info("هذا الرادار يراقب الأسهم باستمرار ويرسل تنبيهات تليجرام مع صوت تنبيه في المتصفح.")

if 'history' not in st.session_state:
    st.session_state.history = []

# قائمة الأسهم الموسعة للسوق الأمريكي
WATCHLIST = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT', 'META', 'PLTR', 'SMCI', 'MARA', 'COIN', 'RIOT', 'MSTR']

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# --- 3. منطق التحليل الفني (بدون قيود زمنية) ---
def analyze_momentum(ticker):
    try:
        # جلب البيانات بفاصل 15 دقيقة لرصد التحركات السريعة
        data = yf.download(ticker, period="5d", interval="15m", progress=False)
        if data.empty or len(data) < 20: return None

        # تنظيف البيانات وتجريدها من الفهارس
        close_np = data['Close'].values.flatten()
        vol_np = data['Volume'].values.flatten()

        # حساب المؤشرات
        rsi = ta.rsi(pd.Series(close_np), length=14).values
        ema20 = ta.ema(pd.Series(close_np), length=20).values
        vol_avg = pd.Series(vol_np).rolling(window=20).mean().values

        # جلب آخر قيم
        last_price = float(close_np[-1])
        last_rsi = float(rsi[-1])
        last_vol = float(vol_np[-1])
        avg_vol = float(vol_avg[-1])
        current_ema = float(ema20[-1])

        # شروط الرادار: زخم فوق 60 وسعر فوق المتوسط وسيولة أعلى من المتوسط
        if last_rsi > 60 and last_price > current_ema and last_vol > (avg_vol * 1.3):
            return {
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Symbol": ticker,
                "Price": f"${last_price:.2f}",
                "RSI": round(last_rsi, 1),
                "Vol_Ratio": f"{round(last_vol / avg_vol, 2)}x"
            }
    except:
        return None
    return None

# --- 4. التحكم والتشغيل ---
st.sidebar.header("🛠 التحكم")
if st.sidebar.button("🧪 اختبار تليجرام + الصوت"):
    send_telegram("🔔 اختبار الرادار: الاتصال يعمل!")
    play_sound()
    st.sidebar.success("تم إرسال الرسالة وتشغيل الصوت")

if st.button("🚀 ابدأ المسح الشامل"):
    with st.spinner("جاري فحص السوق الآن..."):
        new_found = False
        for ticker in WATCHLIST:
            res = analyze_momentum(ticker)
            if res:
                # التحقق من عدم التكرار
                if not any(d['Symbol'] == ticker for d in st.session_state.history):
                    st.session_state.history.append(res)
                    send_telegram(f"🔥 *فرصة رادار:* {res['Symbol']}\n💰 السعر: {res['Price']}\n📈 RSI: {res['RSI']}\n📊 سيولة: {res['Vol_Ratio']}")
                    play_sound() # تشغيل الصوت عند وجود فرصة جديدة
                    new_found = True
        
        if new_found:
            st.success("تم اكتشاف فرص جديدة!")
        else:
            st.info("لا توجد فرص تحقق الشروط في هذه اللحظة. الرادار مستمر في المراقبة.")

# عرض النتائج
if st.session_state.history:
    df_history = pd.DataFrame(st.session_state.history)
    st.subheader("📋 السجل التراكمي للفرص")
    st.table(df_history)

    # تصدير التقرير
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_history.to_excel(writer, index=False, sheet_name='All_Signals')
    
    st.download_button("📥 تحميل التقرير الشامل (Excel)", data=buffer.getvalue(), file_name="radar_full_report.xlsx")
