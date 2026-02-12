import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import requests
import io

# --- 1. إعدادات الصفحة وجلب المفاتيح ---
st.set_page_config(page_title="رادار النخبة v4", layout="wide")

try:
    TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception:
    st.error("⚠️ خطأ في الإعدادات: يرجى التأكد من إضافة TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID في قائمة Secrets.")
    st.stop()

st.title("🏹 رادار قناص السيولة والزخم (النسخة المستقرة)")

# --- 2. وظائف التليجرام والاختبار ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

st.sidebar.header("⚙️ أدوات الفحص")
if st.sidebar.button("🧪 اختبار ربط تليجرام"):
    if send_telegram("🔔 *رسالة اختبار:* نظام الرادار متصل وجاهز للعمل!"):
        st.sidebar.success("✅ تم الإرسال بنجاح!")
    else:
        st.sidebar.error("❌ فشل الإرسال. تحقق من البيانات.")

# --- 3. منطق التحليل الفني ومعالجة البيانات ---
if 'history' not in st.session_state:
    st.session_state.history = []

WATCHLIST = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT', 'META', 'PLTR', 'SMCI', 'COIN', 'MARA']

def analyze_momentum(ticker):
    try:
        # جلب البيانات
        data = yf.download(ticker, period="20d", interval="1h", progress=False)
        if data.empty or len(data) < 25: return None

        # تحويل البيانات إلى قيم مجردة لتجنب أخطاء المقارنة (ValueError)
        close_values = data['Close'].values.flatten()
        volume_values = data['Volume'].values.flatten()

        # حساب المؤشرات
        rsi_series = ta.rsi(pd.Series(close_values), length=14)
        ema_series = ta.ema(pd.Series(close_values), length=20)
        vol_avg_series = pd.Series(volume_values).rolling(window=20).mean()

        # جلب آخر قيم (أرقام فقط)
        last_price = float(close_values[-1])
        last_rsi = float(rsi_series.iloc[-1])
        last_vol = float(volume_values[-1])
        avg_vol = float(vol_avg_series.iloc[-1])
        last_ema = float(ema_series.iloc[-1])

        # الشروط: زخم > 60 ، سعر > متوسط 20 ، سيولة > 1.5 ضعف المتوسط
        if last_rsi > 60 and last_price > last_ema and last_vol > (avg_vol * 1.5):
            return {
                "Time": pd.Timestamp.now().strftime("%H:%M"),
                "Symbol": ticker,
                "Price": f"${last_price:.2f}",
                "RSI": round(last_rsi, 1),
                "Vol_Ratio": f"{round(last_vol / avg_vol, 2)}x"
            }
    except:
        return None
    return None

# --- 4. تشغيل المسح وعرض النتائج ---
if st.button("🚀 ابدأ مسح السوق الآن"):
    with st.spinner("جاري تحليل الأسهم ورصد السيولة..."):
        new_items = 0
        for ticker in WATCHLIST:
            res = analyze_momentum(ticker)
            if res:
                # التحقق من عدم التكرار في الجلسة الحالية
                if not any(d['Symbol'] == ticker for d in st.session_state.history):
                    st.session_state.history.append(res)
                    send_telegram(f"✅ *فرصة مرصودة:* {res['Symbol']}\n💰 السعر: {res['Price']}\n📈 الزخم: {res['RSI']}\n📊 السيولة: {res['Vol_Ratio']}")
                    new_items += 1
        
        if new_items > 0:
            st.success(f"تم العثور على {new_items} فرصة جديدة!")
        else:
            st.info("لا توجد فرص تحقق الشروط في هذه اللحظة.")

# عرض السجل وزر التحميل
if st.session_state.history:
    df_history = pd.DataFrame(st.session_state.history)
    st.subheader("📋 سجل الفرص المكتشفة")
    st.table(df_history)

    # تصدير التقرير
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_history.to_excel(writer, index=False, sheet_name='Signals')
    
    st.download_button(
        label="📥 تحميل سجل الفرص (Excel)",
        data=buffer.getvalue(),
        file_name="radar_report.xlsx",
        mime="application/vnd.ms-excel"
    )
