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
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⏳ Pending Approval", 
        "✅ Approved", 
        "📊 Statistics", 
        "➕ Manage Subjects",
        "🗑️ Cleanup"
    ])
    
    with tab1:
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
    
    with tab2:
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
    
    with tab3:
        st.subheader("Platform Statistics")
        
        try:
            all_files = list(db.collection('uploaded_files').stream())
            pending_count = sum(1 for f in all_files if not f.to_dict().get('verified', False))
            approved_count = sum(1 for f in all_files if f.to_dict().get('verified', False))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Resources", len(all_files))
            
            with col2:
                st.metric("Pending", pending_count)
            
            with col3:
                st.metric("Approved", approved_count)
        
        except Exception as e:
            st.error(f"Error: {e}")
    
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
                        'id': subject_id,  # CRITICAL: Add the ID field
                        'name': new_subject_name.strip(),
                        'category': new_subject_category.strip() if new_subject_category else 'General',  # Default to 'General' if empty
                        'icon': new_subject_icon.strip() if new_subject_icon else '📚',  # Default icon if empty
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
    
    with tab5:
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