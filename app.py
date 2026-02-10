import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. التصميم الملكي (Royal Cyber Design) ---
st.set_page_config(page_title="منصة الفرص - النسخة الأسطورية", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.8rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; margin-top: -50px; }
    
    /* تكبير نصوص الجدول بشكل فائق */
    .stDataFrame div { font-size: 1.8rem !important; font-weight: 500 !important; }
    
    .status-badge { padding: 10px 20px; border-radius: 30px; font-weight: bold; font-size: 1.4rem; text-align: center; }
    
    /* شريط المؤشرات العلوي */
    .ticker-tape { background: rgba(0, 255, 204, 0.05); padding: 10px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; font-size: 1.2rem; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك الذكاء والبيانات ---
st_autorefresh(interval=60 * 1000, key="v12_refresh")

def get_market_indices():
    """جلب حالة السوق العام"""
    try:
        indices = yf.download(["^IXIC", "^GSPC", "BTC-USD"], period="1d", interval="15m", progress=False)['Close']
        nasdaq_chg = ((indices['^IXIC'].iloc[-1] - indices['^IXIC'].iloc[0]) / indices['^IXIC'].iloc[0]) * 100
        return nasdaq_chg
    except: return 0

def run_legendary_engine():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # تصفية النخبة (أعلى 35 سهم سيولة)
        watchlist = df_raw.sort_values(by='Volume', ascending=False).head(35)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="10d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            
            price = df_t['Close'].iloc[-1]
            change = ((price - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # 1. حساب زخم الحيتان (Whale Momentum)
            vol_last = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            whale_activity = vol_last / vol_avg
            
            # 2. تحليل الخبر والسلوك
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # معادلة "نسبة النجاح الأسطورية"
            score = (100 - rsi) * (1 + (whale_activity * 0.15))
            if change > 0: score += 10
            score = min(max(score, 5), 99.5)

            # تحديد الحالة بناءً على تجميع الإشارات
            if score > 85 and whale_activity > 2: status = "🐳 انفجار مؤسسات"
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
    except: return pd.DataFrame()

# --- 3. الواجهة النهائية ---
st.title("🛰️ منصة الفرص الأسطورية")

# شريط المؤشرات
nasdaq_perf = get_market_indices()
st.markdown(f"""
<div class="ticker-tape">
    📊 حالة السوق العام (NASDAQ): <span style="color:{'#00ffcc' if nasdaq_perf > 0 else '#ff4b4b'}; font-weight:bold;">
    {nasdaq_perf:+.2f}% {'📈' if nasdaq_perf > 0 else '📉'}</span> | 
    النظام الآن يقوم بمسح تدفق السيولة لـ 35 سهم قيادي
</div>
""", unsafe_allow_html=True)

df_legend = run_legendary_engine()

if not df_legend.empty:
    def style_final(val):
        if "🐳" in str(val): color = '#00e5ff'; weight = 'bold'
        elif "🎯" in str(val): color = '#00ffcc'; weight = 'bold'
        elif "👀" in str(val): color = '#ffcc00'; weight = 'normal'
        else: color = '#777'; weight = 'normal'
        return f'color: {color}; font-weight: {weight}; font-size: 1.7rem;'

    st.dataframe(
        df_legend.style.applymap(style_final, subset=['الحالة'])
        .applymap(lambda x: 'color: #00ffcc; font-size: 1.8rem; font-weight: bold;' if float(x) > 75 else 'color: #ccc;', subset=['قوة الإشارة %']),
        use_container_width=True,
        hide_index=True,
        height=900
    )
else:
    st.info("🔎 جاري تشغيل محركات البحث عن الحيتان والسيولة... يرجى الانتظار.")
