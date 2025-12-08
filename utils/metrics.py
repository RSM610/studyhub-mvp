import streamlit as st
from datetime import datetime

class MetricsTracker:
    """Track user engagement metrics during session"""
    
    @staticmethod
    def init_session():
        """Initialize session tracking variables"""
        if 'session_start' not in st.session_state:
            st.session_state.session_start = datetime.now()
            st.session_state.ads_shown = 0
            st.session_state.messages_sent = 0
            st.session_state.files_uploaded = 0
    
    @staticmethod
    def track_ad_impression():
        """Increment ad counter"""
        st.session_state.ads_shown += 1
    
    @staticmethod
    def track_message():
        """Increment message counter"""
        st.session_state.messages_sent += 1
    
    @staticmethod
    def track_upload():
        """Increment file upload counter"""
        st.session_state.files_uploaded += 1
    
    @staticmethod
    def get_session_duration():
        """Calculate session duration in seconds"""
        if 'session_start' in st.session_state:
            return (datetime.now() - st.session_state.session_start).total_seconds()
        return 0
    
    @staticmethod
    def get_metrics_summary():
        """Return dictionary of all tracked metrics"""
        return {
            'session_duration': MetricsTracker.get_session_duration(),
            'ads_shown': st.session_state.get('ads_shown', 0),
            'messages_sent': st.session_state.get('messages_sent', 0),
            'files_uploaded': st.session_state.get('files_uploaded', 0)
        }