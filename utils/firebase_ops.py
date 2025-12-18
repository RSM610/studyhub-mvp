from datetime import datetime
from config.firebase_config import db
import streamlit as st
from firebase_admin import storage
import uuid

class FirebaseOps:
    """Handle all Firebase database operations"""
    
    @staticmethod
    def create_user_session(user_id, email):
        """Track user login session"""
        session_data = {
            'user_id': user_id,
            'email': email,
            'login_time': datetime.now(),
            'session_id': st.session_state.get('session_id')
        }
        # Store the document reference ID
        doc_ref = db.collection('sessions').add(session_data)
        return doc_ref[1].id  # Return the document ID
    
    @staticmethod
    def log_interaction(user_id, event_type, metadata=None):
        """Log user interactions for metrics tracking"""
        interaction = {
            'user_id': user_id,
            'event_type': event_type,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }
        db.collection('interactions').add(interaction)
    
    @staticmethod
    def track_session_duration(session_doc_id, duration_seconds):
        """Update session duration on logout"""
        try:
            db.collection('sessions').document(session_doc_id).update({
                'duration_seconds': duration_seconds,
                'logout_time': datetime.now()
            })
        except Exception as e:
            # If document doesn't exist, just log the error and continue
            print(f"Could not update session: {e}")
    
    @staticmethod
    def save_uploaded_file(user_id, file_name, file_data, subject):
        """Store uploaded file to Firebase Storage and save metadata"""
        try:
            # Generate unique file path
            file_id = str(uuid.uuid4())
            storage_path = f"uploads/{subject}/{file_id}_{file_name}"
            
            # Upload to Firebase Storage
            bucket = storage.bucket()
            blob = bucket.blob(storage_path)
            blob.upload_from_string(file_data, content_type='application/octet-stream')
            
            # Make file publicly accessible (or use signed URLs for private access)
            blob.make_public()
            download_url = blob.public_url
            
            # Save metadata to Firestore
            file_doc = {
                'user_id': user_id,
                'file_name': file_name,
                'subject': subject,
                'upload_time': datetime.now(),
                'file_size': len(file_data),
                'verified': False,
                'storage_path': storage_path,
                'download_url': download_url
            }
            return db.collection('uploaded_files').add(file_doc)
            
        except Exception as e:
            st.error(f"Error uploading file: {e}")
            return None
    
    @staticmethod
    def get_file_download_url(doc_id):
        """Get download URL for a file"""
        try:
            doc = db.collection('uploaded_files').document(doc_id).get()
            if doc.exists:
                data = doc.to_dict()
                return data.get('download_url', None)
            return None
        except Exception as e:
            st.error(f"Error getting download URL: {e}")
            return None
    
    @staticmethod
    def download_file_from_storage(storage_path):
        """Download file content from Firebase Storage"""
        try:
            bucket = storage.bucket()
            blob = bucket.blob(storage_path)
            return blob.download_as_bytes()
        except Exception as e:
            st.error(f"Error downloading file: {e}")
            return None
    
    @staticmethod
    def get_user_stats(user_id):
        """Retrieve user engagement statistics"""
        try:
            interactions = list(db.collection('interactions').where(field_path='user_id', op_string='==', value=user_id).stream())
            return len(interactions)
        except Exception as e:
            st.error(f"Error getting stats: {e}")
            return 0