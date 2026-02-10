import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. هندسة الهوية البصرية (CSS Pro) ---
st.set_page_config(page_title="منصة الفرص الذكية", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    /* توحيد الخلفية والخط */
    .stApp {
        background-color: #0e1117;
        font-family: 'Inter', sans-serif;
        color: #e0e0e0;
    }
    
    /* تخصيص العناوين */
    h1, h2, h3 {
        color: #00ffcc !important;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.3);
    }

    /* تحسين شكل البطاقات والجداول */
    .stDataFrame {
        border: 1px solid #333;
        border-radius: 10px;
    }
    
    /* تخصيص مربعات الإحصائيات */
    div[data-testid="stMetricValue"] {
        color: #00ffcc !important;
        font-size: 1.8rem !important;
    }

    /* إلغاء الحواف البيضاء في الشارت */
    .js-plotly-plot {
        border-radius: 15px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك البيانات المحدث ---
TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
st_autorefresh(interval=60 * 1000, key="v5_refresh")

def get_styled_data():
    try:
        df = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # اختيار النخبة بناءً على حجم التداول
        watchlist = df.sort_values(by='Volume', ascending=False).head(35)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="5d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            
            price = df_t['Close'].iloc[-1]
            change = ((price - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # حساب RSI
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            action = "مراقبة"
            if rsi < 42 and change > 0: action = "🎯 اقتناص"
            
            results.append({
                "الرمز": ticker, 
                "السعر": f"${price:.2f}", 
                "التغير%": f"{change:+.2f}%", 
                "RSI": round(rsi, 1), 
                "الحالة": action
            })
        return pd.DataFrame(results)
    except: return pd.DataFrame()

# --- 3. بناء واجهة المستخدم المتناسقة ---
st.title("🎯 منصة الفرص الذكية")
st.write(f"📡 الرادار نشط الآن | {datetime.now().strftime('%H:%M:%S')}")

df_final = get_styled_data()

if not df_final.empty:
    # تقسيم العرض
    col_table, col_chart = st.columns([1, 1.5])
    
    with col_table:
        st.subheader("📋 رادار السوق")
        # عرض الجدول بتصميم متناسق
        st.dataframe(
            df_final.style.applymap(
                lambda x: 'color: #00ffcc; font-weight: bold' if '🎯' in str(x) else 'color: #e0e0e0',
                subset=['الحالة']
            ).applymap(
                lambda x: 'color: #00ffcc' if '+' in str(x) else 'color: #ff4b4b',
                subset=['التغير%']
            ),
            use_container_width=True,
            hide_index=True
        )
        selected_ticker = st.selectbox("اختر السهم للتحليل:", df_final['الرمز'].tolist())

    with col_chart:
        st.subheader(f"📊 نبض السعر: {selected_ticker}")
        hist = yf.download(selected_ticker, period="5d", interval="15m", progress=False)
        if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
        
        # تصميم شارت متناسق مع الخلفية
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'],
            low=hist['Low'], close=hist['Close'],
            increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b'
        )])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_rangeslider_visible=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("🔎 جاري مزامنة بيانات السوق الأمريكي...")
