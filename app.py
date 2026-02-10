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
    h1, h2, h3 { color: #00ffcc !important; text-shadow: 0 0 8px rgba(0, 255, 204, 0.2); }
    /* تحسين شكل الجدول */
    .stDataFrame { border: 1px solid #333; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك الحسابات والترتيب بالأفضلية ---
st_autorefresh(interval=60 * 1000, key="v7_refresh")

def get_ranked_opportunities():
    try:
        # قراءة البيانات الأساسية
        df = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df.sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب بيانات السوق
        data = yf.download(symbols, period="7d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            
            current_price = df_t['Close'].iloc[-1]
            change = ((current_price - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # حساب RSI لتحويله لنسبة دخول
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # معادلة "قوة الدخول" المبتكرة
            entry_confidence = 100 - rsi
            if change > 0: entry_confidence += 10 # دعم إضافي عند الارتداد الإيجابي
            entry_confidence = min(max(entry_confidence, 5), 98) 
            
            # حساب المخاطرة
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
        
        # تحويل النتائج لجدول
        final_df = pd.DataFrame(results)
        
        # --- الترتيب بالأفضلية (السر السحري) ---
        # نقوم بترتيب الجدول بناءً على "قوة الدخول %" من الأعلى للأقل
        if not final_df.empty:
            final_df = final_df.sort_values(by="قوة الدخول %", ascending=False).reset_index(drop=True)
            
        return final_df
    except: return pd.DataFrame()

# --- 3. عرض الواجهة النهائية ---
st.title("🏹 منصة الفرص الذكية | ترتيب الأفضلية")

df_final = get_ranked_opportunities()

if not df_final.empty:
    col_t, col_c = st.columns([1.2, 1.8])
    
    with col_t:
        st.subheader("🔝 أفضل الفرص الحالية")
        
        # تنسيق ألوان النسب
        def style_rows(val):
            color = '#00ffcc' if val > 75 else '#ffcc00' if val > 50 else '#ff4b4b'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_final.style.applymap(style_rows, subset=['قوة الدخول %'])
            .applymap(lambda x: 'color: #ff4b4b' if float(x) > 4 else 'color: #00ffcc', subset=['المخاطرة %']),
            use_container_width=True, hide_index=True
        )
        # اختيار السهم الأول في الترتيب تلقائياً ليكون هو المعروض في الشارت
        default_ticker = df_final['الرمز'].iloc[0]
        selected_ticker = st.selectbox("حلل السهم المختار:", df_final['الرمز'].tolist(), index=0)

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
    st.info("🔎 جاري البحث عن أفضل الفرص المتاحة في السوق الأمريكي...")
