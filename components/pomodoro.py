import streamlit as st
from datetime import datetime, timedelta

class PomodoroTimer:
    """Pomodoro timer with virtual plant growth - non-blocking"""
    
    @staticmethod
    def init_pomodoro():
        """Initialize pomodoro state"""
        if 'pomo_start_time' not in st.session_state:
            st.session_state.pomo_start_time = None
            st.session_state.pomo_duration = 25 * 60  # 25 minutes
            st.session_state.pomo_running = False
            st.session_state.pomo_mode = 'work'  # work or break
            st.session_state.plant_water = 0
            st.session_state.plant_stage = 0  # 0: seed, 1: sprout, 2: small, 3: medium, 4: full
            st.session_state.last_water = datetime.now()
        
        # Initialize completed_cycles if not exists
        if 'completed_cycles' not in st.session_state:
            st.session_state.completed_cycles = 0
    
    @staticmethod
    def get_time_left():
        """Calculate time left without blocking"""
        if not st.session_state.pomo_running or not st.session_state.pomo_start_time:
            return st.session_state.pomo_duration
        
        elapsed = (datetime.now() - st.session_state.pomo_start_time).total_seconds()
        remaining = max(0, st.session_state.pomo_duration - elapsed)
        
        # Check if cycle complete
        if remaining == 0 and st.session_state.pomo_running:
            PomodoroTimer.complete_cycle()
        
        return int(remaining)
    
    @staticmethod
    def complete_cycle():
        """Complete a pomodoro cycle"""
        if st.session_state.pomo_mode == 'work':
            # Water plant automatically
            st.session_state.plant_water += 5
            st.session_state.completed_cycles += 1
            
            # Grow plant if enough water
            if st.session_state.plant_water >= 20 and st.session_state.plant_stage < 4:
                st.session_state.plant_stage += 1
                st.session_state.plant_water = 0
                st.balloons()
            
            # Switch to break
            st.session_state.pomo_mode = 'break'
            st.session_state.pomo_duration = 5 * 60
        else:
            # Switch to work
            st.session_state.pomo_mode = 'work'
            st.session_state.pomo_duration = 25 * 60
        
        st.session_state.pomo_running = False
        st.session_state.pomo_start_time = None
        st.session_state.last_water = datetime.now()
    
    @staticmethod
    def get_plant_emoji():
        """Get plant emoji based on growth stage"""
        plants = ['🌱', '🌿', '🪴', '🌳', '🌸']
        stage = min(st.session_state.plant_stage, 4)
        return plants[stage]
    
    @staticmethod
    def water_plant():
        """Water the plant manually"""
        st.session_state.plant_water += 5
        if st.session_state.plant_water >= 20 and st.session_state.plant_stage < 4:
            st.session_state.plant_stage += 1
            st.session_state.plant_water = 0
            st.balloons()
        st.session_state.last_water = datetime.now()
    
    @staticmethod
    def check_plant_health():
        """Check if plant needs water (withers after 48 hours)"""
        hours_since_water = (datetime.now() - st.session_state.last_water).total_seconds() / 3600
        if hours_since_water > 48 and st.session_state.plant_stage > 0:
            st.session_state.plant_stage = max(0, st.session_state.plant_stage - 1)
            st.session_state.last_water = datetime.now()
    
    @staticmethod
    def render_timer():
        """Render the pomodoro timer - non-blocking"""
        PomodoroTimer.init_pomodoro()
        PomodoroTimer.check_plant_health()
        
        st.markdown("""
            <style>
            .plant-display {
                font-size: 4rem;
                margin: 15px 0;
                animation: gentle-sway 3s ease-in-out infinite;
            }
            @keyframes gentle-sway {
                0%, 100% { transform: rotate(-2deg); }
                50% { transform: rotate(2deg); }
            }
            .water-bar {
                background: #e9d5ff;
                height: 10px;
                border-radius: 10px;
                overflow: hidden;
                margin: 15px 0;
            }
            .water-fill {
                background: linear-gradient(90deg, #a78bfa 0%, #ec4899 100%);
                height: 100%;
                transition: width 0.3s ease;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Plant display
        plant = PomodoroTimer.get_plant_emoji()
        st.markdown(f'<div class="plant-display" style="text-align: center;">{plant}</div>', unsafe_allow_html=True)
        
        # Growth stage
        stage_names = ['Seed', 'Sprout', 'Seedling', 'Young Plant', 'Blooming!']
        st.markdown(f'<p style="color: #9333ea; font-weight: 600; margin: 0; text-align: center;">Stage: {stage_names[st.session_state.plant_stage]}</p>', unsafe_allow_html=True)
        
        # Stats
        st.markdown(f'<p style="text-align: center; color: #7c3aed; margin: 10px 0;">🔥 {st.session_state.completed_cycles} cycles completed</p>', unsafe_allow_html=True)
        
        # Water bar
        water_percent = (st.session_state.plant_water / 20) * 100
        st.markdown(f"""
            <div class="water-bar">
                <div class="water-fill" style="width: {water_percent}%"></div>
            </div>
            <p style="color: #a855f7; font-size: 0.9rem; margin: 5px 0; text-align: center;">Water: {st.session_state.plant_water}/20 💧</p>
        """, unsafe_allow_html=True)
        
        # Timer display
        time_left = PomodoroTimer.get_time_left()
        minutes = time_left // 60
        seconds = time_left % 60
        mode_emoji = '📚' if st.session_state.pomo_mode == 'work' else '☕'
        
        st.markdown(f'<h1 style="text-align: center; color: #7c3aed; margin: 20px 0;">{mode_emoji} {minutes:02d}:{seconds:02d}</h1>', unsafe_allow_html=True)
        
        # Controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Start" if not st.session_state.pomo_running else "⏸️ Pause", 
                        use_container_width=True, type="primary", key="pomo_start"):
                if not st.session_state.pomo_running:
                    st.session_state.pomo_running = True
                    st.session_state.pomo_start_time = datetime.now()
                else:
                    st.session_state.pomo_running = False
                    # Save remaining time
                    remaining = PomodoroTimer.get_time_left()
                    st.session_state.pomo_duration = remaining
                    st.session_state.pomo_start_time = None
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset", use_container_width=True, key="pomo_reset"):
                if st.session_state.pomo_mode == 'work':
                    st.session_state.pomo_duration = 25 * 60
                else:
                    st.session_state.pomo_duration = 5 * 60
                st.session_state.pomo_running = False
                st.session_state.pomo_start_time = None
                st.rerun()
        
        with col3:
            if st.button("💧 Water", use_container_width=True, key="pomo_water"):
                PomodoroTimer.water_plant()
                st.rerun()
        
        # Auto-refresh if timer is running
        if st.session_state.pomo_running:
            st.rerun()