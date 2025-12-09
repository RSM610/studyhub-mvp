import streamlit as st
from utils.firebase_ops import FirebaseOps
from utils.metrics import MetricsTracker
from utils.qdrant_ops import QdrantRAG
from config.firebase_config import db
from firebase_admin import storage

def render_chat():
    """Render AI chat interface with REAL RAG functionality and downloads - USER ISOLATED"""
    subject = st.session_state.selected_subject
    
    # USER-SPECIFIC chat key - prevents cross-user chat leakage
    user_id = st.session_state.user['id']
    subject_key = f"{user_id}_{subject['name']}_{subject.get('category', 'General')}".replace(' ', '_')
    
    # Initialize USER-SPECIFIC chat history
    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}
    
    if subject_key not in st.session_state.chat_histories:
        st.session_state.chat_histories[subject_key] = []
    
    # Use USER-SPECIFIC messages
    messages = st.session_state.chat_histories[subject_key]
    
    st.markdown("""
        <style>
        .user-message {
            background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 20px 20px 5px 20px;
            margin: 10px 0;
            margin-left: auto;
            max-width: 70%;
            box-shadow: 0 4px 10px rgba(167, 139, 250, 0.3);
            word-wrap: break-word;
        }
        .ai-message {
            background: linear-gradient(135deg, #fef3c7 0%, #fce7f3 100%);
            color: #7c3aed;
            padding: 15px 20px;
            border-radius: 20px 20px 20px 5px;
            margin: 10px 0;
            margin-right: auto;
            max-width: 70%;
            border: 2px solid #fbcfe8;
            box-shadow: 0 4px 10px rgba(236, 72, 153, 0.2);
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .download-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 10px;
            text-decoration: none;
            display: inline-block;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        if st.button("← Back", key="back_btn", use_container_width=True):
            st.session_state.selected_subject = None
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear", key="clear_chat_btn", use_container_width=True):
            # FIXED: Actually clear the chat
            st.session_state.chat_histories[subject_key] = []
            st.success("Chat cleared!")
            # Force immediate rerun
            import time
            time.sleep(0.5)
            st.rerun()
    
    st.title(f"{subject['icon']} {subject['name']}")
    st.write(f"**{subject.get('category', 'General')}**")
    
    st.markdown("---")
    
    # Get subject files
    subject_full_name = f"{subject['name']} ({subject.get('category', 'General')})"
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
    
    # Quick Action Buttons
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📚 List Resources", use_container_width=True, key="btn_list"):
            if len(subject_files) == 0:
                response = f"📭 No resources uploaded yet for {subject['name']}."
            else:
                response = f"📚 **{len(subject_files)} Resources Available:**\n\n"
                for idx, (doc_id, file_data) in enumerate(subject_files, 1):
                    response += f"{idx}. 📄 {file_data.get('file_name', 'Unknown')}\n"
            
            st.session_state.chat_histories[subject_key].append({'role': 'assistant', 'content': response})
            st.rerun()
    
    with col2:
        if st.button("📝 Summaries", use_container_width=True, key="btn_summary"):
            if len(subject_files) == 0:
                response = "📭 No files to summarize yet."
            else:
                with st.spinner("Generating summaries..."):
                    response = f"📝 **Document Summaries:**\n\n"
                    for idx, (doc_id, file_data) in enumerate(subject_files[:3], 1):  # Limit to 3
                        file_name = file_data.get('file_name', 'Unknown')
                        summary = QdrantRAG.get_document_summary(file_name, subject_full_name)
                        response += f"**{idx}. {file_name}**\n{summary}\n\n"
            
            st.session_state.chat_histories[subject_key].append({'role': 'assistant', 'content': response})
            st.rerun()
    
    with col3:
        if st.button("🔍 Search", use_container_width=True, key="btn_search"):
            response = f"🔍 **Ready to search {len(subject_files)} documents!**\n\n"
            response += "Type any question and I'll search through all uploaded materials.\n\n"
            response += "**Examples:**\n"
            response += "• What are the key concepts?\n"
            response += "• Explain [topic]\n"
            response += "• Summarize the main points"
            
            st.session_state.chat_histories[subject_key].append({'role': 'assistant', 'content': response})
            st.rerun()
    
    with col4:
        if st.button("💡 Help", use_container_width=True, key="btn_help"):
            response = "💡 **How to Use:**\n\n"
            response += "📚 **List Resources** - View all materials\n"
            response += "📝 **Summaries** - Get document overviews\n"
            response += "🔍 **Search** - AI-powered search tips\n"
            response += "💬 **Chat** - Ask questions naturally\n\n"
            response += "Type your question below and I'll search through the documents!"
            
            st.session_state.chat_histories[subject_key].append({'role': 'assistant', 'content': response})
            st.rerun()
    
    st.markdown("---")
    
    # Show resources with DOWNLOAD functionality
    with st.expander(f"📚 View & Download {len(subject_files)} Resources", expanded=False):
        if len(subject_files) == 0:
            st.info(f"No resources yet. Upload some materials to get started!")
        else:
            for doc_id, file_data in subject_files:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"📄 **{file_data.get('file_name', 'Unknown')}**")
                    st.caption(f"Size: {file_data.get('file_size', 0) / 1024:.1f} KB")
                
                with col2:
                    download_url = file_data.get('download_url')
                    
                    if download_url:
                        st.markdown(f'<a href="{download_url}" class="download-btn" download>⬇️ Download</a>', unsafe_allow_html=True)
                    else:
                        storage_path = file_data.get('storage_path')
                        if storage_path:
                            try:
                                bucket = storage.bucket()
                                blob = bucket.blob(storage_path)
                                from datetime import timedelta
                                signed_url = blob.generate_signed_url(timedelta(hours=1))
                                st.markdown(f'<a href="{signed_url}" class="download-btn" download>⬇️ Download</a>', unsafe_allow_html=True)
                            except Exception as e:
                                st.caption("❌ Error")
                        else:
                            st.caption("⏳ Processing")
                
                st.divider()
    
    st.markdown("---")
    
    # Language selector
    col_lang, col_count = st.columns([2, 3])
    with col_lang:
        language = st.selectbox(
            "🌍 Language:",
            ["English", "Urdu", "Arabic", "Spanish", "French"],
            key=f"language_{subject_key}"
        )
    
    with col_count:
        st.caption(f"💬 {len(messages)} messages • 🔒 Private to you")
    
    # Messages display
    if len(messages) == 0:
        st.markdown(f"""
            <div style="text-align: center; padding: 60px 20px; color: #c084fc;">
                <div style="font-size: 4rem; margin-bottom: 20px;">🤖</div>
                <p style="font-size: 1.3rem; font-weight: 600;">AI Assistant Ready!</p>
                <p style="font-size: 1rem;">Ask me anything about {subject['name']}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        for idx, msg in enumerate(messages):
            if msg['role'] == 'user':
                st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-message">{msg["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        prompt = st.text_input(
            "Message",
            placeholder=f"Ask about {subject['name']}...",
            label_visibility="collapsed",
            key=f"input_{subject_key}"
        )
    
    with col2:
        send_btn = st.button("Send", use_container_width=True, type="primary", key="btn_send")
    
    if send_btn and prompt:
        # Add user message
        st.session_state.chat_histories[subject_key].append({'role': 'user', 'content': prompt})
        
        # Log interaction
        FirebaseOps.log_interaction(user_id, 'message_sent', {
            'subject': subject['name'],
            'message': prompt,
            'language': language
        })
        MetricsTracker.track_message()
        
        # Generate response
        with st.spinner("🔍 Searching documents..."):
            ai_response = QdrantRAG.generate_rag_response(
                query=prompt,
                subject=subject_full_name,
                language=language
            )
        
        # Add AI response
        st.session_state.chat_histories[subject_key].append({'role': 'assistant', 'content': ai_response})
        st.rerun()