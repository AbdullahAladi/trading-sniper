import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="🛰️ رادار النخبة والتحليل العميق", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a14 0%, #040408 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00ffcc, #0077ff); -webkit-background-clip: text; -webkit-fill-color: transparent; text-align: center; filter: drop-shadow(0 0 10px #00ffcc); }
    .status-bar { background: rgba(0, 255, 204, 0.05); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة الذاكرة (منع NameError) ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "السعر", "بصمة السيولة", "درجة الثقة"])

# --- 3. بناء الواجهة (Tabs) ---
tab1, tab2, tab3 = st.tabs(["🛰️ رادار النخبة الذكي", "📈 تحليل العمق", "📊 سجل النخبة"])
st_autorefresh(interval=60 * 1000, key="v29_refresh")

with tab1:
    st.title("🛰️ رادار النخبة والتحليل العميق")
    st.markdown('<div class="status-bar">📡 الفلتر يطارد "بصمة السيولة الذكية" | التحديث القادم خلال دقيقة</div>', unsafe_allow_html=True)

    try:
        # جلب البيانات
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب الأسعار اللحظية مع تفعيل prepost
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 15: continue
            
            # --- معايير العمق (VPA Analysis) ---
            live_p = df_t['Close'].iloc[-1]
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            
            # تحليل بصمة السيولة (Money Flow)
            # نقارن إجمالي التغير السعري مضروباً في الحجم لآخر 5 دقائق
            mf_raw = (df_t['Close'].diff().tail(5) * df_t['Volume'].tail(5)).sum()
            mf_status = "✅ تجميع" if mf_raw > 0 else "🛑 تصريف"
            
            # درجة الثقة
            confidence = "High" if vol_now > vol_avg * 2 and mf_raw > 0 else "Medium"
            
            # حساب الأفضلية
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100 if len(df_t) >= 15 else 0
            priority_score = (mom_15m * 45) + ((vol_now/vol_avg) * 35) + (20 if mf_raw > 0 else 0)
            priority_score = min(max(priority_score, 0), 99.9)

            results.append({
                "الرمز": ticker,
                "السعر ⚡": f"${live_p:.2f}",
                "% الأفضلية": round(priority_score, 1),
                "بصمة السيولة": mf_status,
                "درجة الثقة": confidence,
                "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 نشط"
            })

        df_final = pd.DataFrame(results).sort_values(by="% الأفضلية", ascending=False)
        
        # عرض مقياس قوة الزخم (حل مشكلة nan)
        avg_market = df_final["% الأفضلية"].head(10).mean()
        st.write(f"### 🌡️ مقياس قوة الزخم الحالي: {avg_market:.1f}%")
        st.progress(float(avg_market / 100))
        
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=650)

    except Exception as e:
        st.info(f"🔎 جاري مزامنة بصمة السيولة... يرجى الانتظار ثوانٍ.")

with tab2:
    st.markdown("### 📈 تحليل قوة الزخم (Top 10)")
    if 'df_final' in locals() and not df_final.empty:
        fig = go.Figure(go.Bar(x=df_final['الرمز'].head(10), y=df_final['% الأفضلية'].head(10), marker_color='#00ffcc'))
        fig.update_layout(template="plotly_dark", title="أقوى 10 أسهم من حيث جودة السيولة")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("📊 سجل النخبة للتقارير")
    # محرك تصدير Excel (حل ModuleNotFoundError)
    if not st.session_state.performance_log.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.performance_log.to_excel(writer, index=False)
        st.download_button("📥 تحميل التقرير الذهبي (Excel)", output.getvalue(), "Elite_Report.xlsx")
        st.table(st.session_state.performance_log)
    else:
        st.info("🔎 بانتظار أول إشارة 'انفجار' لبدء التوثيق.")
