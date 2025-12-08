import streamlit as st
from components.auth import render_auth
from components.dashboard import render_dashboard
from components.chat import render_chat
from components.ads import show_ad
from components.pomodoro import PomodoroTimer
from components.admin import render_admin_panel
from components.achievements import AchievementSystem
from components.calendar_view import render_calendar
from components.mascot import Mascot
from utils.metrics import MetricsTracker
from utils.firebase_ops import FirebaseOps
import time

st.set_page_config(
    page_title="StudyHub - By Students, For Students",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Admin email from secrets with fallback
try:
    ADMIN_EMAIL = st.secrets.get("admin", {}).get("email", "u2023610@giki.edu.pk")
except:
    ADMIN_EMAIL = "u2023610@giki.edu.pk"

if 'user' not in st.session_state:
    st.session_state.user = None

if 'ad_last_shown' not in st.session_state:
    st.session_state.ad_last_shown = time.time()

if 'selected_subject' not in st.session_state:
    st.session_state.selected_subject = None

if 'firebase_doc_id' not in st.session_state:
    st.session_state.firebase_doc_id = None

if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False

if 'show_calendar' not in st.session_state:
    st.session_state.show_calendar = False

if 'timer_paused' not in st.session_state:
    st.session_state.timer_paused = False

MetricsTracker.init_session()

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {display: none;}
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    
    .stApp {
        background: linear-gradient(to bottom, #faf5ff 0%, #fef3c7 50%, #fce7f3 100%);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
        color: white;
        border-radius: 15px;
        padding: 12px 28px;
        border: none;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(167, 139, 250, 0.4);
        font-size: 1rem;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%);
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(167, 139, 250, 0.5);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fff5f7 0%, #fef3c7 100%);
        border-right: 3px solid #fbcfe8;
    }
    
    .stTextInput > div > div > input,
    .stTextInput input {
        border-radius: 12px;
        border: 2px solid #e9d5ff !important;
        padding: 12px;
        background: white;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextInput input:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.2) !important;
    }
    
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 20px;
        padding: 25px;
        border: 3px dashed #d8b4fe;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #dcfce7 0%, #fef3c7 100%);
        border: 2px solid #86efac;
        border-radius: 15px;
        padding: 15px;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    .stSelectbox > div > div,
    .stSelectbox select {
        border-radius: 12px;
        border: 2px solid #e9d5ff;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        background: white;
        border: 2px solid #e9d5ff;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
        color: white;
    }
    
    [data-testid="stVerticalBlock"],
    [data-testid="column"],
    .element-container {
        background: transparent !important;
    }
    
    .stRadio > div {
        background: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.user:
    render_auth()
else:
    AchievementSystem.check_achievements()
    AchievementSystem.show_notifications()
    
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 3rem; margin-bottom: 10px;">✨</div>
                <h2 class="gradient-text" style="font-size: 1.8rem;">StudyHub</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 15px; 
                 text-align: center; margin-bottom: 15px; border: 2px solid #fce7f3;">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">👤</div>
                <p style="color: #7c3aed; font-weight: 600; margin: 0;">
                    {st.session_state.user['email'].split('@')[0]}
                </p>
                <p style="color: #a855f7; font-size: 0.85rem; margin: 5px 0 0 0;">
                    {st.session_state.user['email']}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🏠 Home", use_container_width=True, key="nav_home"):
                st.session_state.show_admin = False
                st.session_state.show_calendar = False
                st.session_state.selected_subject = None
                st.rerun()
        
        with col2:
            if st.button("📅 Calendar", use_container_width=True, key="nav_calendar"):
                st.session_state.show_admin = False
                st.session_state.show_calendar = True
                st.session_state.selected_subject = None
                st.rerun()
        
        # Admin button with unique key
        if st.session_state.user['email'] == ADMIN_EMAIL:
            if st.button("🛡️ Admin Panel", use_container_width=True, key="btn_show_admin"):
                st.session_state.show_admin = True
                st.session_state.show_calendar = False
                st.session_state.selected_subject = None
                st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True, key="logout_sidebar"):
            user_id = st.session_state.user['id']
            duration = MetricsTracker.get_session_duration()
            
            if st.session_state.firebase_doc_id:
                FirebaseOps.track_session_duration(st.session_state.firebase_doc_id, duration)
            
            metrics = MetricsTracker.get_metrics_summary()
            st.success(f"""
                ✨ Session Complete! ✨
                
                Time: {int(metrics['session_duration'])}s
                Messages: {metrics['messages_sent']}
                Uploads: {metrics['files_uploaded']}
                Ads: {metrics['ads_shown']}
            """)
            
            time.sleep(2)
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        
        AchievementSystem.render_achievements_panel()
        
        st.markdown("---")
        
        st.markdown("""
            <h3 class="gradient-text" style="font-size: 1.5rem; text-align: center; margin-bottom: 20px;">
                Pomodoro Timer
            </h3>
        """, unsafe_allow_html=True)
        
        # Timer with pause functionality to prevent rerun issues
        if not st.session_state.get('timer_paused', False):
            PomodoroTimer.render_timer()
    
    # Mascot bar
    Mascot.render_mascot_bar()
    
    # Ad logic
    current_time = time.time()
    if current_time - st.session_state.ad_last_shown > 150:
        show_ad()
        st.session_state.ad_last_shown = current_time
        st.rerun()
    
    # Route
    if st.session_state.show_admin:
        render_admin_panel()
    elif st.session_state.show_calendar:
        render_calendar()
    elif st.session_state.selected_subject:
        render_chat()
    else:
        render_dashboard()