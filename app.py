import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. إعدادات الهوية والواجهة ---
st.set_page_config(page_title="منصة الفرص الذكية", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. نظام الأسرار والتحديث التلقائي ---
TOKEN_FROM_SECRETS = st.secrets.get("TELEGRAM_TOKEN", "")
ID_FROM_SECRETS = st.secrets.get("TELEGRAM_CHAT_ID", "")

TELEGRAM_TOKEN = TOKEN_FROM_SECRETS if TOKEN_FROM_SECRETS else st.sidebar.text_input("Telegram Token", type="password")
TELEGRAM_CHAT_ID = ID_FROM_SECRETS if ID_FROM_SECRETS else st.sidebar.text_input("Telegram Chat ID")

st_autorefresh(interval=60 * 1000, key="smart_refresh")

if 'sent_alerts' not in st.session_state:
    st.session_state.sent_alerts = set()

# --- 3. الوظائف البرمجية المساندة ---
def send_telegram_msg(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=10)
        except Exception:
            pass

def clean_ticker(ticker):
    return str(ticker).replace('.', '-').strip()

# --- 4. محرك تحليل الفرص الذكي ---
def run_smart_scanner():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        df_raw['Market Cap'] = pd.to_numeric(df_raw['Market Cap'], errors='coerce').fillna(0)
        
        filtered = df_raw[(df_raw['Market Cap'] > 15_000_000) & (df_raw['Volume'] > 150000)]
        watchlist = filtered.sort_values(by='Volume', ascending=False).head(40)
        
        symbols = [clean_ticker(s) for s in watchlist['Symbol']]
        data = yf.download(symbols, period="7d", interval="1h", group_by='ticker', progress=False)
        
        results = []
        for index, row_meta in watchlist.iterrows():
            ticker = clean_ticker(row_meta['Symbol'])
            if ticker not in data or data[ticker].empty: continue
            
            df_t = data[ticker].dropna()
            if len(df_t) < 15: continue
            
            price = df_t['Close'].iloc[-1]
            prev_close = df_t['Close'].iloc[-2]
            change = ((price - prev_close) / prev_close) * 100
            
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # حساب وقف الخسارة والهدف (إدارة مخاطر احترافية)
            volatility = (df_t['High'] - df_t['Low']).mean()
            stop_loss = price - (volatility * 1.5)
            # الهدف: نسبة ربح إلى خسارة 1:2
            risk_amount = price - stop_loss
            target_price = price + (risk_amount * 2) 
            
            action = "مراقبة 👀"
            if rsi < 45 and change > 0.5:
                action = "شراء 🚀"
                if ticker not in st.session_state.sent_alerts:
                    msg = (f"🎯 *فرصة من منصة الفرص الذكية!*\n\n"
                           f"السهم: #{ticker}\n"
                           f"السعر: ${price:.2f}\n"
                           f"الهدف المتوقع: ${target_price:.2f} 💰\n"
                           f"وقف الخسارة: ${stop_loss:.2f} 🛡️\n"
                           f"RSI: {rsi:.1f}")
                    send_telegram_msg(msg)
                    st.session_state.sent_alerts.add(ticker)
            
            results.append({
                "الرمز": ticker, "السعر": round(price, 2), "التغير%": round(change, 2),
                "RSI": round(rsi, 1), "التوصية": action, 
                "الهدف": round(target_price, 2), "الوقف": round(stop_loss, 2)
            })
            
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return pd.DataFrame()

# --- 5. واجهة المستخدم النهائية ---
st.title("🏹 منصة الفرص الذكية | رادار الاقتناص اللحظي")

with st.spinner('جاري قنص أفضل الفرص...'):
    df_results = run_smart_scanner()

if not df_results.empty:
    st.markdown("---")
    col_list, col_chart = st.columns([1, 1.4])
    
    with col_list:
        st.subheader("📋 مصفوفة الفرص")
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        selected = st.selectbox("اختر السهم للتحليل:", df_results['الرمز'].tolist())
    
    with col_chart:
        st.subheader(f"📊 تحليل حركة {selected}")
        chart_raw = yf.download(selected, period="5d", interval="15m", progress=False)
        if isinstance(chart_raw.columns, pd.MultiIndex): chart_raw.columns = chart_raw.columns.get_level_values(0)
            
        if not chart_raw.empty:
            fig = go.Figure(data=[go.Candlestick(x=chart_raw.index, open=chart_raw['Open'], high=chart_raw['High'], low=chart_raw['Low'], close=chart_raw['Close'])])
            
            # رسم خطوط الهدف والوقف على الشارت
            s_info = df_results[df_results['الرمز'] == selected].iloc[0]
            fig.add_hline(y=s_info['الهدف'], line_dash="dash", line_color="#00ff00", annotation_text="Target")
            fig.add_hline(y=s_info['الوقف'], line_dash="dash", line_color="#ff4b4b", annotation_text="Stop Loss")
            
            fig.update_layout(template="plotly_dark", height=480, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("🔎 الرادار يبحث عن فرص دخول مثالية...")
