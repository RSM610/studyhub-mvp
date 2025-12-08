import streamlit as st
import time
from utils.metrics import MetricsTracker
from utils.firebase_ops import FirebaseOps
import streamlit.components.v1 as components
import base64
from pathlib import Path

def get_dummy_ad_image():
    """Return base64 encoded placeholder image or use user's custom image"""
    # Check if custom ad image exists
    custom_img = Path("assets/ad_placeholder.png")
    
    if custom_img.exists():
        with open(custom_img, "rb") as f:
            img_data = f.read()
            return base64.b64encode(img_data).decode()
    
    # Return SVG placeholder if no custom image
    svg_placeholder = """
    <svg width="800" height="500" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#a78bfa;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#ec4899;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="800" height="500" fill="url(#grad1)" rx="30"/>
      <text x="400" y="200" font-family="Arial, sans-serif" font-size="80" fill="white" text-anchor="middle">🎀</text>
      <text x="400" y="280" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="white" text-anchor="middle">Your Ad Here</text>
      <text x="400" y="330" font-family="Arial, sans-serif" font-size="24" fill="white" text-anchor="middle">Ready for PropellerAds</text>
      <text x="400" y="380" font-family="Arial, sans-serif" font-size="18" fill="rgba(255,255,255,0.8)" text-anchor="middle">Replace assets/ad_placeholder.png with your ad image</text>
      <rect x="300" y="420" width="200" height="50" rx="10" fill="white" fill-opacity="0.2"/>
      <text x="400" y="453" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="white" text-anchor="middle">Get Started →</text>
    </svg>
    """
    return base64.b64encode(svg_placeholder.encode()).decode()

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
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="ad-icon">🌸</div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; color: #ec4899; font-size: 3rem; margin-bottom: 20px;">Quick Study Break</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #9333ea; font-size: 1.3rem; margin-bottom: 40px;">Take a moment to breathe~</p>', unsafe_allow_html=True)
    
    countdown_placeholder = st.empty()
    
    # Get ad image
    ad_image_b64 = get_dummy_ad_image()
    
    # Display ad image
    st.markdown(f"""
        <div style="text-align: center; margin: 30px auto; max-width: 100%; padding: 0 20px; box-sizing: border-box;">
            <img src="data:image/png;base64,{ad_image_b64}" 
                 style="max-width: 100%; height: auto; border-radius: 20px; box-shadow: 0 10px 40px rgba(167, 139, 250, 0.3);" 
                 alt="Advertisement" />
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="text-align: center; margin-top: 20px; color: #9333ea; font-size: 0.9rem;">
            💡 <strong>To add your ad:</strong><br>
            1. Create folder: <code>assets/</code><br>
            2. Add image: <code>assets/ad_placeholder.png</code><br>
            3. Or integrate PropellerAds script above
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