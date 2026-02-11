import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية ---
st.set_page_config(page_title="🛰️ فحص تشغيل رادار النخبة", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #050505; color: #f0f0f0; }
    h1 { color: #00ffcc !important; text-align: center; text-shadow: 0 0 10px #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛰️ فحص تشغيل رادار النخبة")

# --- 2. محرك قراءة الملف المرن (حل مشكلة KeyError) ---
@st.cache_data
def load_flexible_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        # البحث الذكي عن الأعمدة
        col_map = {}
        for col in df.columns:
            if 'Symbol' in col: col_map['Symbol'] = col
            if 'Price' in col or 'Last' in col: col_map['Price'] = col
            if 'Volume' in col: col_map['Volume'] = col
        
        # إعادة تسمية الأعمدة لتناسب الكود
        df = df.rename(columns={col_map.get('Symbol'): 'Symbol', 
                                col_map.get('Price'): 'Last Price', 
                                col_map.get('Volume'): 'Volume'})
        return df[['Symbol', 'Last Price', 'Volume']]
    except Exception as e:
        st.error(f"❌ خطأ في هيكلة الملف: {e}")
        return None

# --- 3. التشغيل ---
st_autorefresh(interval=30 * 1000, key="v40_fix")

try:
    df_raw = load_flexible_csv('nasdaq_screener_1770731394680.csv')
    
    if df_raw is not None:
        # فلتر مخفف جداً للتأكد من ظهور نتائج (أي سهم فوق 0.1$ وسيولة فوق 50 ألف)
        watchlist = df_raw[(df_raw['Last Price'] >= 0.1) & (df_raw['Volume'] > 50000)].head(30)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات الحية (prepost لضمان النتائج في أي وقت)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 2: continue
            
            current_p = df_t['Close'].iloc[-1]
            change = ((current_p - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            results.append({
                "الرمز": ticker,
                "السعر⚡": f"${current_p:.2f}",
                "التغير اليومي %": f"{change:+.2f}%",
                "الحالة": "✅ متصل"
            })

        if results:
            st.success(f"✅ تم الاتصال بنجاح! رصد {len(results)} سهم.")
            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        else:
            st.warning("🔎 البيانات مستلمة ولكن السوق قد يكون مغلقاً تماماً أو السيولة ضعيفة جداً.")
            
except FileNotFoundError:
    st.error("❌ لم يتم العثور على ملف الـ CSV. تأكد من وجوده بجانب الكود.")
except Exception as e:
    st.error(f"❌ حدث خطأ غير متوقع: {e}")
