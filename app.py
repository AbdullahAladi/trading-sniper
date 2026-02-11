import streamlit as st
import yfinance as yf
import pandas_ta as ta
import requests
import pandas as pd

# --- استدعاء الإعدادات من Secrets ---
TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# --- إعدادات الصفحة ---
st.set_page_config(page_title="رادار النخبة للأسهم", layout="wide")
st.title("🚀 رادار النخبة - فرصة التداول الذكية")

# قائمة الأسهم (يمكنك جعلها مدخلات من المستخدم في الواجهة)
default_stocks = ['AAPL', 'TSLA', 'NVDA', '2222.SR', '1120.SR', '4110.SR']
selected_stocks = st.sidebar.multiselect("اختر الأسهم للمراقبة", default_stocks, default_stocks)

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        st.error(f"خطأ في إرسال التليجرام: {e}")

def analyze_stock(ticker):
    # جلب البيانات
    df = yf.download(ticker, period="60d", interval="1h", progress=False)
    if df.empty or len(df) < 50:
        return None

    # حساب المؤشرات فنية
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['EMA_50'] = ta.ema(df['Close'], length=50)

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    # شروط الاستراتيجية (تغيير السلوك السعري)
    price_breakout = (prev_row['Close'] < prev_row['EMA_20']) and (last_row['Close'] > last_row['EMA_20'])
    is_bullish = last_row['RSI'] > 50
    is_uptrend = last_row['Close'] > last_row['EMA_50']

    if price_breakout and is_bullish and is_uptrend:
        return {
            'Symbol': ticker,
            'Price': round(float(last_row['Close']), 2),
            'RSI': round(float(last_row['RSI']), 2),
            'Signal': "🔥 اختراق إيجابي"
        }
    return None

# --- واجهة المستخدم ---
if st.button('ابدأ المسح الآن 🔍'):
    st.write("جاري فحص الأسهم المختارة...")
    found_opportunities = []
    
    for ticker in selected_stocks:
        result = analyze_stock(ticker)
        if result:
            found_opportunities.append(result)
            # إرسال تنبيه للتليجرام
            msg = f"✅ *فرصة جديدة:* {ticker}\n💰 *السعر:* {result['Price']}\n📈 *RSI:* {result['RSI']}"
            send_telegram_msg(msg)

    if found_opportunities:
        st.success(f"تم العثور على {len(found_opportunities)} فرصة صاعدة!")
        st.table(pd.DataFrame(found_opportunities))
    else:
        st.warning("لا توجد فرص مطابقة للشروط حالياً. جرب لاحقاً.")

st.info("ملاحظة: الكود يفحص الفاصل الزمني (ساعة) لآخر 60 يوم عمل.")
