import streamlit as st
import yfinance as yf
import json
import os

st.set_page_config(page_title="Hameeda Absolute Safety", layout="wide")
st.title("🛡️ منصة حميدة - نسخة الأمان المطلق v4.2")

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

# جلب بيانات السوق
option = st.selectbox('العملة المراقبة:', ('BTC-USD', 'ETH-USD'))
data = yf.download(option, period='1d', interval='1m')

if not data.empty:
    current_price = float(data['Close'].iloc[-1])
    ma_value = float(data['Close'].rolling(window=15).mean().iloc[-1])

    # --- قسم الأمان والتحكم (دائم الظهور) ---
    st.sidebar.header("🚨 مركز التحكم في الطوارئ")
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

    # --- منطق التداول ---
    if not holding:
        if current_price > ma_value:
            st.session_state.db["holding"] = True
            st.session_state.db["buy_price"] = current_price
            st.session_state.db["trades"].append(f"✅ شراء حكيم بسعر ${current_price:,.2f}")
            save_data(st.session_state.db)
            st.rerun()
    else:
        # جني أرباح 1% أو وقف خسارة 2%
        if current_price >= buy_price * 1.01 or current_price <= buy_price * 0.98:
            is_profit = current_price >= buy_price * 1.01
            change = (buy_price * 0.01) if is_profit else -(buy_price * 0.02)
            msg = "💰 ربح (%1)" if is_profit else "🛡️ حماية (%-2)"
            st.session_state.db["holding"] = False
            st.session_state.db["balance"] += change
            st.session_state.db["trades"].append(f"{msg} بسعر ${current_price:,.2f}")
            save_data(st.session_state.db)
            if is_profit:
                st.balloons()
            st.rerun()

    st.line_chart(data['Close'])
    st.write("### 📋 سجل العمليات (محفوظ)")
    for t in reversed(trades[-10:]):
        st.info(t)
                  
  
