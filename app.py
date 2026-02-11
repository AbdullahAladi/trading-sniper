import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. التصميم الملكي ---
st.set_page_config(page_title="منصة الفرص - نسخة الزخم", layout="wide")

# --- 2. إدارة التنبيهات الذكية (تحديث جوهري) ---
TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

# تخزين السعر الأخير الذي تم التنبيه عنده لكل سهم
if 'alert_prices' not in st.session_state:
    st.session_state.alert_prices = {} 

def send_telegram_msg(message):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=10)
        except: pass

# --- 3. المحرك المطور (Focus on Momentum) ---
st_autorefresh(interval=60 * 1000, key="v14_refresh")

def run_momentum_engine():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # التركيز فقط على الأسهم ذات السيولة المليونية (Active Stocks)
        watchlist = df_raw[df_raw['Volume'] > 1000000].sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        data = yf.download(symbols, period="5d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            
            price = df_t['Close'].iloc[-1]
            change_daily = ((price - df_t['Close'].iloc[0]) / df_t['Close'].iloc[0]) * 100
            
            # حساب حجم التداول اللحظي مقارنة بالمتوسط (Relative Volume)
            vol_now = df_t['Volume'].iloc[-1]
            vol_avg = df_t['Volume'].mean()
            rel_vol = vol_now / vol_avg
            
            # شرط النشاط: استبعاد أي سهم لا يمتلك حجم تداول عالٍ (RelVol > 1.2)
            if rel_vol < 1.1: continue 

            # حساب قوة الزخم (Momentum Score)
            # ندمج التغير السعري مع السيولة
            m_score = (change_daily * 2) + (rel_vol * 10)
            m_score = min(max(m_score, 0), 100)

            # --- منطق التنبيه الجديد الذكي ---
            should_alert = False
            last_alert_price = st.session_state.alert_prices.get(ticker)

            if last_alert_price is None:
                # أول تنبيه للسهم (شرط دخول قوي: صعود + سيولة)
                if m_score > 60:
                    should_alert = True
                    alert_reason = "بداية زخم نشط 🚀"
            else:
                # تنبيه لاحق فقط إذا تحرك السعر بـ 5% صعوداً أو هبوطاً
                price_diff_pct = abs((price - last_alert_price) / last_alert_price) * 100
                if price_diff_pct >= 5.0:
                    should_alert = True
                    alert_reason = "تحرك سعري كبير (>5%) ⚠️"

            if should_alert:
                msg = (f"🎯 *تنبيه نشاط: {ticker}*\n"
                       f"السبب: {alert_reason}\n"
                       f"السعر الحالي: ${price:.2f}\n"
                       f"التغير اليومي: {change_daily:+.2f}%\n"
                       f"قوة الزخم: {round(m_score, 1)}%")
                send_telegram_msg(msg)
                st.session_state.alert_prices[ticker] = price

            results.append({
                "الرمز": ticker,
                "السعر": f"${price:.2f}",
                "قوة الزخم %": round(m_score, 1),
                "التغير": f"{change_daily:+.2f}%",
                "الحالة": "نشط جداً 🔥" if m_score > 70 else "تحرك مستقر 📈",
                "السيولة": f"{rel_vol:.1f}x"
            })
        
        return pd.DataFrame(results).sort_values(by="قوة الزخم %", ascending=False)
    except: return pd.DataFrame()

# --- 4. العرض ---
st.title("🛰️ رادار الزخم والنشاط الفائق")

df_mom = run_momentum_engine()

if not df_mom.empty:
    st.dataframe(
        df_mom.style.applymap(lambda x: 'color: #00ffcc; font-weight: bold;' if '🔥' in str(x) else 'color: #ccc;', subset=['الحالة']),
        use_container_width=True, hide_index=True, height=800
    )
else:
    st.info("🔎 بانتظار رصد أسهم تدخل في موجة نشاط عالية...")
