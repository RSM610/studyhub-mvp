import streamlit as st
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import hashlib
from datetime import datetime
import PyPDF2
import io

class QdrantRAG:
    """Handle all Qdrant vector database operations for RAG - FREE VERSION"""
    
    # Cache the embedding model (loaded once)
    _embedding_model = None
    
    @staticmethod
    def get_client():
        """Get Qdrant client from secrets"""
        try:
            return QdrantClient(
                url=st.secrets["qdrant"]["url"],
                api_key=st.secrets["qdrant"]["api_key"]
            )
        except Exception as e:
            st.warning(f"⚠️ Qdrant not configured. Add credentials to secrets.toml")
            return None
    
    @staticmethod
    @st.cache_resource
    def get_embedding_model():
        """Get FREE Hugging Face embedding model (cached)"""
        if QdrantRAG._embedding_model is None:
            try:
                # Use free, lightweight model: all-MiniLM-L6-v2 (384 dimensions)
                QdrantRAG._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                st.error(f"Failed to load embedding model: {e}")
                return None
        return QdrantRAG._embedding_model
    
    @staticmethod
    def create_collection_if_not_exists(collection_name):
        """Create Qdrant collection if it doesn't exist"""
        client = QdrantRAG.get_client()
        if not client:
            return False
        
        try:
            collections = client.get_collections().collections
            exists = any(col.name == collection_name for col in collections)
            
            if not exists:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                return True
            return False
        except Exception as e:
            st.error(f"Error creating collection: {e}")
            return False
    
    @staticmethod
    def get_embeddings(text):
        """Get embeddings using FREE Hugging Face model"""
        try:
            model = QdrantRAG.get_embedding_model()
            if not model:
                return None
            
            # Generate embedding
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
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
        Process document and upload to Qdrant using FREE embeddings
        """
        try:
            client = QdrantRAG.get_client()
            if not client:
                st.warning("⚠️ Qdrant not configured - file saved to Firebase only")
                return 0
            
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
                    # Use integer IDs (Qdrant prefers this over strings)
                    point_id = abs(hash(f"{doc_id}_{idx}")) % (2**31)
                    
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
        """Search Qdrant for relevant document chunks using FREE embeddings"""
        try:
            client = QdrantRAG.get_client()
            if not client:
                return []
            
            collection_name = f"subject_{subject.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '')}"
            
            # Check if collection exists
            try:
                collections = client.get_collections().collections
                if not any(col.name == collection_name for col in collections):
                    return []
            except:
                return []
            
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
        """
        Generate RAG response - Returns FULL READABLE TEXT, not word lists
        """
        try:
            # Search for relevant documents
            documents = QdrantRAG.search_documents(query, subject, limit=5)
            
            if not documents:
                return (
                    f"❌ I couldn't find relevant information about '{query}' in the {subject} materials.\n\n"
                    f"💡 **Suggestions:**\n"
                    f"• Make sure documents are uploaded and approved\n"
                    f"• Try different keywords or phrasing\n"
                    f"• Ask about topics covered in the uploaded files"
                )
            
            # Build readable response with FULL SENTENCES
            response = f"📚 **Search Results for: '{query}'**\n\n"
            response += f"Found {len(documents)} relevant sections in your {subject} materials.\n\n"
            response += "---\n\n"
            
            # Show each document excerpt with context
            for idx, doc in enumerate(documents, 1):
                response += f"**#{idx} - From: {doc['file_name']}** (Relevance: {doc['score']:.1%})\n\n"
                
                # Clean and format the text properly
                text = doc['text'].strip()
                
                # Limit to first 400 characters for readability
                if len(text) > 400:
                    text = text[:400] + "..."
                
                response += f"{text}\n\n"
                response += "---\n\n"
            
            # Add summary
            response += "💡 **Summary:**\n"
            response += f"The information above is the most relevant content I found about '{query}' "
            response += f"in your {subject} materials. The excerpts are ranked by relevance.\n\n"
            
            if language != "English":
                response += f"\n🌍 **Note:** Full AI translation to {language} requires an LLM API. "
                response += "Currently showing English excerpts from your documents."
            
            return response
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
            return (
                f"❌ **Error:** {str(e)}\n\n"
                f"Please check:\n"
                f"• Qdrant connection is working\n"
                f"• Documents are properly uploaded\n"
                f"• Collection exists for {subject}"
            )
    
    @staticmethod
    def get_document_summary(file_name, subject):
        """Get summary of a specific document - FIXED to avoid index error"""
        try:
            client = QdrantRAG.get_client()
            if not client:
                return "⚠️ Qdrant not configured"
            
            collection_name = f"subject_{subject.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '')}"
            
            # Check if collection exists
            try:
                collections = client.get_collections().collections
                if not any(col.name == collection_name for col in collections):
                    return f"No collection found for {subject}"
            except:
                return "Error checking collections"
            
            # Get ALL points from collection (no filter to avoid index requirement)
            try:
                results = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )
            except Exception as e:
                return f"Error scrolling collection: {str(e)}"
            
            if not results or not results[0]:
                return "No content found in collection."
            
            # Filter for matching file_name in Python (avoids Qdrant index requirement)
            matching_chunks = [
                point for point in results[0]
                if point.payload.get("file_name") == file_name
            ]
            
            if not matching_chunks:
                available_files = list(set(p.payload.get('file_name', 'Unknown') for p in results[0][:10]))
                return (
                    f"No chunks found for '{file_name}' in this collection.\n\n"
                    f"Available files: {', '.join(available_files[:5])}"
                )
            
            # Sort by chunk_index to get them in order
            matching_chunks.sort(key=lambda x: x.payload.get("chunk_index", 0))
            
            # Combine first few chunks as summary
            chunks = [point.payload.get("text", "") for point in matching_chunks[:3]]
            summary = "\n\n".join(chunks)
            
            # Limit length
            if len(summary) > 1000:
                summary = summary[:1000] + "..."
            
            return (
                f"📄 **{file_name}**\n\n"
                f"{summary}\n\n"
                f"💡 This document contains {len(matching_chunks)} indexed sections."
            )
            
        except Exception as e:
            return f"Error getting summary: {str(e)}"