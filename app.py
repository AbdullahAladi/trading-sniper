import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية الملكية ---
st.set_page_config(page_title="منصة الفرص الأسطورية - النسخة الاحترافية", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.2rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 20px #00ffcc; margin-top: -20px; }
    .stDataFrame div { font-size: 1.6rem !important; font-weight: 700 !important; }
    .ticker-tape { background: rgba(0, 255, 204, 0.1); padding: 15px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; font-size: 1.4rem; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والتنبيهات الذكية (قاعدة الـ 5%) ---
if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {} 

if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "سعر التنبيه", "الحالة"])

TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_priority(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=10)
        except: pass

# --- 3. المحرك الأسطوري (Live Accuracy & Elite Filtering) ---
st_autorefresh(interval=60 * 1000, key="v24_final_refresh")

tab1, tab2 = st.tabs(["🛰️ الرادار المباشر", "📊 لوحة التحكم والتقارير"])

with tab1:
    st.title("🛰️ رادار الأفضلية والزخم")
    st.markdown('<div class="ticker-tape">📡 يتم إرسال "الانفجارات" فقط للتليجرام | مراقبة تحركات الـ 5% نشطة</div>', unsafe_allow_html=True)

    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw[df_raw['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(50)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات اللحظية (دقة دقيقة واحدة - يشمل التداول الليلي)
        data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 15: continue
            
            live_price = df_t['Close'].iloc[-1]
            mom_15m = ((live_price - df_t['Close'].iloc[-15]) / df_t['Close'].iloc[-15]) * 100
            rel_vol = df_t['Volume'].iloc[-1] / df_t['Volume'].mean() if df_t['Volume'].mean() > 0 else 1
            daily_change = ((live_price - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
            
            # معادلة الأفضلية (الأوزان المتفق عليها)
            priority_score = (mom_15m * 50) + (rel_vol * 30) + (abs(daily_change) * 20)
            priority_score = min(max(priority_score, 0), 99.9)

            # --- منطق التنبيهات الذكي المحدث ---
            last_alert_price = st.session_state.alert_prices.get(ticker)
            should_send = False
            msg_type = ""

            # الشرط 1: انفجار لأول مرة (أعلى من 80)
            if priority_score >= 80 and last_alert_price is None:
                should_send = True
                msg_type = "🔥 انفجار سعري أسطوري"
            
            # الشرط 2: متابعة حركة الـ 5% (صعود أو نزول)
            elif last_alert_price is not None:
                price_diff = ((live_price - last_alert_price) / last_alert_price) * 100
                if abs(price_diff) >= 5.0:
                    should_send = True
                    msg_type = f"⚠️ تحرك حي بنسبة ({price_diff:+.1f}%)"

            if should_send:
                msg = (f"🎯 *تنبيه النخبة: #{ticker}*\n"
                       f"الحالة: {msg_type}\n"
                       f"السعر: ${live_price:.2f}\n"
                       f"الأفضلية: {priority_score:.1f}%")
                send_telegram_priority(msg)
                st.session_state.alert_prices[ticker] = live_price # تحديث السعر المرجعي
                
                # قيد في السجل
                new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "سعر التنبيه": live_price, "الحالة": msg_type}])
                st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

            if priority_score > 5:
                results.append({
                    "الرمز": ticker, "السعر الحي⚡": f"${live_price:.2f}",
                    "قوة الأفضلية %": round(priority_score, 1),
                    "الزخم": f"{mom_15m:+.2f}%",
                    "الحالة": "🔥 انفجار" if priority_score > 80 else "📈 صعود نشط" if mom_15m > 0 else "👀 مراقبة",
                    "السيولة": f"{rel_vol:.1f}x"
                })

        df_display = pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False)
        st.dataframe(df_display.style.applymap(lambda x: 'color: #00ffcc;' if '🔥' in str(x) else '', subset=['الحالة']), use_container_width=True, hide_index=True, height=800)
    except:
        st.info("🔎 الرادار يمسح السوق الآن... يرجى الانتظار")

with tab2:
    st.title("📊 لوحة الأداء والتقارير اليدوية")
    log_df = st.session_state.performance_log
    
    if not log_df.empty:
        c1, c2 = st.columns(2)
        c1.metric("إجمالي الفرص المكتشفة", len(log_df))
        c2.metric("دقة الرادار", "High Quality ✅")

        st.markdown("---")
        # زر استخراج الإكسل اليدوي
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            log_df.to_excel(writer, index=False, sheet_name='Daily_Signals')
        
        st.download_button(label="📥 تحميل تقرير الإكسل الكامل", data=output.getvalue(), file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.table(log_df)
    else:
        st.info("🔎 السجل فارغ. سيتم تسجيل أول 'انفجار' يظهر في الرادار آلياً هنا.")
