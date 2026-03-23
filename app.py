import streamlit as st
import sqlite3
from pathlib import Path
import hashlib
import secrets

# ===== CONFIG =====
ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "alkttab.sqlite3"

# ===== DB =====
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ===== INIT DB (reuse your logic simplified) =====
def init_db():
    conn = get_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT
    )
    """)
    conn.commit()
    conn.close()

# ===== AUTH =====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(email, password):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if user and user["password_hash"] == hash_password(password):
        return dict(user)
    return None

def register(name, email, password):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (role, name, email, password_hash) VALUES (?, ?, ?, ?)",
            ("student", name, email, hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# ===== APP START =====
st.set_page_config(page_title="الكتّاب", layout="centered")
init_db()

st.title("📖 الكتّاب | اقرأ ورتّل")

# Session
if "user" not in st.session_state:
    st.session_state.user = None

# ===== AUTH UI =====
if not st.session_state.user:

    tab1, tab2 = st.tabs(["Login", "Register"])

    # LOGIN
    with tab1:
        st.subheader("تسجيل الدخول")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login(email, password)
            if user:
                st.session_state.user = user
                st.success("تم تسجيل الدخول ✅")
                st.rerun()
            else:
                st.error("بيانات غير صحيحة ❌")

    # REGISTER
    with tab2:
        st.subheader("إنشاء حساب")
        name = st.text_input("Name")
        email_r = st.text_input("Email ")
        password_r = st.text_input("Password ", type="password")

        if st.button("Register"):
            if register(name, email_r, password_r):
                st.success("تم إنشاء الحساب ✅")
            else:
                st.error("البريد مستخدم بالفعل ❌")

# ===== DASHBOARD =====
else:
    user = st.session_state.user

    st.success(f"Welcome {user['name']} 👋")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    st.divider()

    st.header("📚 المستويات")

    conn = get_connection()

    # You can reuse your LEVEL_DATA manually here if needed
    levels = [
        {"title": "المستوى الأول", "desc": "التأسيس"},
        {"title": "المستوى الثاني", "desc": "متقدم"}
    ]

    for lvl in levels:
        with st.container():
            st.subheader(lvl["title"])
            st.write(lvl["desc"])

    conn.close()
