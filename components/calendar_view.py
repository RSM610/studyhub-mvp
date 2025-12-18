import streamlit as st
from datetime import datetime, timedelta
from utils.firebase_ops import FirebaseOps
from config.firebase_config import db

def render_calendar():
    """Render calendar schedule planner with proper persistence and logic"""
    
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
        .today-header {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize calendar state with Firebase persistence
    user_id = st.session_state.get('user', {}).get('id')
    
    if not user_id:
        st.error("❌ Please log in to use the calendar")
        return
    
    # Load calendar events from Firebase on first render
    if 'calendar_events' not in st.session_state or 'calendar_loaded' not in st.session_state:
        try:
            # Try to load from Firebase
            user_calendar = db.collection('calendars').document(user_id).get()
            
            if user_calendar.exists:
                calendar_data = user_calendar.to_dict()
                st.session_state.calendar_events = calendar_data.get('events', {})
            else:
                st.session_state.calendar_events = {}
            
            st.session_state.calendar_loaded = True
        except Exception as e:
            st.warning(f"Could not load calendar from Firebase: {e}")
            st.session_state.calendar_events = {}
            st.session_state.calendar_loaded = True
    
    # Initialize current_week_start
    if 'current_week_start' not in st.session_state:
        today = datetime.now().date()
        # Set to Monday of current week
        days_since_monday = today.weekday()
        st.session_state.current_week_start = today - timedelta(days=days_since_monday)
    
    st.title("📅 Study Schedule")
    st.write("Plan your week and stay organized~")
    
    # Week selector
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Previous Week", use_container_width=True, key="prev_week"):
            st.session_state.current_week_start -= timedelta(days=7)
            st.rerun()
    
    with col2:
        week_end = st.session_state.current_week_start + timedelta(days=6)
        st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <p style="color: #7c3aed; font-weight: 700; font-size: 1.1rem; margin: 0;">
                    {st.session_state.current_week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("Next Week →", use_container_width=True, key="next_week"):
            st.session_state.current_week_start += timedelta(days=7)
            st.rerun()
    
    # Today button for quick navigation
    today = datetime.now().date()
    today_week_start = today - timedelta(days=today.weekday())
    
    if st.session_state.current_week_start != today_week_start:
        if st.button("📍 Jump to Current Week", use_container_width=True, key="jump_today"):
            st.session_state.current_week_start = today_week_start
            st.rerun()
    
    st.markdown("---")
    
    # Add new event section
    with st.expander("➕ Add New Study Session", expanded=False):
        # Use unique keys with timestamp to prevent conflicts
        event_key = st.session_state.get('event_form_key', datetime.now().timestamp())
        
        new_date = st.date_input(
            "Date",
            value=datetime.now().date(),
            key=f"new_event_date_{event_key}"
        )
        
        new_subject = st.text_input(
            "Subject",
            placeholder="e.g., Physics, Business, etc.",
            key=f"new_event_subject_{event_key}"
        )
        
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            new_start = st.time_input(
                "Start Time",
                value=datetime.now().time(),
                key=f"new_event_start_{event_key}"
            )
        
        with col_time2:
            # Default end time is 1 hour after start
            default_end = (datetime.combine(datetime.today(), new_start) + timedelta(hours=1)).time()
            new_end = st.time_input(
                "End Time",
                value=default_end,
                key=f"new_event_end_{event_key}"
            )
        
        new_notes = st.text_area(
            "Notes (optional)",
            placeholder="Topics to cover, homework, etc.",
            key=f"new_event_notes_{event_key}",
            height=100
        )
        
        if st.button("✨ Add to Schedule", type="primary", use_container_width=True, key=f"add_event_{event_key}"):
            if new_subject and new_subject.strip():
                # Validate time logic
                if new_start >= new_end:
                    st.error("❌ End time must be after start time!")
                else:
                    date_key = new_date.isoformat()
                    
                    if date_key not in st.session_state.calendar_events:
                        st.session_state.calendar_events[date_key] = []
                    
                    event = {
                        'subject': new_subject.strip(),
                        'start_time': new_start.strftime('%H:%M'),
                        'end_time': new_end.strftime('%H:%M'),
                        'notes': new_notes.strip(),
                        'completed': False,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    st.session_state.calendar_events[date_key].append(event)
                    
                    # Sort events by start time
                    st.session_state.calendar_events[date_key].sort(
                        key=lambda x: x['start_time']
                    )
                    
                    # Save to Firebase
                    try:
                        db.collection('calendars').document(user_id).set({
                            'user_id': user_id,
                            'events': st.session_state.calendar_events,
                            'last_updated': datetime.now()
                        })
                    except Exception as e:
                        st.warning(f"Could not save to Firebase: {e}")
                    
                    st.success(f"✨ Added {new_subject} to schedule!")
                    
                    # Update form key to reset form
                    st.session_state.event_form_key = datetime.now().timestamp()
                    st.rerun()
            else:
                st.error("❌ Please enter a subject name")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display week view
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_emojis = ['📚', '📝', '📖', '✏️', '🎯', '🌟', '💫']
    
    for i in range(7):
        current_day = st.session_state.current_week_start + timedelta(days=i)
        date_key = current_day.isoformat()
        
        # Day header
        is_today = current_day == datetime.now().date()
        header_class = "day-header today-header" if is_today else "day-header"
        
        st.markdown(f'<div class="{header_class}">', unsafe_allow_html=True)
        st.markdown(
            f'{day_emojis[i]} {days[i]} - {current_day.strftime("%b %d")}'
            f'{"  (Today)" if is_today else ""}',
            unsafe_allow_html=True
        )
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
                    completed_style = "text-decoration: line-through; opacity: 0.6;" if event.get('completed', False) else ""
                    
                    st.markdown(f"""
                        <h4 style="color: #7c3aed; margin: 0 0 10px 0; {completed_style}">
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
                    # Toggle completion
                    toggle_text = "↻" if event.get('completed', False) else "✓"
                    toggle_key = f"toggle_{date_key}_{idx}_{event.get('created_at', '')}"
                    
                    if st.button(toggle_text, key=toggle_key, use_container_width=True):
                        st.session_state.calendar_events[date_key][idx]['completed'] = \
                            not event.get('completed', False)
                        
                        # Save to Firebase
                        try:
                            db.collection('calendars').document(user_id).set({
                                'user_id': user_id,
                                'events': st.session_state.calendar_events,
                                'last_updated': datetime.now()
                            })
                        except Exception as e:
                            st.warning(f"Could not save to Firebase: {e}")
                        
                        st.rerun()
                    
                    # Delete button
                    delete_key = f"delete_{date_key}_{idx}_{event.get('created_at', '')}"
                    if st.button("🗑️", key=delete_key, use_container_width=True):
                        st.session_state.calendar_events[date_key].pop(idx)
                        
                        # Clean up empty days
                        if not st.session_state.calendar_events[date_key]:
                            del st.session_state.calendar_events[date_key]
                        
                        # Save to Firebase
                        try:
                            db.collection('calendars').document(user_id).set({
                                'user_id': user_id,
                                'events': st.session_state.calendar_events,
                                'last_updated': datetime.now()
                            })
                        except Exception as e:
                            st.warning(f"Could not save to Firebase: {e}")
                        
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Week summary with proper date range calculation
    week_start = st.session_state.current_week_start
    week_end = week_start + timedelta(days=6)
    
    # Count sessions for current week only
    total_sessions = 0
    completed_sessions = 0
    
    for i in range(7):
        current_day = week_start + timedelta(days=i)
        date_key = current_day.isoformat()
        day_events = st.session_state.calendar_events.get(date_key, [])
        
        total_sessions += len(day_events)
        completed_sessions += sum(1 for event in day_events if event.get('completed', False))
    
    # Calculate completion percentage
    completion_percentage = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dcfce7 0%, #fef3c7 100%);
             padding: 20px; border-radius: 15px; margin-top: 30px;
             border: 2px solid #86efac; text-align: center;">
            <p style="color: #059669; font-weight: 700; font-size: 1.2rem; margin: 0 0 10px 0;">
                Week Progress: {completed_sessions}/{total_sessions} sessions completed
            </p>
            <div style="background: white; height: 20px; border-radius: 10px; overflow: hidden; margin: 10px auto; max-width: 300px;">
                <div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); 
                     height: 100%; width: {completion_percentage}%; transition: width 0.3s ease;"></div>
            </div>
            <p style="color: #059669; font-weight: 600; font-size: 1rem; margin: 10px 0 0 0;">
                {completion_percentage:.0f}% Complete 🎉
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Overall statistics
    st.markdown("---")
    st.subheader("📊 Overall Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate all-time statistics
    all_events = []
    for date_events in st.session_state.calendar_events.values():
        all_events.extend(date_events)
    
    total_all_time = len(all_events)
    completed_all_time = sum(1 for event in all_events if event.get('completed', False))
    upcoming_count = sum(
        1 for date_key, events in st.session_state.calendar_events.items()
        for event in events
        if datetime.fromisoformat(date_key).date() >= datetime.now().date()
        and not event.get('completed', False)
    )
    overdue_count = sum(
        1 for date_key, events in st.session_state.calendar_events.items()
        for event in events
        if datetime.fromisoformat(date_key).date() < datetime.now().date()
        and not event.get('completed', False)
    )
    
    with col1:
        st.metric("Total Sessions", total_all_time)
    
    with col2:
        st.metric("Completed", completed_all_time)
    
    with col3:
        st.metric("Upcoming", upcoming_count)
    
    with col4:
        st.metric("Overdue", overdue_count, delta=f"-{overdue_count}" if overdue_count > 0 else None)
    
    # Clear completed sessions button
    if completed_all_time > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        col_clear1, col_clear2, col_clear3 = st.columns([1, 1, 1])
        
        with col_clear2:
            if st.button("🧹 Clear All Completed Sessions", use_container_width=True):
                # Remove all completed events
                for date_key in list(st.session_state.calendar_events.keys()):
                    st.session_state.calendar_events[date_key] = [
                        event for event in st.session_state.calendar_events[date_key]
                        if not event.get('completed', False)
                    ]
                    
                    # Clean up empty days
                    if not st.session_state.calendar_events[date_key]:
                        del st.session_state.calendar_events[date_key]
                
                # Save to Firebase
                try:
                    db.collection('calendars').document(user_id).set({
                        'user_id': user_id,
                        'events': st.session_state.calendar_events,
                        'last_updated': datetime.now()
                    })
                    st.success(f"✨ Cleared {completed_all_time} completed sessions!")
                except Exception as e:
                    st.error(f"Could not save to Firebase: {e}")
                
                st.rerun()