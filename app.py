import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. التنسيق البصري الملكي ---
st.set_page_config(page_title="منصة النخبة - ذكاء السيولة والاستقرار", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات الذكية ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "سعر التنبيه", "بصمة السيولة", "درجة الثقة"])

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_smart(msg):
    if TOKEN and CHAT_ID:
        try: url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"; requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 3. بناء الواجهة والتحديث التلقائي ---
st_autorefresh(interval=60 * 1000, key="v33_final_refresh")
tab1, tab2 = st.tabs(["🛰️ رادار الأفضلية الذكي", "📊 سجل الجودة والتقارير"])

with tab1:
    st.title("🛰️ رادار النخبة المطور")
    st.markdown('<div class="ticker-tape">📡 تم تحسين "حساسية السيولة" لضمان منطقية النتائج | التنبيهات للانفجارات الذكية فقط</div>', unsafe_allow_html=True)

    try:
        # جلب البيانات الأساسية
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات اللحظية بدقة 1m مع prepost
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 15: continue
            
            live_p = df_t['Close'].iloc[-1]
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            rel_vol = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
            daily_change = ((live_p - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            # --- محرك ذكاء السيولة (المطور والمستقر) ---
            # حساب تدفق السيولة المتوسط لآخر 5 دقائق لمنع التناقض
            recent_mf = (df_t['Close'].diff().tail(5) * df_t['Volume'].tail(5)).mean()
            
            if recent_mf > 0:
                mf_status = "✅ تجميع"
                bonus = 15 if rel_vol > 1.2 else 5
                confidence = "High" if rel_vol > 2 else "Medium"
            else:
                # لا نعتبره تصريف إلا إذا كان التراجع حقيقياً وليس مجرد هدوء
                if abs(recent_mf) > (df_t['Volume'].mean() * 0.05):
                    mf_status = "⚠️ تصريف"
                    bonus = -15
                    confidence = "Low"
                else:
                    mf_status = "⚖️ توازن"
                    bonus = 0
                    confidence = "Medium"
            
            # معادلة الأفضلية المتوازنة
            priority_score = (mom_15m * 45) + (rel_vol * 35) + (abs(daily_change) * 10) + bonus
            priority_score = min(max(priority_score, 0), 99.9)

            # --- التنبيهات (قاعدة الـ 5% + تجميع حصراً) ---
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score >= 80 and mf_status == "✅ تجميع" and last_p is None:
                msg = (f"💎 *انفجار وتجميع: #{ticker}*\n"
                       f"💰 السعر: ${live_p:.2f} | القوة: {priority_score:.1f}%\n"
                       f"📊 بصمة السيولة: {mf_status}")
                send_telegram_smart(msg)
                st.session_state.alert_prices[ticker] = live_p
                # تسجيل السجل
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "سعر التنبيه": live_p, "بصمة السيولة": mf_status, "درجة الثقة": confidence}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            results.append({
                "الرمز": ticker, "السعر⚡": f"${live_p:.2f}",
                "قوة الأفضلية %": round(priority_score, 1),
                "بصمة السيولة": mf_status,
                "درجة الثقة": confidence,
                "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 نشط"
            })

        if results:
            df_final = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
            
            # مقياس قوة السوق البصري
            avg_mkt = df_final["قوة الأفضلية %"].head(10).mean()
            st.write(f"### 🌡️ مقياس قوة الزخم السوقي: {avg_mkt:.1f}%")
            st.progress(float(avg_mkt / 100))
            
            st.dataframe(df_final, use_container_width=True, hide_index=True, height=750)
        else:
            st.warning("🔎 بانتظار مزامنة بيانات السوق... تأكد من وقت عمل البورصة")
            
    except Exception as e:
        st.info("🔎 الرادار يبحث عن بصمات السيولة الآن... يرجى الانتظار ثوانٍ.")

with tab2:
    st.header("📊 لوحة الأداء التاريخية")
    log_df = st.session_state.performance_log
    if not log_df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            log_df.to_excel(writer, index=False)
        st.download_button("📥 تحميل التقرير الذهبي (Excel)", output.getvalue(), f"Report_{datetime.now().date()}.xlsx")
        st.table(log_df)
    else:
        st.info("🔎 السجل بانتظار صيد أول فرصة تجمع بين 'الانفجار السعري' و 'التجميع الحقيقي'.")
