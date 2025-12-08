import streamlit as st
import time
from utils.metrics import MetricsTracker
from utils.firebase_ops import FirebaseOps
import streamlit.components.v1 as components

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
    
    # PropellerAds Integration - RESPONSIVE LARGE AD
    propellerads_html = """
    <div style="text-align: center; margin: 30px auto; width: 100%; max-width: 1200px; padding: 0 20px; box-sizing: border-box;">
        <div id="propeller-ad-container" style="width: 100%; min-height: 500px; display: flex; align-items: center; justify-content: center;">
            <!-- PropellerAds Banner -->
            <!-- Replace YOUR_ZONE_ID with your actual Zone ID from PropellerAds -->
            
            <!-- Uncomment after getting Zone ID:
            <script type="text/javascript">
                atOptions = {
                    'key' : 'YOUR_ZONE_ID',
                    'format' : 'iframe',
                    'height' : 500,
                    'width' : 728,
                    'params' : {}
                };
            </script>
            <script type="text/javascript" src="//www.topcreativeformat.com/YOUR_ZONE_ID/invoke.js"></script>
            -->
            
            <!-- Default placeholder -->
            <div style="background: white; padding: 60px 40px; border-radius: 30px; 
                 border: 4px dashed #d8b4fe; min-height: 500px; width: 100%; max-width: 800px;
                 display: flex; align-items: center; justify-content: center; flex-direction: column;
                 box-shadow: 0 10px 40px rgba(167, 139, 250, 0.3); box-sizing: border-box;">
                <div style="font-size: 6rem; margin-bottom: 30px;">🎀</div>
                <h1 style="color: #7c3aed; margin-bottom: 20px; font-size: 3rem; text-align: center;">Ad Space</h1>
                <p style="color: #a855f7; font-size: 1.5rem; margin-bottom: 15px; font-weight: 600; text-align: center;">Ready for PropellerAds</p>
                <p style="color: #c084fc; font-size: 1rem; text-align: center; padding: 0 20px; margin-bottom: 30px; line-height: 1.6; max-width: 600px;">
                    Sign up at PropellerAds and add your Zone ID to start earning revenue from your student platform
                </p>
                <a href="https://publishers.propellerads.com/" target="_blank" 
                   style="padding: 15px 40px; background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
                   color: white; text-decoration: none; border-radius: 15px; font-weight: 700; font-size: 1.2rem;
                   box-shadow: 0 8px 25px rgba(167, 139, 250, 0.4); transition: all 0.3s ease; display: inline-block;">
                    Get Started →
                </a>
            </div>
        </div>
    </div>
    """
    
    components.html(propellerads_html, height=600)
    
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