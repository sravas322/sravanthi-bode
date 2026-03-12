import streamlit as st
import ollama
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
import uuid
import json

# -----------------------------
# Load Banking Library
# -----------------------------
def load_library():
    try:
        with open("banking_library.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        return {}

banking_data = load_library()

# -----------------------------
# Get Answer from Library
# -----------------------------
def get_library_answer(user_input):
    user_input = user_input.lower().strip()
    for question, answer in banking_data.items():
        if question in user_input:
            return answer
    return None

# -----------------------------
# Banking Restriction Function
# -----------------------------
def is_banking_question(user_input):
    banking_keywords = [
        "bank","account","loan","balance","credit","debit",
        "transfer","ifsc","interest","deposit","withdraw",
        "savings","current","atm","upi","transaction"
    ]
    user_input = user_input.lower()
    for keyword in banking_keywords:
        if keyword in user_input:
            return True
    return False

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="AI Banking Assistant Pro",
    page_icon="🏦",
    layout="wide"
)

# -----------------------------
# DATABASE FUNCTIONS
# -----------------------------
def get_connection():
    return sqlite3.connect("bank_users.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            username TEXT,
            title TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# PASSWORD FUNCTIONS
# -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username, password):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?)",
                  (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# -----------------------------
# LOGIN PAGE
# -----------------------------
if not st.session_state.logged_in:

    st.title("🏦 AI Banking Assistant Pro")

    option = st.radio("Choose Option", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Signup":
        if st.button("SIGNUP"):
            if signup(username, password):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists.")

    if option == "Login":
        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

# -----------------------------
# MAIN APP
# -----------------------------
else:

    st.sidebar.title("🏦 BankBot")
    st.sidebar.markdown(
    f"""
    👋 **Welcome, {st.session_state.username}!**  
    _Have a great banking day 💼_
    """
)
    st.sidebar.divider()

    # Load Chat Sessions
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT session_id, title
        FROM chat_sessions
        WHERE username=?
        ORDER BY created_at DESC
    """, (st.session_state.username,))
    sessions = c.fetchall()
    conn.close()

    st.sidebar.subheader("🕘 Chats")

    for session_id, title in sessions:
        col1, col2, col3 = st.sidebar.columns([3, 1, 1])

        if col1.button(title, key="open_" + session_id):
            st.session_state.current_chat = session_id
            st.session_state.page = "Chat"
            st.rerun()

        if col2.button("✏️", key="rename_" + session_id):
            st.session_state.rename_chat = session_id

        if col3.button("🗑️", key="delete_" + session_id):
            conn = get_connection()
            c = conn.cursor()
            c.execute("DELETE FROM chat_sessions WHERE session_id=?", (session_id,))
            c.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
            conn.commit()
            conn.close()
            st.rerun()

    if "rename_chat" in st.session_state:
        new_title = st.sidebar.text_input("New Chat Name")
        if st.sidebar.button("Save Name"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE chat_sessions SET title=? WHERE session_id=?",
                      (new_title, st.session_state.rename_chat))
            conn.commit()
            conn.close()
            del st.session_state.rename_chat
            st.rerun()

    st.sidebar.divider()

    if st.sidebar.button("➕ New Chat"):
        new_id = str(uuid.uuid4())
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO chat_sessions VALUES (?, ?, ?, ?)",
                  (new_id, st.session_state.username, "New Chat", str(datetime.now())))
        conn.commit()
        conn.close()
        st.session_state.current_chat = new_id
        st.session_state.page = "Chat"
        st.rerun()

    if st.sidebar.button("📊 Dashboard"):
        st.session_state.page = "Dashboard"

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.current_chat = None
        st.rerun()

    # -----------------------------
    # DASHBOARD
    # -----------------------------
    if st.session_state.page == "Dashboard":

        st.title("📊 Bank Dashboard")

        col1, col2, col3 = st.columns(3)
        col1.metric("Account Balance", "₹1,25,000")
        col2.metric("Active Loans", "2")
        col3.metric("Credit Score", "785")

        balance_data = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Balance": [100000, 110000, 105000, 120000, 125000, 130000]
        })

        st.subheader("📈 Balance Trend")
        st.line_chart(balance_data.set_index("Month"))

        st.divider()
        expense_data = pd.DataFrame({
            "Category": ["Food", "Rent", "Transport", "Shopping", "Utilities"],
            "Amount": [8000, 25000, 4000, 6000, 3000]
})
        st.subheader("💸 Monthly Expenses")
        st.bar_chart(expense_data.set_index("Category"))
        if st.sidebar.button("👤 Profile"):
            st.session_state.page = "Profile"

    # -----------------------------
    # CHAT PAGE
    # -----------------------------
    elif st.session_state.page == "Profile":
        st.title("👤 User Profile")

        st.subheader("Basic Information")
        st.write(f"**Username:** {st.session_state.username}")
        st.write("**Account Type:** Savings")
        st.write("**Branch:** Nellore Main Branch")
        st.write("**IFSC:** BANK0001234")

        st.divider()

        st.subheader("Account Status")
        st.success("✅ Active Account")
    elif st.session_state.page == "Chat":
        st.title("🤖 BankBot Assistant")

        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT role, content FROM messages
            WHERE session_id=?
            ORDER BY id ASC
        """, (st.session_state.current_chat,))
        messages = c.fetchall()
        conn.close()

        for role, content in messages:
            with st.chat_message(role):
                st.markdown(content)

        user_input = st.chat_input("Ask Banking Assistant...")

        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)

            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO messages (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (st.session_state.current_chat, "user", user_input, str(datetime.now())))
            conn.commit()
            conn.close()

            # 🔒 Banking Restriction + JSON + Ollama
            if not is_banking_question(user_input):
                bot_reply = "❌ I am a Banking Assistant. Please ask banking-related questions only."

            else:
                library_answer = get_library_answer(user_input)
                if library_answer:
                    bot_reply = library_answer
                else:
                    response = ollama.chat(
                        model="phi3:mini",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a strict banking assistant. Answer only banking-related questions."
                            },
                            {
                                "role": "user",
                                "content": user_input
                            }
                        ]
                    )
                    bot_reply = response["message"]["content"]

            with st.chat_message("assistant"):
                st.markdown(bot_reply)

            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO messages (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (st.session_state.current_chat, "assistant", bot_reply, str(datetime.now())))
            conn.commit()
            conn.close()

            st.rerun()
