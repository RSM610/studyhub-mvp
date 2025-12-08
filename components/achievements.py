import streamlit as st
from datetime import datetime

class AchievementSystem:
    """Manage achievements and plant collection"""
    
    ACHIEVEMENTS = {
        'first_session': {
            'name': 'First Steps',
            'description': 'Complete your first study session',
            'plant': '🌱',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 1
        },
        'early_bird': {
            'name': 'Early Bird',
            'description': 'Study 5 sessions',
            'plant': '🌿',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 5
        },
        'dedicated': {
            'name': 'Dedicated Student',
            'description': 'Study 10 sessions',
            'plant': '🪴',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 10
        },
        'tree_hugger': {
            'name': 'Tree Hugger',
            'description': 'Study 20 sessions',
            'plant': '🌳',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 20
        },
        'blooming': {
            'name': 'In Full Bloom',
            'description': 'Study 30 sessions',
            'plant': '🌸',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 30
        },
        'cherry_blossom': {
            'name': 'Cherry Blossom',
            'description': 'Study 40 sessions',
            'plant': '🌺',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 40
        },
        'sunflower': {
            'name': 'Sunflower Scholar',
            'description': 'Study 50 sessions',
            'plant': '🌻',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 50
        },
        'rose_garden': {
            'name': 'Rose Garden',
            'description': 'Study 75 sessions',
            'plant': '🌹',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 75
        },
        'lotus': {
            'name': 'Lotus Master',
            'description': 'Study 100 sessions',
            'plant': '🪷',
            'requirement': lambda: st.session_state.get('completed_cycles', 0) >= 100
        }
    }
    
    @staticmethod
    def init_achievements():
        """Initialize achievement tracking"""
        if 'unlocked_achievements' not in st.session_state:
            st.session_state.unlocked_achievements = []
            st.session_state.new_achievements = []
        if 'completed_cycles' not in st.session_state:
            st.session_state.completed_cycles = 0
    
    @staticmethod
    def check_achievements():
        """Check for newly unlocked achievements"""
        AchievementSystem.init_achievements()
        
        for key, achievement in AchievementSystem.ACHIEVEMENTS.items():
            if key not in st.session_state.unlocked_achievements:
                if achievement['requirement']():
                    st.session_state.unlocked_achievements.append(key)
                    st.session_state.new_achievements.append(key)
    
    @staticmethod
    def show_notifications():
        """Display achievement notifications"""
        if st.session_state.get('new_achievements', []):
            for key in st.session_state.new_achievements[:]:
                achievement = AchievementSystem.ACHIEVEMENTS[key]
                st.success(f"""
                    🎉 **Achievement Unlocked!** 🎉
                    
                    {achievement['plant']} **{achievement['name']}**
                    
                    {achievement['description']}
                """)
                st.balloons()
            st.session_state.new_achievements = []
    
    @staticmethod
    def render_achievements_panel():
        """Render achievements in sidebar"""
        AchievementSystem.init_achievements()
        
        st.markdown("""
            <div style="background: white; padding: 20px; border-radius: 15px; 
                 margin: 20px 0; border: 2px solid #fce7f3;">
                <h3 style="color: #7c3aed; text-align: center; margin-bottom: 15px;">
                    🏆 Plant Collection
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        unlocked_count = len(st.session_state.unlocked_achievements)
        total_count = len(AchievementSystem.ACHIEVEMENTS)
        
        st.markdown(f"""
            <p style="text-align: center; color: #9333ea; font-weight: 600; margin-bottom: 15px;">
                {unlocked_count}/{total_count} Plants Collected
            </p>
        """, unsafe_allow_html=True)
        
        # Show unlocked plants
        cols = st.columns(3)
        for idx, (key, achievement) in enumerate(AchievementSystem.ACHIEVEMENTS.items()):
            with cols[idx % 3]:
                if key in st.session_state.unlocked_achievements:
                    st.markdown(f"""
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 2rem;">{achievement['plant']}</div>
                            <p style="font-size: 0.7rem; color: #7c3aed; margin: 0;">
                                {achievement['name']}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="text-align: center; padding: 10px; opacity: 0.3;">
                            <div style="font-size: 2rem;">🔒</div>
                            <p style="font-size: 0.7rem; color: #9ca3af; margin: 0;">
                                Locked
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
        
        # Progress to next achievement
        next_achievement = None
        for key, achievement in AchievementSystem.ACHIEVEMENTS.items():
            if key not in st.session_state.unlocked_achievements:
                next_achievement = (key, achievement)
                break
        
        if next_achievement:
            key, achievement = next_achievement
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fef3c7 0%, #fce7f3 100%);
                     padding: 15px; border-radius: 15px; margin-top: 15px;
                     border: 2px solid #fbcfe8; text-align: center;">
                    <p style="color: #7c3aed; font-weight: 600; margin: 0; font-size: 0.9rem;">
                        Next: {achievement['plant']} {achievement['name']}
                    </p>
                    <p style="color: #9333ea; font-size: 0.8rem; margin: 5px 0 0 0;">
                        {achievement['description']}
                    </p>
                </div>
            """, unsafe_allow_html=True)