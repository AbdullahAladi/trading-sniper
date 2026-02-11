import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. الهوية البصرية وإعدادات إدارة المخاطر ---
st.set_page_config(page_title="🛰️ رادار النخبة الاستراتيجي V41", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;700&display=swap');
    .stApp { background: radial-gradient(circle, #0a0a12 0%, #050505 100%); color: #f0f0f0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.3rem !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# قائمة جانبية لإدارة المحفظة
st.sidebar.header("💰 إدارة رأس المال")
capital = st.sidebar.number_input("إجمالي المحفظة ($)", min_value=1000, value=10000)
risk_percent = st.sidebar.slider("مخاطرة الصفقة (%)", 0.5, 3.0, 1.0)
max_loss = capital * (risk_percent / 100)

# --- 2. معالج البيانات الذكي (المعتمد في تجربة الاتصال الناجحة) ---
def load_and_clean_data(file_path):
    try:
        df = pd.read_csv(file_path)
        col_map = {}
        for col in df.columns:
            if 'Symbol' in col: col_map['Symbol'] = col
            if any(x in col for x in ['Price', 'Last', 'Close']): col_map['Price'] = col
            if 'Volume' in col: col_map['Volume'] = col
        
        df = df.rename(columns={col_map.get('Symbol'): 'Symbol', 
                                col_map.get('Price'): 'Last Price', 
                                col_map.get('Volume'): 'Volume'})
        
        # تنظيف وتحويل البيانات لضمان عدم تكرار خطأ str vs float
        df['Last Price'] = df['Last Price'].replace(r'[^\d.]', '', regex=True).astype(float)
        df['Volume'] = df['Volume'].replace(r'[^\d.]', '', regex=True).astype(float)
        return df.dropna(subset=['Symbol', 'Last Price'])
    except Exception as e:
        st.error(f"❌ خطأ في معالجة الملف: {e}")
        return None

# --- 3. التنبيهات وإدارة الذاكرة ---
if 'alert_prices' not in st.session_state: st.session_state.alert_prices = {}
if 'performance_log' not in st.session_state:
    st.session_state.performance_log = pd.DataFrame(columns=["التوقيت", "الرمز", "الكمية", "الدخول", "الهدف 🎯"])

def send_telegram_elite(ticker, entry, qty, t1, sl, score):
    TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
    CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if TOKEN and CHAT_ID:
        msg = (f"🎯 *توصية الفرص: #{ticker}*\n"
               f"━━━━━━━━━━━━━━\n"
               f"💰 دخول: ${entry:.2f}\n"
               f"📦 الكمية: {qty} سهم\n"
               f"✅ هدف: ${t1:.2f}\n"
               f"🛑 وقف: ${sl:.2f}\n"
               f"━━━━━━━━━━━━━━\n"
               f"⚡ القوة: {score:.1f}%")
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 4. محرك الرصد المتقدم ---
st_autorefresh(interval=60 * 1000, key="v41_stable")
tab1, tab2 = st.tabs(["🛰️ رادار الفرص الذكي", "📊 سجل المحفظة"])

with tab1:
    st.title("🛰️ رادار النخبة V41")
    st.info(f"🛡️ حماية المحفظة: أقصى خسارة للصفقة الواحدة هي **${max_loss:.2f}**")

    try:
        df_raw = load_and_clean_data('nasdaq_screener_1770731394680.csv')
        
        if df_raw is not None:
            # فلتر الجودة (سعر > 1$ وسيولة عالية)
            watchlist = df_raw[(df_raw['Last Price'] > 1.0) & (df_raw['Volume'] > 500000)].sort_values(by='Volume', ascending=False).head(35)
            symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
            
            # جلب البيانات الحية (تفعيل prepost)
            all_data = yf.download(symbols, period="1d", interval="1m", group_by='ticker', progress=False, prepost=True, threads=True)
            
            results = []
            for ticker in symbols:
                if ticker not in all_data or all_data[ticker].empty: continue
                df_t = all_data[ticker].dropna()
                if len(df_t) < 5: continue
                
                live_p = df_t['Close'].iloc[-1]
                
                # --- الاستراتيجية الذكية ---
                target1 = live_p * 1.02 # هدف 2%
                stop_loss = live_p * 0.98 # وقف 2%
                
                # حساب حجم الصفقة (Position Sizing)
                risk_per_share = live_p - stop_loss
                qty = int(max_loss / risk_per_share) if risk_per_share > 0 else 0
                
                # قوة الأفضلية (زخم + حجم)
                mom = ((live_p - df_t['Open'].iloc[0]) / df_t['Open'].iloc[0]) * 100
                vol_ratio = df_t['Volume'].iloc[-1] / (df_t['Volume'].mean() + 1)
                score = min((abs(mom) * 40) + (vol_ratio * 30), 99.9)

                # التنبيهات
                last_p = st.session_state.alert_prices.get(ticker)
                if score >= 85 and last_p is None and qty > 0:
                    send_telegram_elite(ticker, live_p, qty, target1, stop_loss, score)
                    st.session_state.alert_prices[ticker] = live_p
                    new_row = pd.DataFrame([{"التوقيت": datetime.now().strftime("%H:%M"), "الرمز": ticker, "الكمية": qty, "الدخول": round(live_p, 2), "الهدف 🎯": round(target1, 2)}])
                    st.session_state.performance_log = pd.concat([st.session_state.performance_log, new_row], ignore_index=True)

                results.append({
                    "الرمز": ticker,
                    "السعر⚡": f"${live_p:.2f}",
                    "قوة الأفضلية %": round(score, 1),
                    "الكمية 📦": qty,
                    "الهدف 🎯": f"${target1:.2f}",
                    "الوقف 🛑": f"${stop_loss:.2f}",
                    "الحالة": "🔥 انفجار" if score > 80 else "📈 نشط"
                })

            if results:
                st.dataframe(pd.DataFrame(results).sort_values(by="قوة الأفضلية %", ascending=False), use_container_width=True, hide_index=True, height=700)
            else:
                st.warning("🔎 البيانات مستلمة ولكن لا توجد أسهم تطابق فلاتر الجودة حالياً.")

    except Exception as e:
        st.info("🔎 الرادار يحلل تدفقات السيولة الآن... يرجى الانتظار")

with tab2:
    st.header("📊 سجل الصفقات المدارة")
    if not st.session_state.performance_log.empty:
        st.table(st.session_state.performance_log)
    else:
        st.info("🔎 بانتظار أول فرصة 'توصية فرص' لتسجيلها هنا آلياً.")
