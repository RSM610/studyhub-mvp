import streamlit as st
import time
from utils.metrics import MetricsTracker
from utils.firebase_ops import FirebaseOps
import streamlit.components.v1 as components
import base64
from pathlib import Path

def get_dummy_ad_image():
    """Return placeholder ad image URL"""
    # Check if custom ad image exists
    custom_img = Path("assets/ad_placeholder.png")
    
    if custom_img.exists():
        with open(custom_img, "rb") as f:
            img_data = f.read()
            return base64.b64encode(img_data).decode(), "base64"
    
    # Use a nice placeholder image from the web
    placeholder_urls = [
        "https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=500&fit=crop",  # Gradient
        "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=800&h=500&fit=crop",  # Abstract gradient
        "https://images.unsplash.com/photo-1557683311-eac922347aa1?w=800&h=500&fit=crop",  # Purple gradient
        "https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=800&h=500&fit=crop",  # Pink gradient
    ]
    
    # Rotate through different images
    import random
    selected_url = random.choice(placeholder_urls)
    
    return selected_url, "url"

def show_ad():
    """Display advertisement with countdown - PropellerAds ready"""
    MetricsTracker.track_ad_impression()
    
    user_id = st.session_state.get('user', {}).get('id')
    if user_id:
        FirebaseOps.log_interaction(user_id, 'ad_shown')
    
    st.markdown("""
        <style>
        .ad-icon {
            font-size: 5rem;
            margin-bottom: 30px;
            animation: bounce 2s ease-in-out infinite;
            text-align: center;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        .countdown {
            font-size: 1.5rem;
            color: #a855f7;
            font-weight: 700;
            margin-top: 30px;
            text-align: center;
        }
        .support-text {
            color: #9333ea;
            font-size: 1.1rem;
            margin-top: 30px;
            text-align: center;
        }
        .heart {
            color: #ec4899;
            font-size: 1.5rem;
        }
        .ad-container {
            position: relative;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(167, 139, 250, 0.3);
        }
        .ad-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="ad-icon">🌸</div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; color: #ec4899; font-size: 3rem; margin-bottom: 20px;">Quick Study Break</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #9333ea; font-size: 1.3rem; margin-bottom: 40px;">Take a moment to breathe~</p>', unsafe_allow_html=True)
    
    countdown_placeholder = st.empty()
    
    # Get ad image
    ad_image, image_type = get_dummy_ad_image()
    
    # Display ad image
    if image_type == "base64":
        st.markdown(f"""
            <div style="text-align: center; margin: 30px auto; max-width: 100%; padding: 0 20px; box-sizing: border-box;">
                <div class="ad-container">
                    <img src="data:image/png;base64,{ad_image}" 
                         style="width: 100%; height: auto; display: block;" 
                         alt="Advertisement" />
                    <div class="ad-overlay">
                        <h2 style="color: #7c3aed; margin: 0 0 10px 0;">Your Ad Here</h2>
                        <p style="color: #9333ea; margin: 0;">Premium advertising space available</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="text-align: center; margin: 30px auto; max-width: 100%; padding: 0 20px; box-sizing: border-box;">
                <div class="ad-container">
                    <img src="{ad_image}" 
                         style="width: 100%; height: auto; display: block;" 
                         alt="Advertisement" />
                    <div class="ad-overlay">
                        <h2 style="color: #7c3aed; margin: 0 0 10px 0; font-size: 2rem;">✨ Your Brand Here ✨</h2>
                        <p style="color: #9333ea; margin: 10px 0; font-size: 1.1rem;">Reach thousands of students</p>
                        <p style="color: #a855f7; margin: 0; font-size: 0.9rem;">Contact: ads@studyhub.com</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Countdown
    for i in range(15, 0, -1):
        countdown_placeholder.markdown(
            f'<p class="countdown">✧ Resuming in {i} seconds ✧</p>',
            unsafe_allow_html=True
        )
        time.sleep(1)
    
    st.markdown(
        '<div class="support-text"><span class="heart">💜</span> Supporting free education for students <span class="heart">💜</span></div>',
        unsafe_allow_html=True
    )