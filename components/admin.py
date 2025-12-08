import streamlit as st
from config.firebase_config import db
from datetime import datetime
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

def render_admin_panel():
    """Render admin panel for approving resources"""
    
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
    st.write("Resource Approval Center")
    st.write(f"Logged in as: **{st.session_state.get('admin_email', 'admin')}**")
    
    tab1, tab2, tab3, tab4 = st.tabs(["⏳ Pending Approval", "✅ Approved", "📊 Statistics", "➕ Manage Subjects"])
    
    with tab1:
        st.subheader("Pending Resources")
        
        try:
            # Get ALL files first
            st.info("🔍 Fetching files from Firebase...")
            all_files = list(db.collection('uploaded_files').stream())
            
            st.success(f"✅ Found {len(all_files)} total files in database")
            
            # Filter for pending files
            pending_files = []
            for doc in all_files:
                file_data = doc.to_dict()
                verified = file_data.get('verified', False)
                st.write(f"Debug: File {file_data.get('file_name', 'Unknown')} - Verified: {verified}")
                if not verified:
                    pending_files.append(doc)
            
            st.write(f"📋 Pending files count: {len(pending_files)}")
            
            if len(pending_files) == 0:
                st.warning("🎉 No pending resources! All caught up~")
                st.info("💡 Tip: Try uploading a file from the dashboard to test the approval system")
            else:
                st.success(f"Found {len(pending_files)} pending resources")
                
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
                            - **Uploaded by:** {file_data.get('user_id', 'Unknown')[:12]}...
                            - **Size:** {file_data.get('file_size', 0) / 1024:.2f} KB
                            - **Date:** {time_str}
                            
                            ⏳ **Status:** Pending Approval
                        """)
                    
                    with col2:
                        st.write("")  # Spacing
                        if st.button("✅ Approve", key=f"approve_{doc.id}", use_container_width=True, type="primary"):
                            try:
                                db.collection('uploaded_files').document(doc.id).update({
                                    'verified': True,
                                    'approved_by': st.session_state.get('admin_email', 'admin'),
                                    'approved_at': datetime.now()
                                })
                                st.success("✨ Resource approved!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error approving: {e}")
                        
                        if st.button("❌ Reject", key=f"reject_{doc.id}", use_container_width=True):
                            try:
                                db.collection('uploaded_files').document(doc.id).delete()
                                st.warning("Resource rejected and removed")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error rejecting: {e}")
        
        except Exception as e:
            st.error(f"Error loading resources: {e}")
            st.exception(e)
    
    with tab2:
        st.subheader("Approved Resources")
        
        try:
            # Get approved files
            all_files = list(db.collection('uploaded_files').stream())
            approved_files = [doc for doc in all_files if doc.to_dict().get('verified', False)]
            
            if len(approved_files) == 0:
                st.info("No approved resources yet")
            else:
                st.success(f"Found {len(approved_files)} approved resources")
                
                for doc in approved_files[:20]:  # Show first 20
                    file_data = doc.to_dict()
                    
                    st.markdown("---")
                    st.markdown(f"""
                        **📄 {file_data.get('file_name', 'Unknown')}**
                        
                        - **Subject:** {file_data.get('subject', 'N/A')}
                        - **Approved by:** {file_data.get('approved_by', 'Unknown')}
                        
                        ✅ **Status:** Approved
                    """)
        
        except Exception as e:
            st.error(f"Error loading resources: {e}")
            st.exception(e)
    
    with tab3:
        st.subheader("Platform Statistics")
        
        try:
            all_files = list(db.collection('uploaded_files').stream())
            pending_count = sum(1 for f in all_files if not f.to_dict().get('verified', False))
            approved_count = sum(1 for f in all_files if f.to_dict().get('verified', False))
            
            all_sessions = list(db.collection('sessions').stream())
            unique_users = len(set(s.to_dict().get('user_id', '') for s in all_sessions))
            
            all_interactions = list(db.collection('interactions').stream())
            total_messages = sum(1 for i in all_interactions if i.to_dict().get('event_type') == 'message_sent')
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Resources", len(all_files), delta=f"+{pending_count} pending")
            
            with col2:
                st.metric("Approved", approved_count)
            
            with col3:
                st.metric("Total Users", unique_users)
            
            with col4:
                st.metric("Messages Sent", total_messages)
            
            st.markdown("---")
            
            st.subheader("Resources by Subject")
            subject_counts = {}
            for doc in all_files:
                subject = doc.to_dict().get('subject', 'Unknown')
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
            
            if subject_counts:
                for subject, count in subject_counts.items():
                    st.write(f"**{subject}:** {count} resources")
            else:
                st.info("No resources uploaded yet")
        
        except Exception as e:
            st.error(f"Error loading statistics: {e}")
            st.exception(e)
    
    with tab4:
        st.subheader("📚 Manage Subjects")
        
        # Add new subject
        st.markdown("### ➕ Add New Subject")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_subject_name = st.text_input("Subject Name", placeholder="e.g., Chemistry", key="new_subj_name")
            new_subject_category = st.text_input("Category", placeholder="e.g., O Levels, A Levels, University", key="new_subj_cat")
        
        with col2:
            new_subject_icon = st.text_input("Icon (emoji)", placeholder="e.g., ⚗️", key="new_subj_icon")
            new_subject_color = st.color_picker("Card Color", "#dbeafe", key="new_subj_color")
        
        if st.button("➕ Add Subject", type="primary", use_container_width=True):
            if new_subject_name and new_subject_category and new_subject_icon:
                try:
                    subject_id = new_subject_name.lower().replace(' ', '_')
                    db.collection('subjects').document(subject_id).set({
                        'id': subject_id,
                        'name': new_subject_name,
                        'category': new_subject_category,
                        'icon': new_subject_icon,
                        'color': new_subject_color,
                        'created_at': datetime.now(),
                        'created_by': st.session_state.get('admin_email', 'admin')
                    })
                    st.success(f"✨ Added {new_subject_name}!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding subject: {e}")
            else:
                st.error("Please fill in all fields")
        
        st.markdown("---")
        st.markdown("### 📋 Existing Subjects")
        
        try:
            subjects = list(db.collection('subjects').stream())
            
            if len(subjects) == 0:
                st.info("No subjects added yet. Add some above!")
            else:
                for doc in subjects:
                    subject_data = doc.to_dict()
                    
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"""
                            {subject_data.get('icon', '📚')} **{subject_data.get('name', 'Unknown')}** 
                            ({subject_data.get('category', 'General')})
                        """)
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_subj_{doc.id}"):
                            db.collection('subjects').document(doc.id).delete()
                            st.success("Deleted!")
                            time.sleep(1)
                            st.rerun()
                    
                    st.divider()
        
        except Exception as e:
            st.error(f"Error loading subjects: {e}")
    
    st.markdown("---")
    
    # Logout button
    if st.button("🚪 Logout from Admin", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.admin_email = None
        st.success("Logged out from admin panel")
        time.sleep(1)
        st.rerun()