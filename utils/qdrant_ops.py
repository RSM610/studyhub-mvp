import streamlit as st
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
import hashlib
from datetime import datetime
import PyPDF2
import io

class QdrantRAG:
    """Handle all Qdrant vector database operations for RAG"""
    
    @staticmethod
    def get_client():
        """Get Qdrant client from secrets"""
        return QdrantClient(
            url=st.secrets["qdrant"]["url"],
            api_key=st.secrets["qdrant"]["api_key"]
        )
    
    @staticmethod
    def get_openai_client():
        """Get OpenAI client for embeddings and chat"""
        return OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    @staticmethod
    def create_collection_if_not_exists(collection_name):
        """Create Qdrant collection if it doesn't exist"""
        client = QdrantRAG.get_client()
        
        try:
            collections = client.get_collections().collections
            exists = any(col.name == collection_name for col in collections)
            
            if not exists:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)  # OpenAI text-embedding-3-small
                )
                return True
            return False
        except Exception as e:
            st.error(f"Error creating collection: {e}")
            return False
    
    @staticmethod
    def get_embeddings(text):
        """Get embeddings using OpenAI"""
        try:
            client = QdrantRAG.get_openai_client()
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            st.error(f"Error getting embeddings: {e}")
            return None
    
    @staticmethod
    def extract_text_from_file(file_content, file_name):
        """Extract text from various file formats"""
        try:
            if file_name.lower().endswith('.pdf'):
                # Extract text from PDF
                pdf_file = io.BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
            elif file_name.lower().endswith('.txt'):
                return file_content.decode('utf-8', errors='ignore')
            else:
                # Try to decode as text
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            st.error(f"Error extracting text: {e}")
            return str(file_content)
    
    @staticmethod
    def upload_document_to_qdrant(file_name, file_content, subject, user_id, doc_id):
        """
        Process document and upload to Qdrant
        """
        try:
            client = QdrantRAG.get_client()
            collection_name = f"subject_{subject.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '')}"
            
            # Create collection
            QdrantRAG.create_collection_if_not_exists(collection_name)
            
            # Extract text
            text_content = QdrantRAG.extract_text_from_file(file_content, file_name)
            
            if not text_content or len(text_content.strip()) < 10:
                return 0
            
            # Chunk text (1000 chars with 100 overlap)
            chunk_size = 1000
            overlap = 100
            chunks = []
            
            for i in range(0, len(text_content), chunk_size - overlap):
                chunk = text_content[i:i + chunk_size]
                if len(chunk.strip()) > 50:  # Minimum chunk size
                    chunks.append(chunk)
            
            # Upload chunks
            points = []
            for idx, chunk in enumerate(chunks):
                embedding = QdrantRAG.get_embeddings(chunk)
                
                if embedding:
                    point_id = hashlib.md5(f"{doc_id}_{idx}".encode()).hexdigest()
                    
                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                "text": chunk,
                                "file_name": file_name,
                                "subject": subject,
                                "user_id": user_id,
                                "doc_id": doc_id,
                                "chunk_index": idx,
                                "upload_time": datetime.now().isoformat()
                            }
                        )
                    )
            
            # Batch upload
            if points:
                client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                return len(points)
            
            return 0
            
        except Exception as e:
            st.error(f"Error uploading to Qdrant: {e}")
            return 0
    
    @staticmethod
    def search_documents(query, subject, limit=5):
        """Search Qdrant for relevant document chunks"""
        try:
            client = QdrantRAG.get_client()
            collection_name = f"subject_{subject.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '')}"
            
            # Get query embedding
            query_embedding = QdrantRAG.get_embeddings(query)
            
            if not query_embedding:
                return []
            
            # Search Qdrant
            results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Extract relevant info
            documents = []
            for result in results:
                documents.append({
                    "text": result.payload.get("text", ""),
                    "file_name": result.payload.get("file_name", "Unknown"),
                    "score": result.score
                })
            
            return documents
            
        except Exception as e:
            st.error(f"Error searching Qdrant: {e}")
            return []
    
    @staticmethod
    def generate_rag_response(query, subject, language="English"):
        """Generate RAG response using OpenAI GPT-4"""
        try:
            # Search for relevant documents
            documents = QdrantRAG.search_documents(query, subject, limit=5)
            
            if not documents:
                return f"I couldn't find relevant information about '{query}' in the uploaded {subject} materials. Try uploading notes or past papers first!"
            
            # Build context
            context = "\n\n".join([
                f"From {doc['file_name']} (relevance: {doc['score']:.2f}):\n{doc['text']}"
                for doc in documents
            ])
            
            # Generate response with GPT-4
            client = QdrantRAG.get_openai_client()
            
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful study assistant for {subject}. Answer questions based ONLY on the provided context. Respond in {language}. If the context doesn't contain relevant information, say so clearly."
                    },
                    {
                        "role": "user",
                        "content": f"Context from uploaded materials:\n\n{context}\n\nQuestion: {query}"
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
            return f"Error: {str(e)}"
    
    @staticmethod
    def get_document_summary(file_name, subject):
        """Get summary of a specific document"""
        try:
            client = QdrantRAG.get_client()
            collection_name = f"subject_{subject.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '')}"
            
            # Get all chunks from this file
            results = client.scroll(
                collection_name=collection_name,
                scroll_filter={
                    "must": [
                        {"key": "file_name", "match": {"value": file_name}}
                    ]
                },
                limit=100
            )
            
            if not results[0]:
                return "No content found."
            
            # Combine chunks
            full_text = " ".join([point.payload.get("text", "") for point in results[0]])
            
            # Generate summary with GPT
            openai_client = QdrantRAG.get_openai_client()
            
            response = openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "user", "content": f"Provide a concise summary:\n\n{full_text[:4000]}"}
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    def create_collections_for_existing_subjects():
        """Create Qdrant collections for all existing subjects in Firebase"""
        try:
            from config.firebase_config import db
            
            subjects = list(db.collection('subjects').stream())
            created = []
            
            for doc in subjects:
                subject_data = doc.to_dict()
                subject_name = f"{subject_data.get('name', '')} ({subject_data.get('category', '')})"
                collection_name = f"subject_{subject_name.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '')}"
                
                if QdrantRAG.create_collection_if_not_exists(collection_name):
                    created.append(subject_name)
            
            return created
            
        except Exception as e:
            st.error(f"Error creating collections: {e}")
            return []