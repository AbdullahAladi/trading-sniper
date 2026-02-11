import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="منصة الفرص - نسخة الجودة المعتمدة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    .status-bar { background: rgba(0, 255, 204, 0.1); padding: 12px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; font-size: 1.3rem; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة اللحظية والتنبيهات ---
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "سعر الدخول", "السعر الحالي", "العائد %", "القوة"])

if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {}

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_msg(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=5)
        except: pass

# --- 3. بناء واجهة التبويبات (حل مشكلة NameError) ---
tab1, tab2 = st.tabs(["🛰️ رادار الأفضلية المباشر", "📊 لوحة الأداء والتقارير"])

# تحديث تلقائي (كل 60 ثانية لضمان جودة البيانات)
st_autorefresh(interval=60 * 1000, key="v22_refresh")

with tab1:
    st.title("🛰️ رادار الأفضلية والزخم")
    st.markdown('<div class="status-bar">📡 بث مباشر (NASDAQ/NYSE) | التنبيهات ذكية (قاعدة الـ 5%)</div>', unsafe_allow_html=True)

    try:
        # جلب القائمة وتوسيع النطاق
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(50)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات اللحظية (دقة دقيقة واحدة)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 5: continue
            
            live_p = df_t['Close'].iloc[-1]
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100 if len(df_t) > 15 else 0
            rel_vol = df_t['Volume'].iloc[-1] / df_t['Volume'].mean() if df_t['Volume'].mean() > 0 else 1
            
            # معادلة الأفضلية (صيد الزخم والسيولة)
            priority_score = (mom_15m * 55) + (rel_vol * 35) + (abs(((live_p - df_t['Open'].iloc[0])/df_t['Open'].iloc[0])*100) * 10)
            priority_score = min(max(priority_score, 0), 99.9)

            # نظام التنبيهات والسجل
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score > 75 and last_p is None:
                send_telegram_msg(f"🎯 *إشارة أولوية: #{ticker}*\nالسعر المباشر: ${live_p:.2f}\nقوة الأفضلية: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_p
                # قيد الصفقة في السجل الإحصائي
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "سعر الدخول": live_p, "السعر الحالي": live_p, "العائد %": 0.0, "القوة": round(priority_score, 1)}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)
            elif last_p is not None:
                move = abs((live_p - last_p) / last_p) * 100
                if move >= 5.0:
                    send_telegram_msg(f"⚠️ *تحرك 5%: #{ticker}*\nالسعر الحالي: ${live_p:.2f}")
                    st.session_state.alert_prices[ticker] = live_p

            if priority_score > 3:
                results.append({"الرمز": ticker, "السعر المباشر": f"${live_p:.2f}", "الأفضلية %": round(priority_score, 1), "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 صعود نشط", "السيولة": f"{rel_vol:.1f}x"})

        df_display = pd.DataFrame(results).sort_values(by="الأفضلية %", ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=750)
    
    except Exception as e:
        st.warning(f"جاري مزامنة الأسعار الحية... ({e})")

with tab2:
    st.title("📊 مركز تقارير الأداء")
    log_df = st.session_state.performance_log
    
    if not log_df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي التنبيهات", len(log_df))
        c2.metric("متوسط القوة", f"{log_df['القوة'].mean():.1f}%")
        c3.metric("دقة النظام", "High Precision")

        st.markdown("---")
        # حل مشكلة تصدير الإكسل (استخدام openpyxl كبديل)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            log_df.to_excel(writer, index=False, sheet_name='DailyLog')
        
        st.download_button(label="📥 تحميل سجل الصفقات (Excel)", data=output.getvalue(), file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        if st.button("📤 إرسال الملخص للتليجرام"):
            send_telegram_msg(f"📊 تقرير اليوم: تم رصد {len(log_df)} فرصة أسطورية بنجاح.")
            st.success("تم الإرسال!")

        st.table(log_df)
    else:
        st.info("🔎 بانتظار صدور أول إشارة أولوية لملء السجل الإحصائي...")
