import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import time
from datetime import datetime

# ==========================================
# 1. DATABASE SETUP (Replaces MongoDB)
# ==========================================
def init_db():
    conn = sqlite3.connect('studyflow.db')
    c = conn.cursor()
    # Create Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Create Study Sessions Table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, duration REAL, subject TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 2. APP CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(page_title="StudyFlow", page_icon="📚", layout="centered")
init_db()

# Initialize variables in Streamlit's memory
if 'user' not in st.session_state:
    st.session_state.user = None
if 'start_time' not in st.session_state:
    st.session_state.start_time = None

# ==========================================
# 3. AUTHENTICATION (Replaces complex JWT/Node.js auth)
# ==========================================
if st.session_state.user is None:
    st.title("📚 Welcome to StudyFlow")
    st.write("Track your late-night study sessions!")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        log_user = st.text_input("Username", key="log_user")
        log_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Login"):
            conn = sqlite3.connect('studyflow.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (log_user, hash_password(log_pass)))
            if c.fetchone():
                st.session_state.user = log_user
                st.rerun()
            else:
                st.error("Invalid username or password")
            conn.close()

    with tab2:
        reg_user = st.text_input("New Username", key="reg_user")
        reg_pass = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register"):
            conn = sqlite3.connect('studyflow.db')
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users VALUES (?, ?)", (reg_user, hash_password(reg_pass)))
                conn.commit()
                st.success("Registered successfully! You can now login.")
            except sqlite3.IntegrityError:
                st.error("Username already exists!")
            conn.close()

# ==========================================
# 4. MAIN APPLICATION (Replaces React JSX)
# ==========================================
else:
    # Sidebar Navigation
    st.sidebar.title(f"Welcome, {st.session_state.user}!")
    menu = st.sidebar.radio("Navigation", ["Home (Timer)", "My Statistics"])
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.start_time = None
        st.rerun()

    # --- HOME PAGE & TIMER ---
    if menu == "Home (Timer)":
        st.title("⏱️ Study Tracker")
        st.write("Ready to crush your syllabus?")
        
        subject = st.selectbox("What are we studying?", ["Physics", "Chemistry", "Biology", "Mock Test", "General"])
        
        # Timer Logic for Streamlit
        if st.session_state.start_time is None:
            if st.button("🚀 Start Study Session", use_container_width=True):
                st.session_state.start_time = time.time()
                st.rerun()
        else:
            elapsed_seconds = int(time.time() - st.session_state.start_time)
            mins, secs = divmod(elapsed_seconds, 60)
            hours, mins = divmod(mins, 60)
            
            st.info(f"**Session in progress:** {hours:02d}:{mins:02d}:{secs:02d}")
            st.write("*(Note: Click refresh to update the clock!)*")
            
            if st.button("⏹️ Stop & Save Session", use_container_width=True):
                duration_hours = elapsed_seconds / 3600.0
                today_date = datetime.now().strftime("%Y-%m-%d")
                
                # Save to database
                conn = sqlite3.connect('studyflow.db')
                c = conn.cursor()
                c.execute("INSERT INTO sessions (username, duration, subject, date) VALUES (?, ?, ?, ?)",
                          (st.session_state.user, duration_hours, subject, today_date))
                conn.commit()
                conn.close()
                
                st.success(f"Saved {duration_hours:.2f} hours of {subject}!")
                st.session_state.start_time = None
                st.rerun()

    # --- STATISTICS PAGE ---
    elif menu == "My Statistics":
        st.title("📊 Your Progress")
        
        conn = sqlite3.connect('studyflow.db')
        df = pd.read_sql_query("SELECT * FROM sessions WHERE username=?", conn, params=(st.session_state.user,))
        conn.close()
        
        if df.empty:
            st.write("No study sessions saved yet. Go track some time!")
        else:
            total_hours = df['duration'].sum()
            st.metric("Total Study Hours", f"{total_hours:.2f} hrs")
            
            # Chart 1: Time per Subject
            st.subheader("Hours per Subject")
            subject_data = df.groupby('subject')['duration'].sum()
            st.bar_chart(subject_data)
            
            # Chart 2: Recent History
            st.subheader("Recent Sessions")
            st.dataframe(df[['date', 'subject', 'duration']].sort_values(by='date', ascending=False), use_container_width=True)
