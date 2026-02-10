import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. تصميم غرفة العمليات (CSS Pro) ---
st.set_page_config(page_title="منصة الفرص الذكية - Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@400;700&display=swap');
    
    .stApp { background-color: #050505; color: #f0f0f0; font-family: 'Inter', sans-serif; }
    
    /* العناوين بنمط سيبراني */
    h1 { 
        font-family: 'Orbitron', sans-serif; 
        font-size: 3.5rem !important; 
        color: #00ffcc !important; 
        text-align: center; 
        text-shadow: 0 0 15px #00ffcc;
    }

    /* تكبير نصوص الجداول */
    .stDataFrame div { font-size: 1.6rem !important; }
    
    /* تنسيق خاص للقطاعات والقوة */
    .sector-box {
        padding: 15px;
        border-radius: 10px;
        background: #1e1e1e;
        border-left: 5px solid #00ffcc;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. المحرك الذكي (الزخم + القطاعات + الاحتمالات) ---
st_autorefresh(interval=60 * 1000, key="v9_refresh")

def run_smart_engine():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        
        # 1. تحليل قوة القطاعات (Sector Strength)
        sector_summary = df_raw.groupby('Sector')['Net Change'].mean().sort_values(ascending=False)
        top_sector = sector_summary.index[0] if not sector_summary.empty else "N/A"
        
        # اختيار الأسهم القيادية
        watchlist = df_raw.sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="5d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            
            price = df_t['Close'].iloc[-1]
            change = ((price - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # --- الميزة 1: مؤشر زخم الصياد (Hunter’s Momentum) ---
            # يدمج السعر مع حجم التداول النسبي والتسارع
            vol_ratio = df_t['Volume'].iloc[-1] / df_t['Volume'].mean() # حجم التداول الحالي مقارنة بالمتوسط
            
            # حساب RSI (كأساس)
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # معادلة قوة الدخول المدمجة بالزخم
            entry_score = (100 - rsi) * (1 + (vol_ratio * 0.2)) # وزن إضافي للسيولة
            if change > 0: entry_score += 15 # وزن إضافي للتسارع السعري
            entry_score = min(max(entry_score, 5), 99.9)

            # --- الميزة 2: نظام الاحتمالات اللونية (Heat-Mapping) ---
            status = "انتظار ⏳"
            if entry_score > 85: status = "🔥 انفجار وشيك"
            elif entry_score > 70: status = "✅ اقتناص ذهبي"
            elif entry_score > 55: status = "👀 مراقبة"

            results.append({
                "الرمز": ticker,
                "السعر": f"${price:.2f}",
                "قوة الفرصة %": round(entry_score, 1),
                "التغير": f"{change:+.2f}%",
                "الحالة": status,
                "القطاع": df_raw[df_raw['Symbol']==ticker]['Sector'].values[0] if ticker in df_raw['Symbol'].values else "أخرى"
            })
        
        final_df = pd.DataFrame(results).sort_values(by="قوة الفرصة %", ascending=False)
        return final_df, top_sector
    except Exception as e:
        st.error(f"خطأ في المحرك: {e}")
        return pd.DataFrame(), "N/A"

# --- 3. عرض غرفة العمليات ---
st.title("🛰️ غرفة عمليات الفرص الذكية")

df_final, leading_sector = run_smart_engine()

if not df_final.empty:
    # عرض الميزة 3: رادار قوة القطاع
    st.markdown(f"""
    <div class="sector-box">
        <span style="font-size:1.5rem;">🚩 القطاع القائد للسوق الآن: </span>
        <span style="font-size:2rem; color:#00ffcc; font-weight:bold;">{leading_sector}</span>
    </div>
    """, unsafe_allow_html=True)

    # عرض جدول الفرص (الاحتمالات اللونية مدمجة برمجياً)
    def heat_map_style(val):
        if "🔥" in str(val): color = '#ff3300' # برتقالي محروق للانفجار
        elif "✅" in str(val): color = '#00ffcc' # أخضر فسفوري للاقتناص
        elif "👀" in str(val): color = '#ffcc00' # أصفر للمراقبة
        else: color = '#888'
        return f'color: {color}; font-weight: bold; font-size: 1.6rem;'

    st.dataframe(
        df_final.style.applymap(heat_map_style, subset=['الحالة'])
        .applymap(lambda x: 'color: #00ffcc; font-size: 1.7rem;' if float(x) > 70 else 'color: #f0f0f0;', subset=['قوة الفرصة %']),
        use_container_width=True,
        hide_index=True,
        height=900
    )
else:
    st.info("🔎 المحرك الذكي يمسح القطاعات والسيولة الآن...")
