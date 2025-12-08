import streamlit as st
from datetime import datetime, timedelta
from utils.firebase_ops import FirebaseOps

def render_calendar():
    """Render calendar schedule planner"""
    
    st.markdown("""
        <style>
        .event-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin: 10px 0;
            border: 2px solid #e9d5ff;
            transition: all 0.3s ease;
        }
        .event-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(167, 139, 250, 0.3);
            border-color: #a78bfa;
        }
        .day-header {
            background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
            color: white;
            padding: 15px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 1.2rem;
            margin: 20px 0 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize calendar state
    if 'calendar_events' not in st.session_state:
        st.session_state.calendar_events = {}
    
    st.title("📅 Study Schedule")
    st.write("Plan your week and stay organized~")
    
    # Week selector
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Previous Week", use_container_width=True):
            if 'current_week_start' not in st.session_state:
                st.session_state.current_week_start = datetime.now().date()
            st.session_state.current_week_start -= timedelta(days=7)
            st.rerun()
    
    with col2:
        if 'current_week_start' not in st.session_state:
            st.session_state.current_week_start = datetime.now().date()
            # Set to Monday of current week
            days_since_monday = st.session_state.current_week_start.weekday()
            st.session_state.current_week_start -= timedelta(days=days_since_monday)
        
        week_end = st.session_state.current_week_start + timedelta(days=6)
        st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <p style="color: #7c3aed; font-weight: 700; font-size: 1.1rem; margin: 0;">
                    {st.session_state.current_week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("Next Week →", use_container_width=True):
            st.session_state.current_week_start += timedelta(days=7)
            st.rerun()
    
    st.markdown("---")
    
    # Add new event section
    with st.expander("➕ Add New Study Session", expanded=False):
        new_date = st.date_input(
            "Date",
            value=datetime.now().date(),
            key="new_event_date"
        )
        
        new_subject = st.text_input(
            "Subject",
            placeholder="e.g., Physics, Business, etc.",
            key="new_event_subject"
        )
        
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            new_start = st.time_input(
                "Start Time",
                value=datetime.now().time(),
                key="new_event_start"
            )
        
        with col_time2:
            new_end = st.time_input(
                "End Time",
                value=(datetime.now() + timedelta(hours=1)).time(),
                key="new_event_end"
            )
        
        new_notes = st.text_area(
            "Notes (optional)",
            placeholder="Topics to cover, homework, etc.",
            key="new_event_notes",
            height=100
        )
        
        if st.button("✨ Add to Schedule", type="primary", use_container_width=True):
            if new_subject:
                date_key = new_date.isoformat()
                if date_key not in st.session_state.calendar_events:
                    st.session_state.calendar_events[date_key] = []
                
                event = {
                    'subject': new_subject,
                    'start_time': new_start.strftime('%H:%M'),
                    'end_time': new_end.strftime('%H:%M'),
                    'notes': new_notes,
                    'completed': False
                }
                st.session_state.calendar_events[date_key].append(event)
                st.success(f"✨ Added {new_subject} to schedule!")
                st.rerun()
            else:
                st.error("Please enter a subject name")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display week view
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_emojis = ['📚', '📝', '📖', '✏️', '🎯', '🌟', '💫']
    
    for i in range(7):
        current_day = st.session_state.current_week_start + timedelta(days=i)
        date_key = current_day.isoformat()
        
        # Day header
        is_today = current_day == datetime.now().date()
        header_style = "background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);" if is_today else ""
        
        st.markdown(f'<div class="day-header" style="{header_style}">', unsafe_allow_html=True)
        st.markdown(f'{day_emojis[i]} {days[i]} - {current_day.strftime("%b %d")}{"  (Today)" if is_today else ""}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Events for this day
        events = st.session_state.calendar_events.get(date_key, [])
        
        if not events:
            st.markdown("""
                <div style="text-align: center; color: #9ca3af; padding: 20px; font-style: italic;">
                    No sessions scheduled for this day
                </div>
            """, unsafe_allow_html=True)
        else:
            for idx, event in enumerate(events):
                st.markdown('<div class="event-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    completed_emoji = "✅" if event.get('completed', False) else "⏰"
                    st.markdown(f"""
                        <h4 style="color: #7c3aed; margin: 0 0 10px 0;">
                            {completed_emoji} {event['subject']}
                        </h4>
                        <p style="color: #6b7280; margin: 5px 0; font-size: 0.95rem;">
                            🕐 {event['start_time']} - {event['end_time']}
                        </p>
                    """, unsafe_allow_html=True)
                    
                    if event.get('notes'):
                        st.markdown(f"""
                            <p style="color: #9333ea; margin: 10px 0 0 0; font-size: 0.9rem;">
                                📝 {event['notes']}
                            </p>
                        """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("✓" if not event.get('completed', False) else "↻", 
                               key=f"toggle_{date_key}_{idx}",
                               use_container_width=True):
                        event['completed'] = not event.get('completed', False)
                        st.rerun()
                    
                    if st.button("🗑️", key=f"delete_{date_key}_{idx}", use_container_width=True):
                        st.session_state.calendar_events[date_key].pop(idx)
                        if not st.session_state.calendar_events[date_key]:
                            del st.session_state.calendar_events[date_key]
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Week summary
    total_sessions = sum(len(events) for events in st.session_state.calendar_events.values())
    completed_sessions = sum(
        sum(1 for event in events if event.get('completed', False))
        for events in st.session_state.calendar_events.values()
    )
    
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dcfce7 0%, #fef3c7 100%);
             padding: 20px; border-radius: 15px; margin-top: 30px;
             border: 2px solid #86efac; text-align: center;">
            <p style="color: #059669; font-weight: 700; font-size: 1.2rem; margin: 0;">
                Week Progress: {completed_sessions}/{total_sessions} sessions completed 🎉
            </p>
        </div>
    """, unsafe_allow_html=True)