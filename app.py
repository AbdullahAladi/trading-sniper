import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية وتكبير الخطوط (CSS Pro) ---
st.set_page_config(page_title="منصة الفرص الذكية", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    /* تكبير الخط العام وتغيير الخلفية */
    .stApp { 
        background-color: #0e1117; 
        font-family: 'Inter', sans-serif; 
        color: #f0f0f0; 
    }

    /* تكبير عناوين الصفحة */
    h1 { font-size: 3rem !important; color: #00ffcc !important; text-align: center; margin-bottom: 30px; }
    h3 { font-size: 1.8rem !important; color: #00ffcc !important; }

    /* تكبير نصوص الجدول (Dataframe) */
    [data-testid="stTable"] { font-size: 1.5rem !important; }
    .stDataFrame div { font-size: 1.3rem !important; }
    
    /* تحسين مظهر الخلايا */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 1.4rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك الحسابات والترتيب بالأفضلية ---
st_autorefresh(interval=60 * 1000, key="v8_refresh")

def get_ranked_data():
    try:
        df = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # تصفية أفضل 40 سهم من حيث السيولة
        watchlist = df.sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="7d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            
            price = df_t['Close'].iloc[-1]
            change = ((price - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # حساب RSI لتحويله لنسبة دخول
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # معادلة قوة الدخول %
            entry_score = 100 - rsi
            if change > 0: entry_score += 10
            entry_score = min(max(entry_score, 5), 98)
            
            # حساب نسبة المخاطرة
            volatility = (df_t['High'] - df_t['Low']).mean()
            risk_pct = (volatility / price) * 100
            
            status = "انتظار"
            if entry_score > 75: status = "🎯 اقتناص الآن"
            elif entry_score > 60: status = "👀 مراقبة"

            results.append({
                "الرمز": ticker,
                "السعر": f"${price:.2f}",
                "قوة الدخول %": round(entry_score, 1),
                "المخاطرة %": round(risk_pct, 1),
                "التغير": f"{change:+.2f}%",
                "الحالة": status
            })
        
        final_df = pd.DataFrame(results)
        # الترتيب بالأفضلية (الأعلى قوة دخول في القمة)
        if not final_df.empty:
            final_df = final_df.sort_values(by="قوة الدخول %", ascending=False).reset_index(drop=True)
        return final_df
    except: return pd.DataFrame()

# --- 3. عرض الواجهة (الجدول العملاق) ---
st.title("🏹 منصة الفرص الذكية")
st.write(f"📡 تحديث تلقائي للرادار كل دقيقة | الوقت الحالي: {datetime.now().strftime('%H:%M:%S')}")

df_final = get_ranked_data()

if not df_final.empty:
    st.markdown("### 🔝 قائمة الفرص المُرتبة بالأفضلية")
    
    # تنسيق الألوان للنسب الكبيرة
    def apply_style(val):
        color = '#00ffcc' if val > 75 else '#ffcc00' if val > 50 else '#ff4b4b'
        return f'color: {color}; font-weight: bold; font-size: 1.4rem;'

    # عرض الجدول بكامل عرض الصفحة مع تكبير الخطوط
    st.dataframe(
        df_final.style.applymap(apply_style, subset=['قوة الدخول %'])
        .applymap(lambda x: 'color: #ff4b4b' if float(x) > 4 else 'color: #00ffcc', subset=['المخاطرة %']),
        use_container_width=True, 
        hide_index=True,
        height=800 # زيادة طول الجدول للعرض الواضح
    )
else:
    st.info("🔎 جاري تحليل بيانات السوق واقتناص أفضل الفرص...")

st.sidebar.markdown("---")
st.sidebar.write("💡 **نصيحة:** الأسهم في أعلى الجدول تمتلك أعلى احتمالية للارتداد السعري بناءً على زخم السوق الحالي.")
