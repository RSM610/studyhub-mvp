import streamlit as st
from utils.firebase_ops import FirebaseOps
from utils.metrics import MetricsTracker
from utils.qdrant_ops import QdrantRAG
from config.firebase_config import db
import base64

def render_dashboard():
    """Render cute main dashboard with subject selection + DOWNLOAD"""
    
    # Get subjects from Firebase (dynamic)
    try:
        subjects_docs = list(db.collection('subjects').stream())
        if len(subjects_docs) == 0:
            # Default subjects if none exist
            subjects = [
                {'id': 'physics_o', 'name': 'Physics', 'category': 'O Levels', 'icon': '⚡', 'color': '#dbeafe'},
                {'id': 'business', 'name': 'Business + Entrepreneurship', 'category': 'University', 'icon': '💼', 'color': '#fef3c7'},
                {'id': 'physics_a', 'name': 'Physics', 'category': 'A Levels', 'icon': '🔬', 'color': '#dcfce7'}
            ]
        else:
            subjects = []
            for doc in subjects_docs:
                data = doc.to_dict()
                # Ensure all required fields exist with defaults
                subject = {
                    'id': data.get('id', doc.id),  # Use doc.id as fallback
                    'name': data.get('name', 'Unknown Subject'),
                    'category': data.get('category', 'General'),
                    'icon': data.get('icon', '📚'),
                    'color': data.get('color', '#dbeafe')
                }
                subjects.append(subject)
    except Exception as e:
        st.error(f"Error loading subjects: {e}")
        # Fallback to default
        subjects = [
            {'id': 'physics_o', 'name': 'Physics', 'category': 'O Levels', 'icon': '⚡', 'color': '#dbeafe'},
            {'id': 'business', 'name': 'Business + Entrepreneurship', 'category': 'University', 'icon': '💼', 'color': '#fef3c7'},
            {'id': 'physics_a', 'name': 'Physics', 'category': 'A Levels', 'icon': '🔬', 'color': '#dcfce7'}
        ]
    
    st.markdown("""
        <style>
        .subject-card {
            background: white;
            padding: 30px;
            border-radius: 25px;
            box-shadow: 0 10px 30px rgba(167, 139, 250, 0.2);
            transition: all 0.3s ease;
            border: 3px solid transparent;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        .subject-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(167, 139, 250, 0.4);
            border-color: #a78bfa;
        }
        .subject-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        .subject-name {
            color: #1f2937;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .subject-badge {
            display: inline-block;
            background: linear-gradient(135deg, #fef3c7 0%, #fce7f3 100%);
            color: #9333ea;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 2px solid #fbcfe8;
        }
        .download-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 10px;
            border: none;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("✨ Your Study Space ✨")
    st.write("Pick a subject and start your learning journey~")
    
    # Get real resource counts from Firebase
    try:
        all_files = list(db.collection('uploaded_files').stream())
        verified_files = [doc for doc in all_files if doc.to_dict().get('verified', False)]
        
        # Count resources per subject - EXACT MATCH ONLY
        subject_counts = {}
        for doc in verified_files:
            subject_name = doc.to_dict().get('subject', '')
            if subject_name:  # Only count if subject is not empty
                subject_counts[subject_name] = subject_counts.get(subject_name, 0) + 1
        
        # Update subjects with real counts - EXACT MATCH
        for subject in subjects:
            # Build the exact subject string as stored in Firebase
            subject_full_name = f"{subject['name']} ({subject.get('category', 'General')})"
            # Get exact match count
            subject['resources'] = subject_counts.get(subject_full_name, 0)
    except Exception as e:
        st.error(f"Error loading resource counts: {e}")
        for subject in subjects:
            subject['resources'] = 0
    
    cols = st.columns(3)
    for idx, subject in enumerate(subjects):
        with cols[idx % 3]:
            # Safely get all values with defaults
            icon = subject.get('icon', '📚')
            name = subject.get('name', 'Unknown')
            category = subject.get('category', 'General')
            color = subject.get('color', '#dbeafe')
            resources = subject.get('resources', 0)
            subject_id = subject.get('id', f'subject_{idx}')
            
            st.markdown(f"""
                <div class="subject-card" style="background: linear-gradient(135deg, white 0%, {color} 100%);">
                    <div class="subject-icon">{icon}</div>
                    <h3 class="subject-name">{name}</h3>
                    <span class="subject-badge">{category}</span>
                    <p style="color: #6b7280; font-size: 0.95rem; margin-top: 15px;">
                        {resources} resources available
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Open {name} ✧", key=subject_id, use_container_width=True, type="primary"):
                st.session_state.selected_subject = subject
                st.rerun()
    
    # Download modal
    if st.session_state.get('download_subject'):
        subject = st.session_state.download_subject
        subject_full_name = f"{subject['name']} ({subject.get('category', 'General')})"
        
        st.markdown("---")
        st.markdown(f"## 📥 Download Resources: {subject['icon']} {subject['name']}")
        
        # Get files for this subject
        try:
            all_files = list(db.collection('uploaded_files').stream())
            subject_files = []
            
            for doc in all_files:
                file_data = doc.to_dict()
                if file_data.get('verified', False):
                    if file_data.get('subject') == subject_full_name:
                        subject_files.append((doc.id, file_data))
        except Exception as e:
            st.error(f"Error loading files: {e}")
            subject_files = []
        
        if len(subject_files) == 0:
            st.info(f"📭 No resources available for download yet. Upload some materials to get started!")
        else:
            st.success(f"✨ Found {len(subject_files)} resources!")
            
            for doc_id, file_data in subject_files:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                        **📄 {file_data.get('file_name', 'Unknown')}**
                        
                        Size: {file_data.get('file_size', 0) / 1024:.1f} KB
                    """)
                
                with col2:
                    st.caption(f"Uploaded: {file_data.get('upload_time', 'N/A')}")
                
                with col3:
                    # Create download button
                    # Note: This creates a placeholder - you need to store actual files
                    # in Firebase Storage or another storage solution
                    download_data = f"File: {file_data.get('file_name', 'Unknown')}\nSubject: {subject_full_name}\nDoc ID: {doc_id}"
                    
                    st.download_button(
                        label="⬇️",
                        data=download_data.encode(),
                        file_name=f"{file_data.get('file_name', 'file.txt')}",
                        mime="text/plain",
                        key=f"dl_{doc_id}",
                        use_container_width=True
                    )
                
                st.markdown("---")
        
        if st.button("← Back to Subjects", key="close_download"):
            st.session_state.download_subject = None
            st.rerun()
        
        st.stop()  # Prevent rendering rest of dashboard
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Upload section
    st.title("🌸 Share Your Knowledge 🌸")
    st.write("Help fellow students by uploading notes and past papers~")
    
    # Subject selection for upload
    upload_subject = st.selectbox(
        "Select subject for upload",
        options=[f"{s['name']} ({s.get('category', 'General')})" for s in subjects],
        key="upload_subject_select"
    )
    
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files and len(uploaded_files) > 0:
        st.info(f"📁 {len(uploaded_files)} file(s) selected and ready to upload")
        
        if st.button("✨ Upload Files", type="primary", use_container_width=True, key="upload_btn"):
            try:
                with st.spinner("Uploading files to Firebase and Qdrant..."):
                    user_id = st.session_state.user['id']
                    
                    success_count = 0
                    for file in uploaded_files:
                        try:
                            file_bytes = file.getvalue()
                            
                            # Save to Firebase
                            result = FirebaseOps.save_uploaded_file(
                                user_id,
                                file.name,
                                file_bytes,
                                upload_subject
                            )
                            
                            if result:
                                doc_id = result[1].id
                                
                                # Upload to Qdrant for RAG
                                with st.spinner(f"Processing {file.name} for AI search..."):
                                    chunks_uploaded = QdrantRAG.upload_document_to_qdrant(
                                        file_name=file.name,
                                        file_content=file_bytes,
                                        subject=upload_subject,
                                        user_id=user_id,
                                        doc_id=doc_id
                                    )
                                    
                                    if chunks_uploaded > 0:
                                        st.success(f"✅ {file.name}: Uploaded {chunks_uploaded} chunks to AI database")
                                
                                success_count += 1
                                MetricsTracker.track_upload()
                                
                        except Exception as file_error:
                            st.error(f"Failed to upload {file.name}: {str(file_error)}")
                    
                    if success_count > 0:
                        st.success(f"✨ Successfully uploaded {success_count}/{len(uploaded_files)} files!")
                        st.balloons()
                        st.info("⏳ Your files are pending admin approval. Once verified, they'll be searchable and downloadable by everyone!")
                    else:
                        st.error("❌ No files were uploaded successfully. Please try again.")
                        
            except Exception as e:
                st.error(f"Upload error: {str(e)}")
                st.exception(e)