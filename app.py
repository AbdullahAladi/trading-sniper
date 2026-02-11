import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. تصميم واجهة التدقيق ---
st.set_page_config(page_title="منصة التدقيق والجودة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;700&display=swap');
    .stApp { background: #050505; color: #00ffcc; font-family: 'Roboto Mono', monospace; }
    h1 { font-family: 'Orbitron', sans-serif; text-align: center; color: #00ffcc; text-shadow: 0 0 10px #00ffcc; }
    .stDataFrame div { font-size: 1.4rem !important; }
    .test-box { border: 1px solid #00ffcc; padding: 10px; border-radius: 5px; margin-bottom: 20px; background: rgba(0, 255, 204, 0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك الجودة والدقة ---
st_autorefresh(interval=30 * 1000, key="v17_1_refresh")

def run_quality_check_engine():
    try:
        # تقليل العدد لضمان استجابة السيرفر وسرعة البيانات
        symbols = ['TSLA', 'NVDA', 'AAPL', 'AMD', 'MSFT', 'AMZN', 'META', 'GOOGL', 'NFLX', 'INTC']
        
        results = []
        # جلب البيانات لكل سهم مع ميزة التداول المسبق
        for ticker in symbols:
            t_obj = yf.Ticker(ticker)
            # جلب آخر 5 دقائق فقط لضمان أقصى سرعة ودقة
            hist = t_obj.history(period="1d", interval="1m", prepost=True)
            
            if hist.empty: continue
            
            live_p = hist['Close'].iloc[-1]
            last_update = hist.index[-1].strftime('%H:%M:%S') # توقيت آخر صفقة
            vol_last_5m = hist['Volume'].tail(5).sum() # حجم التداول في آخر 5 دقائق
            
            # حساب الفجوة السعرية (Gap) للتأكد من التقاط سعر ما قبل الافتتاح
            # السعر الحالي مقابل سعر إغلاق الأمس
            prev_close = t_obj.fast_info.get('previousClose', live_p)
            gap_pct = ((live_p - prev_close) / prev_close) * 100

            results.append({
                "الرمز": ticker,
                "السعر المباشر": f"${live_p:.2f}",
                "توقيت التحديث": last_update,
                "فجوة السعر %": f"{gap_pct:+.2f}%",
                "سيولة (5د)": int(vol_last_5m),
                "الجودة": "✅ دقيق (حية)" if vol_last_5m > 0 else "⚠️ خامل"
            })
            
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"خطأ في التدقيق: {e}")
        return pd.DataFrame()

# --- 3. عرض لوحة الجودة ---
st.title("🏹 منصة التدقيق والجودة الفائقة")

st.markdown("""
<div class="test-box">
    <strong>🎯 اختبار الدقة:</strong> إذا كان "توقيت التحديث" يطابق الوقت الحالي و "السيولة (5د)" تتغير، فالمنصة تعمل بكفاءة 100%.
</div>
""", unsafe_allow_html=True)

df_check = run_quality_check_engine()

if not df_check.empty:
    st.dataframe(df_check, use_container_width=True, hide_index=True)
    
    # رسم بياني صغير للتأكد من الحركة (اختبار البصر)
    st.markdown("### 📈 اختبار حركة الزخم (لأول سهم في القائمة)")
    top_ticker = df_check['الرمز'].iloc[0]
    test_hist = yf.download(top_ticker, period="1d", interval="1m", prepost=True, progress=False)
    st.line_chart(test_hist['Close'])
else:
    st.warning("⚠️ بانتظار استجابة سيرفرات البيانات... تأكد من أن السوق في فترة تداول (رسمي أو مسبق).")
