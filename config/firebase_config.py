import firebase_admin
from firebase_admin import credentials, firestore, auth
import streamlit as st

def initialize_firebase():
    """Initialize Firebase with service account credentials"""
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": st.secrets["FIREBASE_TYPE"],
            "project_id": st.secrets["FIREBASE_PROJECT_ID"],
            "private_key_id": st.secrets["FIREBASE_PRIVATE_KEY_ID"],
            "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
            "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
            "client_id": st.secrets["FIREBASE_CLIENT_ID"],
            "auth_uri": st.secrets["FIREBASE_AUTH_URI"],
            "token_uri": st.secrets["FIREBASE_TOKEN_URI"],
            "auth_provider_x509_cert_url": st.secrets["FIREBASE_AUTH_PROVIDER_CERT_URL"],
            "client_x509_cert_url": st.secrets["FIREBASE_CLIENT_CERT_URL"],
            "universe_domain": st.secrets.get("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")
        })
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

db = initialize_firebase()