import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. التصميم الملكي والسيبراني (Final Ultra Design) ---
st.set_page_config(page_title="منصة الفرص الأسطورية - V12.1", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    
    .stApp { 
        background: radial-gradient(circle, #0a0a12 0%, #050505 100%); 
        color: #f0f0f0; 
        font-family: 'Inter', sans-serif; 
    }
    
    h1 { 
        font-family: 'Orbitron', sans-serif; 
        font-size: 3.8rem !important; 
        color: #00ffcc !important; 
        text-align: center; 
        text-shadow: 0 0 20px #00ffcc; 
        margin-top: -30px; 
    }
    
    /* تنسيق الجداول والخطوط الكبيرة */
    .stDataFrame div { 
        font-size: 1.6rem !important; 
        font-weight: 500 !important; 
    }
    
    /* شريط المؤشرات العلوي */
    .ticker-tape { 
        background: rgba(0, 255, 204, 0.05); 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #00ffcc; 
        text-align: center; 
        font-size: 1.3rem; 
        margin-bottom: 25px; 
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محركات التحليل (التقني + السلوكي + الأخبار + الحيتان) ---
st_autorefresh(interval=60 * 1000, key="v12_1_refresh")

def get_market_indices():
    """جلب أداء السوق العام (NASDAQ)"""
    try:
        nasdaq = yf.Ticker("^IXIC")
        hist = nasdaq.history(period="2d")
        if len(hist) >= 2:
            prev_close = hist['Close'].iloc[-2]
            curr_price = hist['Close'].iloc[-1]
            chg = ((curr_price - prev_close) / prev_close) * 100
            return chg
        return 0.0
    except:
        return 0.0

def run_legendary_engine():
    try:
        # تحميل البيانات المرجعية
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw.sort_values(by='Volume', ascending=False).head(35)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب بيانات السوق
        data = yf.download(symbols, period="10d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            ticker_obj = yf.Ticker(ticker)
            
            price = df_t['Close'].iloc[-1]
            change = ((price - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # 1. زخم الحيتان والسيولة
            vol_last = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            whale_activity = vol_last / vol_avg
            
            # 2. التحليل النفسي (RSI + السلوك)
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # 3. دمج الأخبار والسلوك في النسبة
            # قمنا بتبسيط المعادلة لتكون منطقية ومبنية على الزخم والسيولة
            score = (100 - rsi) * (1 + (whale_activity * 0.1))
            if change > 0: score += 10 # حافز الارتداد
            score = min(max(score, 5), 99.9)

            # تحديد الحالة بناءً على تكامل الإشارات
            if score > 85 and whale_activity > 1.8: status = "🐳 انفجار مؤسسات"
            elif score > 75: status = "🎯 قنص ذهبي"
            elif score > 60: status = "👀 مراقبة"
            else: status = "⏳ انتظار"

            results.append({
                "الرمز": ticker,
                "السعر": f"${price:.2f}",
                "قوة الإشارة %": round(score, 1),
                "التغير": f"{change:+.2f}%",
                "الحالة": status,
                "السيولة": "عالية 🔥" if whale_activity > 1.5 else "هادئة 😴"
            })
        
        return pd.DataFrame(results).sort_values(by="قوة الإشارة %", ascending=False)
    except Exception as e:
        return pd.DataFrame()

# --- 3. الواجهة النهائية لغرفة العمليات ---
st.title("🛰️ منصة الفرص الأسطورية")

# شريط الحالة العلوي
nasdaq_perf = get_market_indices()
st.markdown(f"""
<div class="ticker-tape">
    📊 حالة السوق العام (NASDAQ): <span style="color:{'#00ffcc' if nasdaq_perf >= 0 else '#ff4b4b'}; font-weight:bold;">
    {nasdaq_perf:+.2f}% {'📈' if nasdaq_perf >= 0 else '📉'}</span> | 
    رادار السيولة يفحص الآن تحركات الحيتان في 35 سهم قيادي
</div>
""", unsafe_allow_html=True)

df_legend = run_legendary_engine()

if not df_legend.empty:
    # تنسيق الحالات اللونية في الجدول
    def style_status(val):
        if "🐳" in str(val): color = '#00e5ff'
        elif "🎯" in str(val): color = '#00ffcc'
        elif "👀" in str(val): color = '#ffcc00'
        else: color = '#888'
        return f'color: {color}; font-weight: bold; font-size: 1.6rem;'

    st.dataframe(
        df_legend.style.applymap(style_status, subset=['الحالة'])
        .applymap(lambda x: 'color: #00ffcc; font-size: 1.7rem; font-weight: bold;' if float(x) > 75 else 'color: #f0f0f0;', subset=['قوة الإشارة %']),
        use_container_width=True,
        hide_index=True,
        height=900
    )
else:
    st.info("🔎 جاري مزامنة بيانات الحيتان والسيولة... يرجى الانتظار")

st.sidebar.markdown("---")
st.sidebar.write("🏆 **نصيحة المنصة:** ركز دائماً على الأسهم التي تجمع بين 'انفجار المؤسسات' والسيولة العالية 🔥")
