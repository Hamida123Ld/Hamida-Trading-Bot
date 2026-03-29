import streamlit as st
import yfinance as yf
import json
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Hameeda Absolute Safety", layout="wide")
st.title("🛡️ منصة حميدة - نسخة الأمان المطلق v5.0")

# --- الذاكرة ---
DB_FILE = "trading_data.json"

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"balance": 10000.0, "trades": [], "holding": False, "buy_price": 0.0}

if 'db' not in st.session_state:
    st.session_state.db = load_data()

# استخراج البيانات
db = st.session_state.db
balance = db["balance"]
holding = db["holding"]
trades = db["trades"]
buy_price = db["buy_price"]

# --- حساب المؤشرات ---
def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices):
    ema12 = float(np.mean(prices[-12:]))
    ema26 = float(np.mean(prices[-26:]))
    return ema12 - ema26

def train_ai(prices):
    if len(prices) < 50:
        return None
    X, y = [], []
    for i in range(30, len(prices) - 1):
        rsi = calculate_rsi(prices[i-14:i])
        macd = calculate_macd(prices[i-26:i])
        ma = np.mean(prices[i-15:i])
        X.append([rsi, macd, prices[i] - ma])
        y.append(1 if prices[i+1] > prices[i] else 0)
    if len(X) < 10:
        return None
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    return model

# جلب بيانات السوق
option = st.selectbox('العملة المراقبة:', ('BTC-USD', 'ETH-USD'))
data = yf.download(option, period='1d', interval='1m')

if not data.empty:
    prices = data['Close'].values.flatten()
    current_price = float(prices[-1])
    ma_value = float(np.mean(prices[-15:]))
    rsi = calculate_rsi(prices)
    macd = calculate_macd(prices)

    # تدريب الذكاء الاصطناعي
    model = train_ai(prices)
    ai_signal = 0
    if model:
        features = [[rsi, macd, current_price - ma_value]]
        ai_signal = model.predict(features)[0]

    # --- قسم الأمان والتحكم ---
    st.sidebar.header("🚨 مركز التحكم في الطوارئ")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 المؤشرات")
    st.sidebar.metric("RSI", f"{rsi:.1f}")
    st.sidebar.metric("MACD", f"{macd:.2f}")
    st.sidebar.metric("AI", "🟢 شراء" if ai_signal == 1 else "🔴 انتظار")

    if st.sidebar.button("🔴 إغلاق كافة الصفقات فوراً"):
        if holding:
            p_amt = current_price - buy_price
            st.session_state.db["balance"] += p_amt
            st.session_state.db["trades"].append(f"🔴 طوارئ: بيع يدوي بسعر ${current_price:,.2f}")
            st.session_state.db["holding"] = False
            save_data(st.session_state.db)
            st.warning("تم تفعيل وضع الطوارئ وإيقاف كافة العمليات.")
            st.rerun()

    # لوحة المؤشرات
    c1, c2, c3 = st.columns(3)
    c1.metric("السعر الحالي", f"${current_price:,.2f}")

    if holding:
        p_amt = current_price - buy_price
        p_pct = (p_amt / buy_price) * 100
        status_color = "normal" if p_pct > 0 else "inverse"
        c2.metric("أداء الصفقة", f"{p_pct:.3f}%", f"{p_amt:.2f}", delta_color=status_color)
    else:
        c2.info("البوت يراقب السوق...")

    c3.metric("إجمالي المحفظة", f"${balance:,.2f}")

    # --- منطق التداول الذكي ---
    buy_condition = rsi < 45 and macd > 0 and ai_signal == 1
    sell_condition = (current_price >= buy_price * 1.01 or
                     current_price <= buy_price * 0.98 or
                     rsi > 65)

    if not holding:
        if buy_condition:
            st.session_state.db["holding"] = True
            st.session_state.db["buy_price"] = current_price
            st.session_state.db["trades"].append(f"✅ شراء ذكي بسعر ${current_price:,.2f} | RSI:{rsi:.1f} | AI:🟢")
            save_data(st.session_state.db)
            st.rerun()
    else:
        if sell_condition:
            is_profit = current_price >= buy_price * 1.01
            change = (buy_price * 0.01) if is_profit else -(buy_price * 0.02)
            msg = "💰 ربح (%1)" if is_profit else "🛡️ حماية (%-2)"
            st.session_state.db["holding"] = False
            st.session_state.db["balance"] += change
            st.session_state.db["trades"].append(f"{msg} بسعر ${current_price:,.2f} | RSI:{rsi:.1f}")
            save_data(st.session_state.db)
            if is_profit:
                st.balloons()
            st.rerun()

    st.line_chart(data['Close'])
    st.write("### 📋 سجل العمليات (محفوظ)")
    for t in reversed(trades[-10:]):
        st.info(t)

                  
  
