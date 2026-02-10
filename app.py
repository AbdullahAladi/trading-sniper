import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية (تنسيق الألوان والخطوط) ---
st.set_page_config(page_title="منصة الفرص الذكية", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    .stApp { background-color: #0e1117; font-family: 'Inter', sans-serif; color: #e0e0e0; }
    h1, h2, h3 { color: #00ffcc !important; }
    /* تخصيص عمود النسبة المئوية */
    .perc-high { color: #00ffcc; font-weight: bold; }
    .perc-med { color: #ffcc00; }
    .perc-low { color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك الحسابات (تحويل RSI إلى نسبة مئوية) ---
st_autorefresh(interval=60 * 1000, key="v6_refresh")

def calculate_entry_score():
    try:
        df = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df.sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="7d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            
            # حساب السعر والتغير
            current_price = df_t['Close'].iloc[-1]
            change = ((current_price - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # حساب RSI لتحويله إلى نسبة دخول
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # تحويل RSI إلى نسبة دخول (كلما قل RSI زادت نسبة قوة الدخول)
            # معادلة عكسية: RSI 30 يعطي قوة دخول 85% تقريباً
            entry_confidence = 100 - rsi
            # تعديل بسيط لإعطاء وزن أكبر إذا كان هناك ارتداد سعري إيجابي
            if change > 0: entry_confidence += 10
            entry_confidence = min(max(entry_confidence, 5), 98) # حصر النسبة بين 5% و 98%
            
            # حساب نسبة المخاطرة (بناءً على التذبذب)
            volatility = (df_t['High'] - df_t['Low']).mean()
            risk_pct = (volatility / current_price) * 100
            
            action = "انتظار"
            if entry_confidence > 75: action = "🎯 اقتناص الآن"
            elif entry_confidence > 60: action = "👀 مراقبة"

            results.append({
                "الرمز": ticker,
                "السعر": f"${current_price:.2f}",
                "قوة الدخول %": round(entry_confidence, 1),
                "المخاطرة %": round(risk_pct, 1),
                "التغير": f"{change:+.2f}%",
                "الحالة": action
            })
        return pd.DataFrame(results)
    except: return pd.DataFrame()

# --- 3. عرض الواجهة النهائية المتناسقة ---
st.title("🎯 منصة الفرص الذكية | رادار النسب المئوية")

df_final = calculate_entry_score()

if not df_final.empty:
    col_t, col_c = st.columns([1.2, 1.8])
    
    with col_t:
        st.subheader("📡 احتمالات الدخول")
        
        # تنسيق الجدول بالألوان بناءً على النسب
        def style_confidence(val):
            color = '#00ffcc' if val > 75 else '#ffcc00' if val > 50 else '#ff4b4b'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_final.style.applymap(style_confidence, subset=['قوة الدخول %'])
            .applymap(lambda x: 'color: #ff4b4b' if float(x) > 4 else 'color: #00ffcc', subset=['المخاطرة %']),
            use_container_width=True, hide_index=True
        )
        selected_ticker = st.selectbox("حلل السهم المختار:", df_final['الرمز'].tolist())

    with col_c:
        st.subheader(f"📊 نبض السوق: {selected_ticker}")
        hist = yf.download(selected_ticker, period="5d", interval="15m", progress=False)
        if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
        
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'],
            low=hist['Low'], close=hist['Close'],
            increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b'
        )])
        
        fig.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0), height=500
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("🔎 جاري تحليل احتمالات الدخول في السوق الأمريكي...")
