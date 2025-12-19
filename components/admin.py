import streamlit as st
from config.firebase_config import db
from datetime import datetime, timedelta
import hashlib
import time

# ADMIN CREDENTIALS
ADMIN_EMAIL = 'u2023610@giki.edu.pk'
ADMIN_PASSWORD = 'meowmeow123'

def hash_password(password):
    """Hash password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_admin(email, password):
    """Verify admin credentials - simple check"""
    return email == ADMIN_EMAIL and password == ADMIN_PASSWORD

def get_analytics_data():
    """Fetch all analytics data from Firebase"""
    try:
        analytics = {
            'total_resources': 0,
            'approved_resources': 0,
            'pending_resources': 0,
            'total_ad_impressions': 0,
            'total_users': 0,
            'returning_users': 0,
            'total_sessions': 0,
            'avg_session_duration': 0,
            'sessions_per_user': {},
            'resources_by_subject': {},
            'recent_uploads': [],
            'top_subjects': [],
            'user_activity': [],
            'total_messages': 0,
            'total_uploads': 0
        }
        
        # 1. Get total resources
        all_files = list(db.collection('uploaded_files').stream())
        analytics['total_resources'] = len(all_files)
        analytics['approved_resources'] = sum(1 for f in all_files if f.to_dict().get('verified', False))
        analytics['pending_resources'] = analytics['total_resources'] - analytics['approved_resources']
        
        # Resources by subject
        for doc in all_files:
            file_data = doc.to_dict()
            if file_data.get('verified', False):
                subject = file_data.get('subject', 'Unknown')
                analytics['resources_by_subject'][subject] = analytics['resources_by_subject'].get(subject, 0) + 1
        
        # Top 5 subjects
        sorted_subjects = sorted(analytics['resources_by_subject'].items(), key=lambda x: x[1], reverse=True)
        analytics['top_subjects'] = sorted_subjects[:5]
        
        # Recent uploads (last 10)
        sorted_files = sorted(all_files, key=lambda x: x.to_dict().get('upload_time', datetime.min), reverse=True)
        analytics['recent_uploads'] = [
            {
                'file_name': f.to_dict().get('file_name', 'Unknown'),
                'subject': f.to_dict().get('subject', 'Unknown'),
                'upload_time': f.to_dict().get('upload_time'),
                'verified': f.to_dict().get('verified', False)
            }
            for f in sorted_files[:10]
        ]
        
        # 2. Get all interactions data
        interactions = list(db.collection('interactions').stream())
        
        # Count ad impressions
        ad_impressions = [i for i in interactions if i.to_dict().get('event_type') == 'ad_shown']
        analytics['total_ad_impressions'] = len(ad_impressions)
        
        # Count messages sent
        messages_sent = [i for i in interactions if i.to_dict().get('event_type') == 'message_sent']
        analytics['total_messages'] = len(messages_sent)
        
        # Count file uploads from interactions
        uploads = [i for i in interactions if i.to_dict().get('event_type') == 'file_upload']
        analytics['total_uploads'] = len(uploads)
        
        # 3. Get user data
        all_users = list(db.collection('users').stream())
        analytics['total_users'] = len(all_users)
        
        # 4. Get session data
        all_sessions = list(db.collection('sessions').stream())
        analytics['total_sessions'] = len(all_sessions)
        
        # Calculate returning users (users with more than 1 session)
        user_session_counts = {}
        total_duration = 0
        valid_durations = 0
        
        for session in all_sessions:
            session_data = session.to_dict()
            user_id = session_data.get('user_id', 'unknown')
            
            # Count sessions per user
            user_session_counts[user_id] = user_session_counts.get(user_id, 0) + 1
            
            # Calculate average session duration
            duration = session_data.get('duration_seconds', 0)
            if duration > 0:
                total_duration += duration
                valid_durations += 1
        
        analytics['returning_users'] = sum(1 for count in user_session_counts.values() if count > 1)
        analytics['sessions_per_user'] = user_session_counts
        
        if valid_durations > 0:
            analytics['avg_session_duration'] = total_duration / valid_durations
        
        # 5. User activity (top 10 most active users)
        sorted_users = sorted(user_session_counts.items(), key=lambda x: x[1], reverse=True)
        analytics['user_activity'] = sorted_users[:10]
        
        return analytics
        
    except Exception as e:
        st.error(f"Error fetching analytics: {e}")
        return None

def render_admin_login():
    """Render admin login form"""
    st.title("🛡️ Admin Access")
    st.write("Enter admin credentials")
    
    admin_email = st.text_input(
        "Admin Email",
        key="admin_email_input",
        value="u2023610@giki.edu.pk"
    )
    admin_password = st.text_input(
        "Admin Password",
        type="password",
        key="admin_password_input"
    )
    
    if st.button("Login as Admin", type="primary", use_container_width=True):
        if verify_admin(admin_email, admin_password):
            st.session_state.admin_authenticated = True
            st.session_state.admin_email = admin_email
            st.success("✨ Admin access granted!")
            st.rerun()
        else:
            st.error("❌ Invalid admin credentials")
    
    st.info(f"💡 Email: {ADMIN_EMAIL} / Password: meowmeow123")

def cleanup_all_documents():
    """Delete ALL documents - DANGER ZONE"""
    st.error("⚠️ DANGER ZONE: This will DELETE ALL uploaded files permanently!")
    
    confirm = st.text_input(
        "Type 'DELETE ALL' to confirm:",
        key="confirm_delete_all"
    )
    
    if confirm == "DELETE ALL":
        if st.button("🗑️ PERMANENTLY DELETE ALL DOCUMENTS", type="primary"):
            try:
                all_files = list(db.collection('uploaded_files').stream())
                deleted_count = 0
                
                progress_bar = st.progress(0)
                
                for idx, doc in enumerate(all_files):
                    db.collection('uploaded_files').document(doc.id).delete()
                    deleted_count += 1
                    progress_bar.progress((idx + 1) / len(all_files))
                
                st.success(f"✅ Deleted {deleted_count} documents!")
                st.balloons()
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")

def render_admin_panel():
    """Render admin panel for approving resources with comprehensive analytics"""
    
    # Check if user is logged in at all
    if 'user' not in st.session_state:
        st.error("❌ Please login first before accessing admin panel")
        return
    
    # Check admin authentication
    if not st.session_state.get('admin_authenticated', False):
        # Check if user email matches admin email
        if st.session_state.user.get('email') == ADMIN_EMAIL:
            render_admin_login()
        else:
            st.error("❌ You don't have admin privileges")
            st.info(f"Admin email is: {ADMIN_EMAIL}")
        return
    
    st.title("🛡️ Admin Panel")
    st.write("Resource Approval & Analytics Center")
    st.write(f"Logged in as: **{st.session_state.get('admin_email', 'admin')}**")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Analytics",
        "⏳ Pending Approval", 
        "✅ Approved", 
        "➕ Manage Subjects",
        "👥 User Management",
        "🗑️ Cleanup"
    ])
    
    # ==================== TAB 1: ANALYTICS ====================
    with tab1:
        st.header("📊 Platform Analytics Dashboard")
        
        with st.spinner("🔄 Loading comprehensive analytics..."):
            analytics = get_analytics_data()
        
        if analytics:
            # ===== MAIN METRICS ROW =====
            st.markdown("### 📈 Key Performance Indicators")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                         padding: 25px; border-radius: 15px; text-align: center;
                         border: 2px solid #93c5fd; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);">
                        <div style="font-size: 2.5rem; margin-bottom: 10px;">📚</div>
                        <h2 style="color: #1e40af; margin: 0; font-size: 2.2rem;">{}</h2>
                        <p style="color: #3b82f6; margin: 5px 0 0 0; font-weight: 600;">Total Resources</p>
                    </div>
                """.format(analytics['total_resources']), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                         padding: 25px; border-radius: 15px; text-align: center;
                         border: 2px solid #fbbf24; box-shadow: 0 4px 15px rgba(251, 191, 36, 0.2);">
                        <div style="font-size: 2.5rem; margin-bottom: 10px;">👁️</div>
                        <h2 style="color: #b45309; margin: 0; font-size: 2.2rem;">{}</h2>
                        <p style="color: #d97706; margin: 5px 0 0 0; font-weight: 600;">Ad Impressions</p>
                    </div>
                """.format(analytics['total_ad_impressions']), unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
                         padding: 25px; border-radius: 15px; text-align: center;
                         border: 2px solid #86efac; box-shadow: 0 4px 15px rgba(134, 239, 172, 0.2);">
                        <div style="font-size: 2.5rem; margin-bottom: 10px;">👥</div>
                        <h2 style="color: #15803d; margin: 0; font-size: 2.2rem;">{}</h2>
                        <p style="color: #16a34a; margin: 5px 0 0 0; font-weight: 600;">Total Users</p>
                    </div>
                """.format(analytics['total_users']), unsafe_allow_html=True)
            
            with col4:
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
                         padding: 25px; border-radius: 15px; text-align: center;
                         border: 2px solid #f9a8d4; box-shadow: 0 4px 15px rgba(249, 168, 212, 0.2);">
                        <div style="font-size: 2.5rem; margin-bottom: 10px;">🔄</div>
                        <h2 style="color: #9f1239; margin: 0; font-size: 2.2rem;">{}</h2>
                        <p style="color: #db2777; margin: 5px 0 0 0; font-weight: 600;">Returning Users</p>
                    </div>
                """.format(analytics['returning_users']), unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ===== SECONDARY METRICS ROW =====
            st.markdown("### 📊 Additional Metrics")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("✅ Approved", analytics['approved_resources'], 
                         delta=f"{(analytics['approved_resources']/max(analytics['total_resources'],1)*100):.0f}%")
            
            with col2:
                st.metric("⏳ Pending", analytics['pending_resources'],
                         delta=f"-{analytics['pending_resources']}" if analytics['pending_resources'] > 0 else "0")
            
            with col3:
                st.metric("🔗 Sessions", analytics['total_sessions'])
            
            with col4:
                avg_duration_min = int(analytics['avg_session_duration'] / 60)
                st.metric("⏱️ Avg Duration", f"{avg_duration_min}m")
            
            with col5:
                st.metric("💬 Messages", analytics['total_messages'])
            
            st.markdown("---")
            
            # ===== USER ENGAGEMENT STATS =====
            st.markdown("### 🎯 User Engagement")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Calculate retention rate
                retention_rate = (analytics['returning_users'] / max(analytics['total_users'], 1)) * 100
                
                st.markdown(f"""
                    <div style="background: white; padding: 25px; border-radius: 15px;
                         border: 2px solid #e9d5ff; box-shadow: 0 4px 15px rgba(167, 139, 250, 0.2);">
                        <h4 style="color: #7c3aed; margin: 0 0 15px 0;">📈 User Retention</h4>
                        <div style="background: #faf5ff; height: 30px; border-radius: 15px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #a78bfa 0%, #ec4899 100%); 
                                 height: 100%; width: {retention_rate}%; 
                                 display: flex; align-items: center; justify-content: center;
                                 color: white; font-weight: 700; font-size: 0.9rem;">
                                {retention_rate:.1f}%
                            </div>
                        </div>
                        <p style="color: #9333ea; margin: 10px 0 0 0; font-size: 0.9rem;">
                            {analytics['returning_users']} of {analytics['total_users']} users returned
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Calculate average sessions per user
                avg_sessions = analytics['total_sessions'] / max(analytics['total_users'], 1)
                
                st.markdown(f"""
                    <div style="background: white; padding: 25px; border-radius: 15px;
                         border: 2px solid #fce7f3; box-shadow: 0 4px 15px rgba(251, 207, 232, 0.2);">
                        <h4 style="color: #db2777; margin: 0 0 15px 0;">🔄 Avg Sessions per User</h4>
                        <div style="text-align: center;">
                            <h2 style="color: #ec4899; font-size: 3rem; margin: 10px 0;">{avg_sessions:.1f}</h2>
                            <p style="color: #f472b6; margin: 0; font-size: 0.9rem;">sessions per user</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ===== TOP SUBJECTS =====
            st.markdown("### 🏆 Top 5 Most Popular Subjects")
            
            if analytics['top_subjects']:
                for idx, (subject, count) in enumerate(analytics['top_subjects'], 1):
                    # Calculate percentage of total
                    percentage = (count / max(analytics['total_resources'], 1)) * 100
                    
                    col1, col2, col3 = st.columns([1, 6, 1])
                    
                    with col1:
                        # Medal emojis for top 3
                        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
                        st.markdown(f"""
                            <div style="text-align: center; font-size: 2rem; padding: 10px;">
                                {medal}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                            <div style="background: white; padding: 15px; border-radius: 10px;
                                 border: 2px solid #e9d5ff;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="color: #7c3aed; font-weight: 700; font-size: 1.1rem;">
                                        {subject}
                                    </span>
                                    <span style="color: #9333ea; font-weight: 600;">
                                        {percentage:.1f}%
                                    </span>
                                </div>
                                <div style="background: #faf5ff; height: 12px; border-radius: 10px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #a78bfa 0%, #ec4899 100%); 
                                         height: 100%; width: {percentage}%; transition: width 0.3s ease;"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
                                 color: white; padding: 15px; border-radius: 10px;
                                 text-align: center; font-weight: 700; font-size: 1.3rem;">
                                {count}
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("📭 No subjects with resources yet")
            
            st.markdown("---")
            
            # ===== USER ACTIVITY LEADERBOARD =====
            st.markdown("### ⭐ Top 10 Most Active Users")
            
            if analytics['user_activity']:
                for idx, (user_id, session_count) in enumerate(analytics['user_activity'], 1):
                    col1, col2, col3 = st.columns([1, 6, 1])
                    
                    with col1:
                        st.markdown(f"""
                            <div style="text-align: center; font-size: 1.5rem; padding: 5px;
                                 color: #7c3aed; font-weight: 700;">
                                #{idx}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Mask user ID for privacy
                        masked_id = f"{user_id[:8]}...{user_id[-4:]}" if len(user_id) > 12 else user_id
                        
                        # Get user email from users collection
                        try:
                            user_doc = db.collection('users').where(field_path='user_id', op_string='==', value=user_id).limit(1).stream()
                            user_list = list(user_doc)
                            user_email = user_list[0].to_dict().get('email', 'Unknown') if user_list else 'Unknown'
                            display_name = user_email.split('@')[0] if user_email != 'Unknown' else masked_id
                        except:
                            display_name = masked_id
                        
                        st.markdown(f"""
                            <div style="background: white; padding: 12px 20px; border-radius: 10px;
                                 border: 2px solid #fce7f3; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="color: #9333ea; font-weight: 600; font-size: 1.05rem;">
                                        👤 {display_name}
                                    </span>
                                    <br>
                                    <span style="color: #c084fc; font-size: 0.85rem;">
                                        User ID: {masked_id}
                                    </span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
                                 color: white; padding: 12px; border-radius: 10px;
                                 text-align: center; font-weight: 700; font-size: 1.1rem;">
                                {session_count} 🔗
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("📊 No user activity data yet")
            
            st.markdown("---")
            
            # ===== RECENT UPLOADS TIMELINE =====
            st.markdown("### 📋 Recent Uploads Timeline")
            
            if analytics['recent_uploads']:
                for upload in analytics['recent_uploads']:
                    status_color = "#10b981" if upload['verified'] else "#f59e0b"
                    status_icon = "✅" if upload['verified'] else "⏳"
                    status_text = "Approved" if upload['verified'] else "Pending"
                    
                    upload_time = upload['upload_time']
                    time_str = upload_time.strftime('%Y-%m-%d %H:%M') if hasattr(upload_time, 'strftime') else 'N/A'
                    
                    # Calculate time ago
                    if hasattr(upload_time, 'strftime'):
                        time_diff = datetime.now() - upload_time
                        if time_diff.days > 0:
                            time_ago = f"{time_diff.days}d ago"
                        elif time_diff.seconds // 3600 > 0:
                            time_ago = f"{time_diff.seconds // 3600}h ago"
                        else:
                            time_ago = f"{time_diff.seconds // 60}m ago"
                    else:
                        time_ago = "Unknown"
                    
                    st.markdown(f"""
                        <div style="background: white; padding: 18px; border-radius: 12px;
                             margin: 12px 0; border-left: 5px solid {status_color};
                             box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="flex: 1;">
                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 1.5rem; margin-right: 12px;">{status_icon}</span>
                                        <span style="color: #1f2937; font-weight: 600; font-size: 1.05rem;">{upload['file_name']}</span>
                                    </div>
                                    <div style="margin-left: 45px;">
                                        <span style="color: #7c3aed; font-size: 0.95rem; margin-right: 15px;">📚 {upload['subject']}</span>
                                        <span style="background: {status_color}20; color: {status_color}; 
                                             padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;">
                                            {status_text}
                                        </span>
                                    </div>
                                </div>
                                <div style="text-align: right; min-width: 120px;">
                                    <div style="color: #6b7280; font-size: 0.85rem;">{time_str}</div>
                                    <div style="color: #9ca3af; font-size: 0.8rem; margin-top: 2px;">{time_ago}</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📭 No recent uploads")
            
            st.markdown("---")
            
            # ===== ALL RESOURCES BY SUBJECT =====
            with st.expander("📚 View All Resources by Subject", expanded=False):
                if analytics['resources_by_subject']:
                    for subject, count in sorted(analytics['resources_by_subject'].items()):
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.write(f"📖 {subject}")
                        with col2:
                            st.markdown(f"""
                                <div style="background: #e9d5ff; color: #7c3aed; padding: 5px 15px;
                                     border-radius: 15px; text-align: center; font-weight: 700;">
                                    {count}
                                </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("No resources yet")
            
            # ===== EXPORT ANALYTICS REPORT =====
            st.markdown("---")
            st.markdown("### 📥 Export Data")
            
            if st.button("📊 Download Full Analytics Report", type="primary", use_container_width=True):
                report = f"""
╔════════════════════════════════════════════════════════════╗
║          STUDYHUB ANALYTICS REPORT                         ║
║          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
╚════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════
                    KEY PERFORMANCE INDICATORS
═══════════════════════════════════════════════════════════════

📚 Total Resources:          {analytics['total_resources']}
   ✅ Approved:              {analytics['approved_resources']}
   ⏳ Pending:               {analytics['pending_resources']}

👥 User Metrics:
   Total Users:              {analytics['total_users']}
   Returning Users:          {analytics['returning_users']}
   Retention Rate:           {(analytics['returning_users']/max(analytics['total_users'],1)*100):.1f}%

🔗 Session Data:
   Total Sessions:           {analytics['total_sessions']}
   Avg Session Duration:     {int(analytics['avg_session_duration'] / 60)} minutes
   Avg Sessions/User:        {analytics['total_sessions']/max(analytics['total_users'],1):.1f}

💬 Engagement:
   Ad Impressions:           {analytics['total_ad_impressions']}
   Messages Sent:            {analytics['total_messages']}
   Total Uploads:            {analytics['total_resources']}

═══════════════════════════════════════════════════════════════
                    TOP 5 SUBJECTS
═══════════════════════════════════════════════════════════════
"""
                for idx, (subject, count) in enumerate(analytics['top_subjects'], 1):
                    percentage = (count / max(analytics['total_resources'], 1)) * 100
                    report += f"{idx}. {subject}\n   Resources: {count} ({percentage:.1f}%)\n\n"
                
                report += """
═══════════════════════════════════════════════════════════════
                    TOP 10 ACTIVE USERS
═══════════════════════════════════════════════════════════════
"""
                for idx, (user_id, sessions) in enumerate(analytics['user_activity'], 1):
                    masked = f"{user_id[:8]}...{user_id[-4:]}"
                    report += f"{idx}. User {masked}: {sessions} sessions\n"
                
                report += """

═══════════════════════════════════════════════════════════════
                ALL RESOURCES BY SUBJECT
═══════════════════════════════════════════════════════════════
"""
                for subject, count in sorted(analytics['resources_by_subject'].items()):
                    report += f"{subject}: {count}\n"
                
                report += f"""

═══════════════════════════════════════════════════════════════
Report End - StudyHub Analytics System
═══════════════════════════════════════════════════════════════
"""
                
                st.download_button(
                    label="💾 Download Report as TXT",
                    data=report.encode('utf-8'),
                    file_name=f"studyhub_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # ==================== TAB 2: PENDING APPROVAL ====================
    with tab2:
        st.subheader("Pending Resources")
        
        try:
            # Get ALL files first
            all_files = list(db.collection('uploaded_files').stream())
            
            # Filter for pending files
            pending_files = [doc for doc in all_files if not doc.to_dict().get('verified', False)]
            
            if len(pending_files) == 0:
                st.success("🎉 No pending resources! All caught up~")
            else:
                st.info(f"Found {len(pending_files)} pending resources")
                
                for doc in pending_files:
                    file_data = doc.to_dict()
                    
                    st.markdown("---")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        upload_time = file_data.get('upload_time')
                        time_str = upload_time.strftime('%Y-%m-%d %H:%M') if hasattr(upload_time, 'strftime') else 'N/A'
                        
                        st.markdown(f"""
                            **📄 {file_data.get('file_name', 'Unknown')}**
                            
                            - **Subject:** {file_data.get('subject', 'N/A')}
                            - **Size:** {file_data.get('file_size', 0) / 1024:.2f} KB
                            - **Date:** {time_str}
                        """)
                    
                    with col2:
                        if st.button("✅", key=f"approve_{doc.id}", use_container_width=True):
                            db.collection('uploaded_files').document(doc.id).update({
                                'verified': True,
                                'approved_at': datetime.now()
                            })
                            st.success("Approved!")
                            time.sleep(1)
                            st.rerun()
                        
                        if st.button("❌", key=f"reject_{doc.id}", use_container_width=True):
                            db.collection('uploaded_files').document(doc.id).delete()
                            st.warning("Deleted!")
                            time.sleep(1)
                            st.rerun()
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    # ==================== TAB 3: APPROVED ====================
    with tab3:
        st.subheader("Approved Resources")
        
        try:
            all_files = list(db.collection('uploaded_files').stream())
            approved_files = [doc for doc in all_files if doc.to_dict().get('verified', False)]
            
            if len(approved_files) == 0:
                st.info("No approved resources yet")
            else:
                st.success(f"Found {len(approved_files)} approved resources")
                
                for doc in approved_files[:20]:
                    file_data = doc.to_dict()
                    st.markdown(f"📄 **{file_data.get('file_name', 'Unknown')}** - {file_data.get('subject', 'N/A')}")
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    # ==================== TAB 4: MANAGE SUBJECTS ====================
    with tab4:
        st.subheader("📚 Manage Subjects")
        
        # Show existing subjects first
        st.markdown("### Current Subjects")
        try:
            existing_subjects = list(db.collection('subjects').stream())
            if existing_subjects:
                for doc in existing_subjects:
                    data = doc.to_dict()
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"{data.get('icon', '📚')} **{data.get('name', 'Unknown')}** - {data.get('category', 'N/A')}")
                    with col2:
                        if st.button("🗑️", key=f"del_subj_{doc.id}"):
                            db.collection('subjects').document(doc.id).delete()
                            st.success(f"Deleted {data.get('name', 'subject')}!")
                            time.sleep(1)
                            st.rerun()
            else:
                st.info("No subjects created yet")
        except Exception as e:
            st.error(f"Error loading subjects: {e}")
        
        st.markdown("---")
        st.markdown("### Add New Subject")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_subject_name = st.text_input("Subject Name", placeholder="e.g., Chemistry", key="new_subj_name")
            new_subject_category = st.text_input("Category", placeholder="e.g., O Levels", key="new_subj_cat")
        
        with col2:
            new_subject_icon = st.text_input("Icon", placeholder="e.g., ⚗️", key="new_subj_icon")
            new_subject_color = st.color_picker("Color", "#dbeafe", key="new_subj_color")
        
        if st.button("➕ Add Subject", type="primary", key="add_subject_btn"):
            if new_subject_name:
                # Generate a unique ID for the subject
                subject_id = new_subject_name.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '').replace(',', '')
                
                # Create the subject with ALL required fields
                try:
                    db.collection('subjects').document(subject_id).set({
                        'id': subject_id,
                        'name': new_subject_name.strip(),
                        'category': new_subject_category.strip() if new_subject_category else 'General',
                        'icon': new_subject_icon.strip() if new_subject_icon else '📚',
                        'color': new_subject_color if new_subject_color else '#dbeafe',
                        'created_at': datetime.now()
                    })
                    st.success(f"✨ Added {new_subject_name}!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding subject: {e}")
            else:
                st.error("Please enter a subject name!")
    
    # ==================== TAB 5: USER MANAGEMENT ====================
    with tab5:
        st.subheader("👥 User Management")
        
        try:
            all_users = list(db.collection('users').stream())
            
            st.info(f"Total Users: {len(all_users)}")
            
            for user_doc in all_users[:20]:
                user_data = user_doc.to_dict()
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                        **📧 {user_data.get('email', 'Unknown')}**
                        
                        User ID: `{user_data.get('user_id', 'Unknown')[:16]}...`
                        
                        Created: {user_data.get('created_at', 'N/A')}
                    """)
                
                with col2:
                    if st.button("🗑️", key=f"delete_user_{user_doc.id}"):
                        db.collection('users').document(user_doc.id).delete()
                        st.warning("User deleted!")
                        time.sleep(1)
                        st.rerun()
                
                st.markdown("---")
            
            if len(all_users) > 20:
                st.info(f"Showing 20 of {len(all_users)} users")
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    # ==================== TAB 6: CLEANUP ====================
    with tab6:
        st.subheader("🗑️ Database Cleanup")
        st.write("Remove orphaned documents without RAG data")
        
        cleanup_all_documents()
        
        st.markdown("---")
        
        st.subheader("📋 Current Documents")
        try:
            all_files = list(db.collection('uploaded_files').stream())
            
            if len(all_files) == 0:
                st.success("✅ Database is clean!")
            else:
                st.warning(f"{len(all_files)} documents in database")
                
                for doc in all_files[:10]:
                    file_data = doc.to_dict()
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.write(f"📄 {file_data.get('file_name', 'Unknown')}")
                    
                    with col2:
                        if st.button("🗑️", key=f"del_{doc.id}"):
                            db.collection('uploaded_files').document(doc.id).delete()
                            st.rerun()
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    
    if st.button("🚪 Logout from Admin", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()