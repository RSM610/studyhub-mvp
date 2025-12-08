import streamlit as st
from utils.firebase_ops import FirebaseOps
import uuid
import hashlib
import time
from datetime import datetime

def hash_password(password):
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(email, password):
    """Verify user credentials from Firebase"""
    from config.firebase_config import db
    try:
        users = list(db.collection('users').where(field_path='email', op_string='==', value=email).limit(1).stream())
        
        if users:
            user_doc = users[0].to_dict()
            return user_doc['password_hash'] == hash_password(password), user_doc.get('user_id')
        return False, None
    except Exception as e:
        st.error(f"Verification error: {e}")
        return False, None

def create_user(email, password):
    """Create new user in Firebase"""
    from config.firebase_config import db
    try:
        # Check if user already exists
        existing = list(db.collection('users').where(field_path='email', op_string='==', value=email).limit(1).stream())
        if len(existing) > 0:
            return False, "Email already registered"
        
        # Create user
        user_id = str(uuid.uuid4())
        db.collection('users').add({
            'user_id': user_id,
            'email': email,
            'password_hash': hash_password(password),
            'created_at': datetime.now()
        })
        return True, user_id
    except Exception as e:
        st.error(f"Create user error: {e}")
        return False, str(e)

def render_auth():
    """Render authentication interface"""
    
    st.markdown("""
        <style>
        .auth-container {
            max-width: 420px;
            margin: 80px auto;
            padding: 50px;
            background: linear-gradient(135deg, #fff5f7 0%, #f3e7ff 100%);
            border-radius: 30px;
            box-shadow: 0 20px 60px rgba(167, 139, 250, 0.3);
            border: 3px solid #fce7f3;
        }
        .cute-icon {
            font-size: 4rem;
            text-align: center;
            margin-bottom: 20px;
            animation: float 3s ease-in-out infinite;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        .auth-title {
            text-align: center;
            background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.8rem;
            font-weight: 800;
            margin-bottom: 10px;
        }
        .auth-subtitle {
            text-align: center;
            color: #9333ea;
            font-size: 1.1rem;
            margin-bottom: 40px;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="cute-icon">✨📚✨</div>', unsafe_allow_html=True)
        st.markdown('<h1 class="auth-title">StudyHub</h1>', unsafe_allow_html=True)
        st.markdown('<p class="auth-subtitle">✧ by students, for students ✧</p>', unsafe_allow_html=True)
        
        # Tab for login/signup
        auth_mode = st.radio(
            "Authentication Mode",
            ["Sign In", "Sign Up"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        email = st.text_input(
            "Email Address",
            placeholder="your.name@university.edu",
            key="email_input",
            label_visibility="visible"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
            key="password_input",
            label_visibility="visible"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if auth_mode == "Sign In":
            if st.button("Sign In ✨", use_container_width=True, type="primary"):
                if email and password:
                    verified, user_id = verify_user(email, password)
                    if verified:
                        st.session_state.user = {
                            'id': user_id,
                            'email': email
                        }
                        doc_id = FirebaseOps.create_user_session(user_id, email)
                        st.session_state.firebase_doc_id = doc_id
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password")
                else:
                    st.error("Please enter both email and password")
        
        else:  # Sign Up
            if st.button("Create Account ✨", use_container_width=True, type="primary"):
                if email and password:
                    if len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, result = create_user(email, password)
                        if success:
                            st.success("✨ Account created! Switching to sign in...")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
                else:
                    st.error("Please enter both email and password")
        
        st.markdown('<p style="text-align: center; color: #c084fc; font-size: 0.85rem; margin-top: 30px;">Made with 💜 by students</p>', unsafe_allow_html=True)