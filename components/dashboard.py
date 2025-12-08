import streamlit as st
from utils.firebase_ops import FirebaseOps
from utils.metrics import MetricsTracker
from utils.qdrant_ops import QdrantRAG
from config.firebase_config import db
from firebase_admin import storage
import io

def render_dashboard():
    """Render cute main dashboard with subject selection"""
    
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
            subjects = [doc.to_dict() for doc in subjects_docs]
    except:
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
        </style>
    """, unsafe_allow_html=True)
    
    st.title("✨ Your Study Space ✨")
    st.write("Pick a subject and start your learning journey~")
    
    # Get real resource counts from Firebase
    try:
        all_files = list(db.collection('uploaded_files').stream())
        verified_files = [doc for doc in all_files if doc.to_dict().get('verified', False)]
        
        # Count resources per subject
        subject_counts = {}
        for doc in verified_files:
            subject_name = doc.to_dict().get('subject', '')
            subject_counts[subject_name] = subject_counts.get(subject_name, 0) + 1
        
        # Update subjects with real counts
        for subject in subjects:
            matching_count = 0
            for stored_subject, count in subject_counts.items():
                if subject['name'] in stored_subject or subject['category'] in stored_subject:
                    matching_count += count
            subject['resources'] = matching_count
    except Exception as e:
        st.error(f"Error loading resource counts: {e}")
        for subject in subjects:
            subject['resources'] = 0
    
    cols = st.columns(3)
    for idx, subject in enumerate(subjects):
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="subject-card" style="background: linear-gradient(135deg, white 0%, {subject.get('color', '#dbeafe')} 100%);">
                    <div class="subject-icon">{subject.get('icon', '📚')}</div>
                    <h3 class="subject-name">{subject['name']}</h3>
                    <span class="subject-badge">{subject.get('category', 'General')}</span>
                    <p style="color: #6b7280; font-size: 0.95rem; margin-top: 15px;">
                        {subject.get('resources', 0)} resources available
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Open {subject['name']} ✧", key=subject['id'], use_container_width=True, type="primary"):
                st.session_state.selected_subject = subject
                st.rerun()
    
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
                with st.spinner("Uploading files to Firebase Storage and Qdrant..."):
                    user_id = st.session_state.user['id']
                    bucket = storage.bucket()
                    
                    success_count = 0
                    for file in uploaded_files:
                        try:
                            file_bytes = file.getvalue()
                            
                            # Upload to Firebase Storage
                            storage_path = f"uploads/{user_id}/{upload_subject}/{file.name}"
                            blob = bucket.blob(storage_path)
                            blob.upload_from_string(file_bytes, content_type=file.type)
                            
                            # Make file publicly accessible (or use signed URLs later)
                            blob.make_public()
                            download_url = blob.public_url
                            
                            # Save metadata to Firestore
                            result = FirebaseOps.save_uploaded_file(
                                user_id,
                                file.name,
                                file_bytes,
                                upload_subject
                            )
                            
                            if result:
                                doc_id = result[1].id
                                
                                # Update with storage URL
                                db.collection('uploaded_files').document(doc_id).update({
                                    'storage_path': storage_path,
                                    'download_url': download_url
                                })
                                
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
                        st.success(f"✨ Successfully uploaded {success_count}/{len(uploaded_files)} files to Firebase Storage!")
                        st.balloons()
                        st.info("⏳ Your files are pending admin approval. Once verified, they'll be downloadable and searchable by AI!")
                    else:
                        st.error("❌ No files were uploaded successfully. Please try again.")
                        
            except Exception as e:
                st.error(f"Upload error: {str(e)}")
                st.exception(e)