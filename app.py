import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. التصميم السيبراني الموحد ---
st.set_page_config(page_title="منصة الفرص - محلل الأخبار", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@400;700&display=swap');
    .stApp { background-color: #050505; color: #f0f0f0; font-family: 'Inter', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; font-size: 3.5rem !important; color: #00ffcc !important; text-align: center; text-shadow: 0 0 15px #00ffcc; }
    .stDataFrame div { font-size: 1.6rem !important; }
    .news-card { padding: 15px; border-radius: 10px; background: #1a1a1a; border-right: 5px solid #00ffcc; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك تحليل الأخبار والأرقام ---
st_autorefresh(interval=60 * 1000, key="v11_refresh")

def analyze_news_impact(ticker_obj):
    """تحليل عناوين الأخبار لتقدير الانطباع العام"""
    try:
        news = ticker_obj.news[:3] # جلب آخر 3 أخبار
        positive_keys = ['growth', 'profit', 'upgrade', 'buy', 'surge', 'beats', 'dividend', 'partnership']
        negative_keys = ['loss', 'fall', 'drop', 'downgrade', 'sell', 'debt', 'miss', 'lawsuit']
        
        score = 0
        titles = ""
        for n in news:
            title = n['title'].lower()
            titles += n['title'] + " | "
            if any(k in title for k in positive_keys): score += 1
            if any(k in title for k in negative_keys): score -= 1
        
        if score > 0: return "إيجابي شديد ✨", titles
        elif score < 0: return "سلبي محذر ⚠️", titles
        else: return "محايد/هادئ 🛡️", titles
    except:
        return "لا يوجد أخبار حالية", ""

def run_global_analyzer():
    try:
        df_raw = pd.read_csv('nasdaq_screener_1770731394680.csv')
        watchlist = df_raw.sort_values(by='Volume', ascending=False).head(40)
        symbols = [str(s).replace('.', '-').strip() for s in watchlist['Symbol']]
        
        # جلب البيانات المالية
        data = yf.download(symbols, period="5d", interval="60m", group_by='ticker', progress=False)
        
        results = []
        for ticker in symbols:
            if ticker not in data or data[ticker].empty: continue
            ticker_obj = yf.Ticker(ticker)
            df_t = data[ticker].dropna()
            
            price = df_t['Close'].iloc[-1]
            change = ((price - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
            
            # حساب قوة الفرصة (بناءً على السعر والزخم السلوكي)
            vol_ratio = df_t['Volume'].iloc[-1] / df_t['Volume'].mean()
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss.replace(0, 0.001)))).iloc[-1]
            
            # تحليل الأخبار
            news_sentiment, news_titles = analyze_news_impact(ticker_obj)
            
            # دمج الخبر في النتيجة النهائية
            score = (100 - rsi) + (20 if "إيجابي" in news_sentiment else 0)
            score = min(max(score, 10), 99)

            results.append({
                "الرمز": ticker,
                "السعر": f"${price:.2f}",
                "قوة الفرصة %": round(score, 1),
                "تأثير الأخبار": news_sentiment,
                "التغير": f"{change:+.2f}%",
                "سلوك السوق": "تجميع ذكي 💎" if score > 80 else "مراقبة 👀"
            })
        
        return pd.DataFrame(results).sort_values(by="قوة الفرصة %", ascending=False)
    except:
        return pd.DataFrame()

# --- 3. واجهة غرفة العمليات النهائية ---
st.title("🛰️ منصة الفرص | محلل الأخبار والسلوك")

df_news = run_global_analyzer()

if not df_news.empty:
    st.markdown("### 🔝 الفرص المرتبطة بقوة الخبر والسيولة")
    
    # تنسيق لوني للأخبار والسلوك
    def style_news(val):
        if "إيجابي" in str(val): color = '#00ffcc'
        elif "سلبي" in str(val): color = '#ff3300'
        else: color = '#888'
        return f'color: {color}; font-weight: bold; font-size: 1.5rem;'

    st.dataframe(
        df_news.style.applymap(style_news, subset=['تأثير الأخبار'])
        .applymap(lambda x: 'color: #00ffcc; font-weight: bold;' if float(x) > 75 else 'color: #f0f0f0;', subset=['قوة الفرصة %']),
        use_container_width=True,
        hide_index=True,
        height=850
    )
else:
    st.info("🔎 جاري مسح وكالات الأنباء وحركة الأسهم... يرجى الانتظار")
