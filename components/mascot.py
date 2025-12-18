import streamlit as st
from datetime import datetime
import random

class Mascot:
    """Interactive pet mascot that walks across the screen"""
    
    MOODS = {
        'happy': {'emoji': '🐱', 'messages': ['Meow~', 'Let\'s study!', 'You\'re doing great!', 'Keep going~']},
        'excited': {'emoji': '😸', 'messages': ['Yay!', 'Amazing!', 'So proud!', '✨']},
        'sleepy': {'emoji': '😴', 'messages': ['Zzz...', 'Need break?', '*yawn*', 'Tired...']},
        'playful': {'emoji': '😺', 'messages': ['Play with me!', 'Pet me!', '*purr*', 'Hello~']},
        'studying': {'emoji': '📚', 'messages': ['Reading...', 'Learning!', 'Smart!', 'Focus!']}
    }
    
    @staticmethod
    def init_mascot():
        """Initialize mascot state"""
        if 'mascot_happiness' not in st.session_state:
            st.session_state.mascot_happiness = 50
            st.session_state.mascot_position = 10
            st.session_state.mascot_mood = 'happy'
            st.session_state.mascot_message = ''
            st.session_state.last_interaction = datetime.now()
            st.session_state.mascot_name = 'Mochi'
    
    @staticmethod
    def update_happiness():
        """Update happiness based on study activity"""
        time_since_interaction = (datetime.now() - st.session_state.last_interaction).total_seconds()
        if time_since_interaction > 300:
            st.session_state.mascot_happiness = max(0, st.session_state.mascot_happiness - 1)
        
        if st.session_state.get('completed_cycles', 0) > 0:
            st.session_state.mascot_happiness = min(100, st.session_state.mascot_happiness + 1)
    
    @staticmethod
    def get_mood():
        """Determine mood based on happiness"""
        happiness = st.session_state.mascot_happiness
        if happiness >= 80:
            return 'excited'
        elif happiness >= 60:
            return 'happy'
        elif happiness >= 40:
            return 'playful'
        else:
            return 'sleepy'
    
    @staticmethod
    def interact():
        """Interact with mascot"""
        st.session_state.mascot_happiness = min(100, st.session_state.mascot_happiness + 10)
        st.session_state.last_interaction = datetime.now()
        mood = Mascot.get_mood()
        messages = Mascot.MOODS[mood]['messages']
        st.session_state.mascot_message = random.choice(messages)
    
    @staticmethod
    def render_mascot_bar():
        """Render mascot bar at top of screen"""
        Mascot.init_mascot()
        Mascot.update_happiness()
        
        mood = Mascot.get_mood()
        st.session_state.mascot_mood = mood
        emoji = Mascot.MOODS[mood]['emoji']
        
        # Update position (walk animation) - but don't trigger rerun
        st.session_state.mascot_position = (st.session_state.mascot_position + 0.5) % 90
        
        # Display mascot info
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        
        with col1:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span style="font-size: 2.5rem;">{emoji}</span>
                    <div>
                        <span style="color: #7c3aed; font-weight: 700; font-size: 1.1rem;">
                            {st.session_state.mascot_name}
                        </span>
                        <div style="background: #e9d5ff; height: 8px; width: 120px; border-radius: 10px; overflow: hidden; margin-top: 5px;">
                            <div style="background: linear-gradient(90deg, #a78bfa 0%, #ec4899 100%); 
                                 height: 100%; width: {st.session_state.mascot_happiness}%; 
                                 transition: width 0.3s ease;"></div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("🎮 Play", key="mascot_play_btn", use_container_width=True):
                Mascot.interact()
                st.rerun()
        
        with col3:
            if st.button("🍰 Feed", key="mascot_feed_btn", use_container_width=True):
                st.session_state.mascot_happiness = min(100, st.session_state.mascot_happiness + 15)
                st.session_state.mascot_message = "Yummy! 😋"
                st.session_state.last_interaction = datetime.now()
                st.rerun()
        
        with col4:
            if st.button("✨ Pet", key="mascot_pet_btn", use_container_width=True):
                Mascot.interact()
                st.balloons()
                st.rerun()
        
        with col5:
            if st.session_state.mascot_message:
                st.info(st.session_state.mascot_message)