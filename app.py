import streamlit as st
import sqlite3
from pathlib import Path
import hashlib
import secrets

# ====== CONFIG ======
DB_PATH = Path("alkttab.sqlite3")

# ====== DB ======
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ====== AUTH ======
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(email, password):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if user and user["password_hash"] == hash_password(password):
        return user
    return None

# ====== UI ======
st.set_page_config(page_title="الكتّاب", layout="centered")

st.title("📖 الكتّاب | اقرأ ورتّل")

# Session state
if "user" not in st.session_state:
    st.session_state.user = None

# ====== LOGIN ======
if not st.session_state.user:
    st.subheader("تسجيل الدخول")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(email, password)
        if user:
            st.session_state.user = dict(user)
            st.success("تم تسجيل الدخول ✅")
            st.rerun()
        else:
            st.error("بيانات غير صحيحة ❌")

# ====== DASHBOARD ======
else:
    user = st.session_state.user

    st.success(f"Welcome {user['name']} 👋")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    st.subheader("📚 المستويات")

    conn = get_connection()
    levels = conn.execute("SELECT * FROM levels").fetchall()
    conn.close()

    for lvl in levels:
        st.markdown(f"### {lvl['title']}")
        st.write(lvl['subtitle'])