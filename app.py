import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# --- 1. إعدادات التليجرام من Secrets ---
TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# --- 2. تحديث تلقائي كل 10 دقائق ---
st_autorefresh(interval=10 * 60 * 1000, key="datarefresh")

st.set_page_config(page_title="رادار الزخم والسيولة", layout="wide")
st.title("🏹 رادار قناص السيولة (السوق الأمريكي)")

# قائمة بأسهم قيادية وأسهم نمو للمراقبة (يمكنك توسيعها)
WATCHLIST = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'MSFT', 'META', 'AMZN', 'NFLX', 'GOOGL', 'PLTR', 'SMCI', 'COIN']

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    requests.get(url)

def analyze_momentum(ticker):
    # جلب بيانات الساعة لآخر 20 يوم لضمان الدقة في رصد الزخم اللحظي
    data = yf.download(ticker, period="20d", interval="1h", progress=False)
    if data.empty or len(data) < 30:
        return None

    # --- المؤشرات الفنية ---
    # 1. الزخم (RSI)
    data['RSI'] = ta.rsi(data['Close'], length=14)
    
    # 2. الاتجاه (EMA 20 & 50)
    data['EMA20'] = ta.ema(data['Close'], length=20)
    data['EMA50'] = ta.ema(data['Close'], length=50)
    
    # 3. السيولة (نسبة حجم التداول الحالي مقارنة بالمتوسط)
    data['Vol_Avg'] = data['Volume'].rolling(window=20).mean()
    
    last = data.iloc[-1]
    prev = data.iloc[-2]

    # --- شروط "قناص السيولة" ---
    # شرط الزخم: RSI فوق 60 (دخول في منطقة القوة)
    momentum_score = last['RSI'] > 60
    
    # شرط السيولة: حجم التداول الحالي أكبر بـ 1.5 مرة من المتوسط (دخول سيولة)
    volume_spike = last['Volume'] > (last['Vol_Avg'] * 1.5)
    
    # شرط الاتجاه: السعر فوق المتوسطات والمتوسط الصغير فوق الكبير
    trend_ok = last['Close'] > last['EMA20'] and last['EMA20'] > last['EMA50']

    if momentum_score and trend_ok and volume_spike:
        return {
            "Symbol": ticker,
            "Price": round(last['Close'], 2),
            "RSI": round(last['RSI'], 1),
            "Vol_Ratio": round(last['Volume'] / last['Vol_Avg'], 2),
            "Change": round(((last['Close'] - prev['Close']) / prev['Close']) * 100, 2)
        }
    return None

# --- واجهة المستخدم ---
st.sidebar.header("إعدادات الرادار")
check_list = st.sidebar.multiselect("عدل قائمة المراقبة:", WATCHLIST, default=WATCHLIST)

if st.sidebar.button("فحص يدوي الآن"):
    st.rerun()

st.subheader("⚠️ الأسهم التي تخترق الآن بسيولة عالية")
cols = st.columns(3)

found_any = False
results_list = []

for i, ticker in enumerate(check_list):
    res = analyze_momentum(ticker)
    if res:
        found_any = True
        results_list.append(res)
        with cols[i % 3]:
            st.success(f"🔥 **{ticker}**")
            st.metric("السعر", f"${res['Price']}", f"{res['Change']}%")
            st.write(f"📈 قوة الزخم (RSI): {res['RSI']}")
            st.write(f"💰 انفجار السيولة: {res['Vol_Ratio']}x")
            
            # إرسال تنبيه تليجرام
            alert_msg = (f"🚀 *إشارة دخول ذكية*\n\n"
                         f"السهم: {ticker}\n"
                         f"السعر: ${res['Price']}\n"
                         f"الزخم (RSI): {res['RSI']}\n"
                         f"تضاعف السيولة: {res['Vol_Ratio']} مرة\n"
                         f"النمو اللحظي: {res['Change']}%")
            send_telegram(alert_msg)

if not found_any:
    st.info("لا توجد أسهم تحقق شروط الزخم والسيولة العالية في هذه اللحظة. الرادار سيستمر بالبحث...")

# عرض جدول البيانات العام
if results_list:
    st.divider()
    st.write("### ملخص الفرص المرصودة")
    df_res = pd.DataFrame(results_list)
    st.dataframe(df_res, use_container_width=True)
