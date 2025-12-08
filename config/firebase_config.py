import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    """Initialize Firebase with service account credentials"""
    if not firebase_admin._apps:
        cred = credentials.Certificate({
  "type": "service_account",
  "project_id": "studyhub-mvp-4f5c9",
  "private_key_id": "8f5586542c153a46cdba3d0810739ff514bc449b",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC1PNIR6CYwKOVY\n8UMul3Gd3uJ3izNq/yxFS97CJShFeFYYBwHIZXMLUoVNbgQU4YATVGZcrj/pxBeg\nzJ38Uyw1wYBtH5+2bACuCn6PMX/9POFxE2jsqyHBBu3qZdoxHH+y+f9/DYrU6zCo\n7y/9gTVJNP7nW7enK3ieqB0zX32XrEEfUoYCQQ33Uh4mU7pOdRzuLnZyAk+c+XDo\nOtQzLbIM14skSo7frLIMaD+sn5QNzRKDcrER2F4/hbLhZBmcNO1oOvsHQd9+oMMr\ni+/7gezHcihwNOiriasdV7NDLuWRqYij0hz9NRnK+5D9w/w/Hd/xGplZNXrYDSZc\nUJdiQDg1AgMBAAECggEADOZL6wH2zd2E5wq50s253ktOtSscOS5f8uK085gvc82R\ndMGMhLxSLukfTpgl0QXbCgUrPMeBcKlujeX8DK/JNffhPmMbPAgXfrIfUro3anyn\nbL2KVBk66TR0Djq61MOhg/yiDP0xKqxx8mQ4qmneGak2LdA4xyMJ9JW+PLminjJO\nzd8uLp90yGotQxZ3F3EeqyrjsUlKWLOjJBJnPEjHnBhgV8KLvQnzcwA6X3UzzADF\nmloq9Q8jKHpZv/5u/jkNS3spHStJhcLt3q6EhneexV9b/LpBmfrlhTzotx2RblER\nmBpB6ANyM7GJLzlKJADcCpKyBc9f/JqaJoCJrE57dQKBgQDXkUtUMRvNXGw09rdz\nQvRqtaCZmeR9DTCkQx7Ef6A6Ums5rZIMKAsi4PNgzRcHYMtqY44gzpqBK/OisIxC\n8PhRUvHkQCwE8/dZKffQj1vT0zCBL7tqu1XDFsr9RVcMltyqg4L1mjU/t5xbLPos\nwuePY/ZJuSy19v3BNMSMNqAOdwKBgQDXOyLRp01CuDfM/s2KTUAEj2w9LzbbjTpQ\nV+1qzL4LKFn2uex3i1Y8MQ+o4Ef5Fpxu3Y3BzBPu5q67Vg27m/ddY+fW3dmh+miW\nHojkxBgGFhbWR83qG43As32OIqRfKQFF/EVtqfxWrowQ549f6sa8+/vf5xV60sI2\nXikEVGp9swKBgATxmReqNKgGCZlBWz2yeGaGGdPL+rh/d/EcdPUutB8CSuE8wM+0\nj2TSYeKDcZbCuoeLFvRbqKFzv5eokt7qJde/njqM2jWW3sJVuxA2aXW3LzKXRKYS\n+8mImUkrsO5h+1eRwowdaEE41cYlhutF4Qeh1EEmlQbrTjCDJErO6ebLAoGBAK5h\nQUKv1A8chklWoF1PXXDUaxPfbwjPEdIKi1ceb1NG7CzUUlxAziuSbGec33NW+INy\niencWMIUsLkjbZj1MqO90BbsQ+nSom4Oa0c+AWDdAL+4CYOFs4HPawh/1MEszdVQ\nIUhKkyH/5YfEtQs3grGXT2kHJwYOQEAgZgcWBfm1AoGAR7y5UlvKoiiUEVb2H75z\n7mMMVMv/E3P00OfpLmc/TABG9Cebi37uk2c4sXQEz/sQjdWCOu2aU95KXduJuNrZ\nolwYnotLr1iURQm2HYy7qzRk94feBNTnPr31r3OqWRdemnJXmRTyU3VhTcTQWIgx\n1HAB8lTXzREX3NWz1s8x284=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@studyhub-mvp-4f5c9.iam.gserviceaccount.com",
  "client_id": "113722371306762996905",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40studyhub-mvp-4f5c9.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
})
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

db = initialize_firebase()