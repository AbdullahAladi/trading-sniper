import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import re
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية ---
st.set_page_config(page_title="🛰️ رادار النخبة - نسخة التشغيل", layout="wide")
st.markdown("<style>.stApp { background: #050505; color: #00ffcc; }</style>", unsafe_allow_html=True)

st.title("🛰️ رادار النخبة - فحص الاتصال")

# --- 2. معالج البيانات الذكي (حل مشكلة str vs float) ---
def clean_and_load_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        col_map = {}
        # البحث عن الأعمدة الأساسية
        for col in df.columns:
            if 'Symbol' in col: col_map['Symbol'] = col
            if any(x in col for x in ['Price', 'Last', 'Close']): col_map['Price'] = col
            if 'Volume' in col: col_map['Volume'] = col
        
        df = df.rename(columns={col_map.get('Symbol'): 'Symbol', 
                                col_map.get('Price'): 'Last Price', 
                                col_map.get('Volume'): 'Volume'})
        
        # تنظيف عمود السعر من أي رموز (مثل $) وتحويله لرقم
        df['Last Price'] = df['Last Price'].replace(r'[^\d.]', '', regex=True).astype(float)
        # تنظيف عمود الحجم
        df['Volume'] = df['Volume'].replace(r'[^\d.]', '', regex=True).astype(float)
        
        return df[['Symbol', 'Last Price', 'Volume']]
    except Exception as e:
        st.error(f"❌ خطأ في معالجة البيانات: {e}")
        return None

# --- 3. محرك الرصد ---
st_autorefresh(interval=30 * 1000, key="v40_2_stable")

try:
    df_raw = clean_and_load_csv('nasdaq_screener_1770731394680.csv')
    
    if df_raw is not None:
        # فلتر مرن جداً للاختبار
        watchlist = df_raw[(df_raw['Last Price'] >= 0.1) & (df_raw['Volume'] > 10000)].head(25)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات الحية شاملة ما قبل/بعد السوق
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 1: continue
            
            current_p = df_t['Close'].iloc[-1]
            # حساب التغير بناءً على الإغلاق السابق أو الافتتاح المتاح
            ref_p = df_t['Open'].iloc[0]
            change = ((current_p - ref_p) / ref_p) * 100
            
            results.append({
                "الرمز": ticker,
                "السعر⚡": f"${current_p:.2f}",
                "التغير اللحظي %": f"{change:+.2f}%",
                "الحالة": "✅ متصل"
            })

        if results:
            st.success(f"🚀 تم بنجاح! الرادار يراقب {len(results)} سهم الآن.")
            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        else:
            st.warning("🔎 تم الاتصال بالملف، لكن Yahoo Finance لم يرسل بيانات حية بعد. تأكد من استقرار الإنترنت.")
            
except Exception as e:
    st.error(f"❌ عائق تقني: {e}")
