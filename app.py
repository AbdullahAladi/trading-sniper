import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. تصميم الواجهة الفريد (Cyber-Trading Style) ---
st.set_page_config(page_title="غرفة عمليات الفرص", layout="wide", page_icon="🎛️")

st.markdown("""
    <style>
    body { color: #e0e0e0; }
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(0, 255, 255, 0.2);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .status-buy { color: #00ffcc; font-weight: bold; text-shadow: 0 0 10px #00ffcc; }
    .status-sell { color: #ff4b4b; font-weight: bold; text-shadow: 0 0 10px #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الإعدادات والربط ---
TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")
st_autorefresh(interval=45 * 1000, key="pro_refresh") # تحديث أسرع كل 45 ثانية

if 'alerts_history' not in st.session_state: st.session_state.alerts_history = []

# --- 3. محرك الإبداع: تحليل الزخم الذكي ---
def advanced_analysis():
    try:
        df = pd.read_csv('nasdaq_screener_1770731394680.csv')
        # تصفية النخبة (أعلى سيولة فقط)
        top_stocks = df[df['Volume'] > 500000].sort_values(by='Volume', ascending=False).head(35)
        symbols = [str(s).replace('.', '-').strip() for s in top_stocks['Symbol']]
        
        data = yf.download(symbols, period="5d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            df_t = data[ticker].dropna()
            if len(df_t) < 10: continue
            
            # حساب الزخم المبتكر (Price + Volatility + Volume)
            close = df_t['Close'].iloc[-1]
            change = ((close - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # حساب RSI
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # ميزة فريدة: "درجة الانفجار" (Explosion Score)
            vol_ratio = df_t['Volume'].iloc[-1] / df_t['Volume'].mean()
            score = (100 - rsi) * (vol_ratio) if change > 0 else 0
            
            action = "انتظار ⏳"
            color = "#ffffff"
            if rsi < 40 and change > 0.2:
                action = "اقتناص 🎯"
                color = "#00ffcc"
                if ticker not in st.session_state.alerts_history:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                 data={"chat_id": CHAT_ID, "text": f"🚀 إشارة ذهبية: {ticker}\nالسعر: {close:.2f}\nالزخم: {score:.1f}", "parse_mode": "Markdown"})
                    st.session_state.alerts_history.append(ticker)

            results.append({
                "الرمز": ticker, "السعر": round(close, 2), "التغير": f"{change:.2f}%",
                "RSI": round(rsi, 1), "قوة الزخم": round(score, 1), "الحالة": action
            })
        return pd.DataFrame(results)
    except: return pd.DataFrame()

# --- 4. تصميم واجهة "غرفة العمليات" ---
st.title("🛰️ غرفة عمليات الفرص الذكية")
st.write(f"آخر تحديث للرادار: {datetime.now().strftime('%H:%M:%S')}")

df_res = advanced_analysis()

# عرض البطاقات العلوية بتصميم عصري
cols = st.columns(4)
if not df_res.empty:
    with cols[0]: st.markdown(f'<div class="metric-card">🟢 فرص الاقتناص<br><h2>{len(df_res[df_res["الحالة"]=="اقتناص 🎯"])}</h2></div>', unsafe_allow_html=True)
    with cols[1]: st.markdown(f'<div class="metric-card">🔥 أعلى زخم<br><h2>{df_res["الرمز"].iloc[df_res["قوة الزخم"].argmax()]}</h2></div>', unsafe_allow_html=True)
    with cols[2]: st.markdown(f'<div class="metric-card">📊 حجم التداول<br><h2>نشط جداً</h2></div>', unsafe_allow_html=True)
    with cols[3]: st.markdown(f'<div class="metric-card">⏱️ التحديث<br><h2>آلي</h2></div>', unsafe_allow_html=True)

st.markdown("---")

# عرض البيانات بشكل إبداعي
c_left, c_right = st.columns([1.2, 2])

with c_left:
    st.subheader("📡 الرادار النشط")
    # عرض الجدول بتنسيق لوني
    for _, row in df_res.iterrows():
        st.markdown(f"""
        <div style="padding:10px; border-bottom:1px solid #333; display:flex; justify-content:space-between;">
            <span><b>{row['الرمز']}</b></span>
            <span style="color:{'#00ffcc' if '🎯' in row['الحالة'] else '#fff'}">{row['الحالة']}</span>
            <span style="color:#00ffcc">{row['التغير']}</span>
        </div>
        """, unsafe_allow_html=True)

with c_right:
    if not df_res.empty:
        selected = st.selectbox("تحليل متقدم للسهم:", df_res['الرمز'].tolist())
        st.subheader(f"📊 نبض السهم: {selected}")
        
        hist = yf.download(selected, period="5d", interval="15m", progress=False)
        if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
        
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
