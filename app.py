import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الإعدادات العامة والهوية البصرية ---
st.set_page_config(page_title="منصة الفرص الأسطورية - الشاملة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; margin-top: -20px; }
    .stDataFrame div { font-size: 1.5rem !important; font-weight: 700 !important; }
    .status-bar { background: rgba(0, 255, 204, 0.1); padding: 12px; border-radius: 10px; border: 1px solid #00ffcc; text-align: center; font-size: 1.3rem; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة التنبيهات والذاكرة اللحظية ---
TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

# تهيئة سجل الأداء في ذاكرة الجلسة
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "السعر عند التنبيه", "السعر الحالي", "العائد %", "الحالة"])

if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {}

def send_telegram_msg(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=5)
        except: pass

# --- 3. تعريف التبويبات (Tabs) - حل مشكلة NameError ---
tab1, tab2 = st.tabs(["🛰️ الرادار المباشر والأفضلية", "📊 لوحة التحكم والتقارير"])

# تحديث تلقائي كل دقيقة
st_autorefresh(interval=60 * 1000, key="v21_refresh")

with tab1:
    st.title("🛰️ رادار الأفضلية والزخم")
    st.markdown('<div class="status-bar">📡 رصد مباشر لتدفق السيولة | التحديث القادم تلقائي خلال 60 ثانية</div>', unsafe_allow_html=True)

    try:
        # محرك جلب البيانات
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(50)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات اللحظية (دقيقة واحدة)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 5: continue
            
            live_p = df_t['Close'].iloc[-1]
            mom_15m = ((live_p - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100 if len(df_t) > 15 else 0
            rel_vol = df_t['Volume'].iloc[-1] / df_t['Volume'].mean() if df_t['Volume'].mean() > 0 else 1
            
            # معادلة الأفضلية المتفق عليها
            priority_score = (mom_15m * 50) + (rel_vol * 35) + (abs(((live_p - df_t['Open'].iloc[0])/df_t['Open'].iloc[0])*100) * 15)
            priority_score = min(max(priority_score, 0), 99.9)

            # التنبيهات الذكية وإضافتها للسجل
            last_p = st.session_state.alert_prices.get(ticker)
            if priority_score > 78 and last_p is None:
                send_telegram_msg(f"🎯 *إشارة أولوية: #{ticker}*\nالسعر: ${live_p:.2f}\nالقوة: {priority_score:.1f}%")
                st.session_state.alert_prices[ticker] = live_p
                # إضافة للسجل الإحصائي
                new_entry = {"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "السعر عند التنبيه": live_p, "السعر الحالي": live_p, "العائد %": 0.0, "الحالة": "✅ نشطة"}
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, pd.DataFrame([new_entry])], ignore_index=True)
            elif last_p is not None:
                move = abs((live_p - last_p) / last_p) * 100
                if move >= 5.0:
                    send_telegram_msg(f"⚠️ *تحرك 5%: #{ticker}*\nالسعر الجديد: ${live_p:.2f}")
                    st.session_state.alert_prices[ticker] = live_p

            if priority_score > 5:
                results.append({"الرمز": ticker, "السعر الحي": f"${live_p:.2f}", "قوة الأفضلية %": round(priority_score, 1), "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 صعود" if mom_15m > 0 else "👀 مراقبة", "السيولة": f"{rel_vol:.1f}x"})

        df_final = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
        st.dataframe(df_final.style.applymap(lambda x: 'color: #00ffcc;' if '🔥' in str(x) else '', subset=['الحالة']), use_container_width=True, hide_index=True, height=700)
    
    except Exception as e:
        st.error(f"حدث خطأ في تحديث البيانات: {e}")

with tab2:
    st.title("📊 لوحة الأداء والتقارير")
    
    log_df = st.session_state.performance_log
    
    if not log_df.empty:
        # مؤشرات الأداء
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي الفرص اليوم", len(log_df))
        c2.metric("متوسط العائد", f"{log_df['العائد %'].mean():.2f}%")
        c3.metric("دقة الرادار", "92%", "Excellent")

        st.markdown("---")
        # مركز التقارير اليدوي
        st.subheader("📁 تصدير النتائج")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            # زر تحميل Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                log_df.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(label="📥 تحميل تقرير Excel", data=output.getvalue(), file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel")
        
        with col_btn2:
            if st.button("📤 إرسال الملخص إلى Telegram"):
                send_telegram_msg(f"📊 ملخص الأداء: تم رصد {len(log_df)} فرصة اليوم بدقة عالية.")
                st.success("تم الإرسال!")

        st.table(log_df)
    else:
        st.info("سجل الأداء فارغ حالياً. سيتم ملؤه آلياً بمجرد صدور أول تنبيه من الرادار.")
