import streamlit as st
from utils.firebase_ops import FirebaseOps
from utils.metrics import MetricsTracker
from utils.qdrant_ops import QdrantRAG
from config.firebase_config import db

def render_chat():
    """Render AI chat interface with REAL RAG functionality"""
    subject = st.session_state.selected_subject
    
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
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("← Back to subjects", key="back_btn"):
        st.session_state.selected_subject = None
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
        if st.button("📚 List Resources", use_container_width=True):
            if len(subject_files) == 0:
                response = f"📭 No resources uploaded yet for {subject['name']}."
            else:
                response = f"📚 **{len(subject_files)} Resources Available:**\n\n"
                for idx, (doc_id, file_data) in enumerate(subject_files, 1):
                    response += f"{idx}. 📄 {file_data.get('file_name', 'Unknown')}\n"
            
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()
    
    with col2:
        if st.button("📝 Get Summaries", use_container_width=True):
            if len(subject_files) == 0:
                response = "📭 No files to summarize yet."
            else:
                with st.spinner("Generating summaries from Qdrant..."):
                    response = f"📝 **Document Summaries:**\n\n"
                    for idx, (doc_id, file_data) in enumerate(subject_files, 1):
                        file_name = file_data.get('file_name', 'Unknown')
                        summary = QdrantRAG.get_document_summary(file_name, subject_full_name)
                        response += f"**{idx}. {file_name}**\n{summary}\n\n"
            
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()
    
    with col3:
        if st.button("🔍 Search All", use_container_width=True):
            response = f"🔍 **Ready to search {len(subject_files)} documents!**\n\n"
            response += "Type any question and I'll search through all uploaded materials using RAG.\n\n"
            response += "Examples:\n"
            response += "• 'What are the key concepts?'\n"
            response += "• 'Explain [topic]'\n"
            response += "• 'Summarize the main points'"
            
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()
    
    with col4:
        if st.button("💡 Topics", use_container_width=True):
            if len(subject_files) == 0:
                response = "📭 No documents to analyze yet."
            else:
                # Use RAG to find common topics
                response = f"💡 **Analyzing {len(subject_files)} documents...**\n\n"
                response += "Available documents:\n"
                for idx, (doc_id, file_data) in enumerate(subject_files, 1):
                    response += f"• {file_data.get('file_name', 'Unknown')}\n"
                response += "\nAsk me about any topic and I'll search through these materials!"
            
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()
    
    st.markdown("---")
    
    # Show resources in expandable
    with st.expander(f"📚 View {len(subject_files)} Resources", expanded=False):
        if len(subject_files) == 0:
            st.info(f"No resources yet. Upload some materials to get started!")
        else:
            for doc_id, file_data in subject_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📄 **{file_data.get('file_name', 'Unknown')}**")
                    st.caption(f"Size: {file_data.get('file_size', 0) / 1024:.1f} KB")
                with col2:
                    if st.button("⬇️", key=f"dl_{doc_id}"):
                        st.info("Upgrade to Blaze for downloads")
    
    st.markdown("---")
    
    # Language selector
    col_lang, _ = st.columns([2, 3])
    with col_lang:
        language = st.selectbox(
            "🌍 Explain in:",
            ["English", "Urdu", "Arabic", "Spanish", "French", "German", "Chinese", "Japanese"],
            key="language_select"
        )
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Messages
    if len(st.session_state.messages) == 0:
        st.markdown(f"""
            <div style="text-align: center; padding: 60px 20px; color: #c084fc;">
                <div style="font-size: 4rem; margin-bottom: 20px;">🤖</div>
                <p style="font-size: 1.3rem; font-weight: 600;">RAG-Powered AI Ready!</p>
                <p style="font-size: 1rem;">Ask me anything about {subject['name']} and I'll search through uploaded materials~</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
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
            key="chat_input"
        )
    
    with col2:
        send_btn = st.button("Send ✨", use_container_width=True, type="primary")
    
    if send_btn and prompt:
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        
        user_id = st.session_state.user['id']
        FirebaseOps.log_interaction(user_id, 'message_sent', {
            'subject': subject['name'],
            'message': prompt,
            'language': language
        })
        MetricsTracker.track_message()
        
        # REAL RAG RESPONSE
        with st.spinner("🔍 Searching through documents..."):
            ai_response = QdrantRAG.generate_rag_response(
                query=prompt,
                subject=subject_full_name,
                language=language
            )
        
        st.session_state.messages.append({'role': 'assistant', 'content': ai_response})
        st.rerun()