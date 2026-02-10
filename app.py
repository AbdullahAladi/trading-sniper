import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time
from datetime import datetime, time as dt_time
from streamlit_autorefresh import st_autorefresh

# --- 1. الإعدادات الأساسية والأمنية ---
st.set_page_config(page_title="منصة الفرص الاحترافية V4.0", layout="wide", page_icon="🚀")

# ضع بياناتك هنا أو ادخلها عبر الواجهة
TELEGRAM_TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
TELEGRAM_CHAT_ID = st.sidebar.text_input("Telegram Chat ID")

# --- 2. التحديث التلقائي ---
# تحديث تلقائي كل 60 ثانية لضمان عمل الرادار باستمرار
st_autorefresh(interval=60 * 1000, key="data_refresh")


# --- 3. وظائف المساعدة (Utility Functions) ---
def send_telegram_msg(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=10)
        except:
            pass


def clean_ticker(ticker):
    return str(ticker).replace('.', '-').strip()


# --- 4. المحرك الرئيسي للتحليل ---
def run_market_radar():
    try:
        # قراءة وتجهيز البيانات
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        df_raw['Market Cap'] = pd.to_numeric(df_raw['Market Cap'], errors='coerce').fillna(0)

        # فلترة الأسهم النشطة والمتوسطة (إدارة مخاطر)
        filtered = df_raw[(df_raw['Market Cap'] > 15_000_000) & (df_raw['Volume'] > 200000)]
        watchlist = filtered.sort_values(by='Volume', ascending=False).head(40)

        symbols = [clean_ticker(s) for s in watchlist['Symbol']]

        # جلب البيانات (7 أيام للحصول على RSI دقيق)
        data = yf.download(symbols, period="7d", interval="1h", group_by='ticker', progress=False)

        results = []
        for index, row_meta in watchlist.iterrows():
            ticker = clean_ticker(row_meta['Symbol'])
            if ticker not in data or data[ticker].empty: continue

            df_t = data[ticker].dropna()
            if len(df_t) < 15: continue

            # الحسابات الفنية
            price = df_t['Close'].iloc[-1]
            prev_close = df_t['Close'].iloc[-2]
            change = ((price - prev_close) / prev_close) * 100

            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]

            # منطق إدارة المخاطر (ATR مبسط)
            volatility = (df_t['High'] - df_t['Low']).mean()
            stop_loss = price - (volatility * 1.5)

            action = "انتظار 🟡"
            if rsi < 45 and change > 0.5:
                action = "شراء 🚀"
                # إرسال تنبيه تليجرام (مرة واحدة فقط)
                if ticker not in st.session_state.sent_alerts:
                    msg = f"🎯 *إشارة فرصة!*\nالسهم: #{ticker}\nالسعر: ${price:.2f}\nالهدف التقريبي: ${price + volatility:.2f}\nالوقف: ${stop_loss:.2f}"
                    send_telegram_msg(msg)
                    st.session_state.sent_alerts.add(ticker)
            elif rsi > 70:
                action = "بيع 💰"

            results.append({
                "الرمز": ticker, "السعر": round(price, 2), "التغير%": round(change, 2),
                "RSI": round(rsi, 1), "التوصية": action, "وقف الخسارة": round(stop_loss, 2)
            })

        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"خطأ في المحرك: {e}")
        return pd.DataFrame()


# --- 5. واجهة المستخدم الرئيسية ---
if 'sent_alerts' not in st.session_state: st.session_state.sent_alerts = set()

st.title("🏹 منصة القناص | الإصدار المتكامل V4.0")

# إحصائيات سريعة
col_stats1, col_stats2, col_stats3 = st.columns(3)

with st.spinner('جاري فحص السوق...'):
    df_results = run_market_radar()

if not df_results.empty:
    col_stats1.metric("الأسهم المكتشفة", len(df_results))
    col_stats2.metric("فرص الشراء حالياً", len(df_results[df_results['التوصية'] == "شراء 🚀"]))
    col_stats3.metric("توقيت النظام", datetime.now().strftime("%H:%M:%S"))

    st.markdown("---")

    col_t, col_c = st.columns([1, 1.2])

    with col_t:
        st.subheader("📋 رادار الفرص")
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        selected = st.selectbox("اختر السهم للشارت:", df_results['الرمز'].tolist())

    with col_c:
        st.subheader(f"📊 شارت {selected}")
        chart_data = yf.download(selected, period="5d", interval="15m", progress=False)
        if isinstance(chart_data.columns, pd.MultiIndex): chart_data.columns = chart_data.columns.get_level_values(0)

        fig = go.Figure(data=[
            go.Candlestick(x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], low=chart_data['Low'],
                           close=chart_data['Close'])])
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=5, r=5, t=5, b=5),
                          xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("🔎 الرادار يعمل... بانتظار إشارات من السوق.")

if st.sidebar.button("تصفير الذاكرة والتنبيهات"):
    st.session_state.sent_alerts = set()

    st.rerun()
