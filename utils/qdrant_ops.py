import streamlit as st
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType, PayloadIndexParams
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
            st.warning(f"⚠️ Qdrant not configured. RAG features disabled. Add Qdrant credentials to secrets.toml")
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
        """Create Qdrant collection if it doesn't exist WITH proper payload indexes"""
        client = QdrantRAG.get_client()
        if not client:
            return False
        
        try:
            collections = client.get_collections().collections
            exists = any(col.name == collection_name for col in collections)
            
            if not exists:
                # Create collection with vector config
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                
                # IMPORTANT: Create payload indexes for filtering
                # This allows us to filter by file_name, subject, etc.
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="file_name",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="subject",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="doc_id",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                except Exception as index_error:
                    # Indexes might already exist or not be needed
                    st.warning(f"Could not create indexes (may already exist): {index_error}")
                
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
            
            collection_name = f"subject_{subject.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '').replace(',', '')}"
            
            # Create collection with proper indexes
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
                    # Use a more unique point ID to avoid collisions
                    point_id = hashlib.md5(f"{doc_id}_{file_name}_{idx}_{datetime.now().timestamp()}".encode()).hexdigest()
                    
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
            
            collection_name = f"subject_{subject.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '').replace(',', '')}"
            
            # Get query embedding
            query_embedding = QdrantRAG.get_embeddings(query)
            
            if not query_embedding:
                return []
            
            # Search Qdrant WITHOUT filters (more reliable)
            # We'll filter in the payload results instead
            results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit * 2  # Get more results to filter
            )
            
            # Extract relevant info
            documents = []
            for result in results:
                # Make sure the result is actually from this subject
                if result.payload.get("subject", "").lower() == subject.lower():
                    documents.append({
                        "text": result.payload.get("text", ""),
                        "file_name": result.payload.get("file_name", "Unknown"),
                        "score": result.score
                    })
                    
                    if len(documents) >= limit:
                        break
            
            return documents
            
        except Exception as e:
            st.error(f"Error searching Qdrant: {e}")
            return []
    
    @staticmethod
    def generate_rag_response(query, subject, language="English"):
        """
        Generate intelligent RAG response using LLM (OpenAI/Anthropic)
        """
        try:
            # Search for relevant documents
            documents = QdrantRAG.search_documents(query, subject, limit=5)
            
            if not documents:
                return f"❌ **No relevant information found**\n\nI couldn't find anything about '{query}' in the uploaded {subject} materials.\n\n**Try:**\n• Uploading notes or past papers for this topic\n• Using different keywords\n• Asking about topics covered in existing files"
            
            # Build context from documents
            context = "\n\n".join([
                f"Source: {doc['file_name']}\n{doc['text']}"
                for doc in documents
            ])
            
            # === ADD YOUR LLM API HERE ===
            # Option 1: OpenAI (Recommended - cheaper)
            try:
                import openai
                openai.api_key = st.secrets.get("openai", {}).get("api_key", "")
                
                if openai.api_key:
                    prompt = f"""You are a helpful study assistant. Answer the student's question using ONLY the provided context from their study materials.

Question: {query}
Subject: {subject}
Language: {language}

Context from uploaded materials:
{context}

Instructions:
1. Answer in {language}
2. Be clear and concise
3. Only use information from the context
4. If the context doesn't contain the answer, say so
5. Cite which source you're using

Answer:"""
                    
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",  # Cheap: $0.50 per 1M tokens
                        messages=[
                            {"role": "system", "content": "You are a helpful study assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    ai_answer = response.choices[0].message.content
                    
                    # Format response nicely
                    final_response = f"🤖 **AI Answer:**\n\n{ai_answer}\n\n---\n\n"
                    final_response += f"📚 **Sources used:**\n"
                    for idx, doc in enumerate(documents, 1):
                        final_response += f"{idx}. {doc['file_name']} (relevance: {doc['score']*100:.1f}%)\n"
                    
                    return final_response
            except Exception as e:
                st.warning(f"⚠️ OpenAI API not configured: {e}")
            
            # Option 2: Anthropic Claude (Better quality, more expensive)
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=st.secrets.get("anthropic", {}).get("api_key", ""))
                
                message = client.messages.create(
                    model="claude-3-haiku-20240307",  # Cheapest Claude
                    max_tokens=500,
                    messages=[{
                        "role": "user",
                        "content": f"""Answer this question using ONLY the provided context.

Question: {query}
Language: {language}

Context: {context}

Answer clearly in {language}:"""
                    }]
                )
                
                ai_answer = message.content[0].text
                
                final_response = f"🤖 **AI Answer:**\n\n{ai_answer}\n\n---\n\n"
                final_response += f"📚 **Sources used:**\n"
                for idx, doc in enumerate(documents, 1):
                    final_response += f"{idx}. {doc['file_name']} (relevance: {doc['score']*100:.1f}%)\n"
                
                return final_response
            except Exception as e:
                st.warning(f"⚠️ Anthropic API not configured: {e}")
            
            # === FALLBACK: No LLM API configured ===
            # Show raw excerpts (current behavior)
            response = f"🔍 **Search Results for: '{query}'**\n\n"
            response += f"⚠️ *No LLM API configured - showing raw excerpts*\n\n"
            response += f"Found **{len(documents)} relevant sections**:\n\n---\n\n"
            
            for idx, doc in enumerate(documents, 1):
                response += f"### 📄 Source {idx}: {doc['file_name']}\n"
                response += f"*Relevance: {doc['score']*100:.1f}%*\n\n"
                text = doc['text'].strip()
                if len(text) > 600:
                    text = text[:600] + "..."
                response += f"{text}\n\n---\n\n"
            
            response += f"\n💡 **To enable AI-generated answers:**\n"
            response += f"Add OpenAI or Anthropic API key to `.streamlit/secrets.toml`\n\n"
            response += f"Example:\n```toml\n[openai]\napi_key = 'sk-...'\n```"
            
            return response
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
            return f"❌ **Error:** {str(e)}\n\nPlease check your Qdrant connection."
    
    @staticmethod
    def get_document_summary(file_name, subject):
        """Get summary of a specific document - NO filters, pure Python filtering"""
        try:
            client = QdrantRAG.get_client()
            if not client:
                return "⚠️ Qdrant not configured"
            
            collection_name = f"subject_{subject.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '').replace(',', '')}"
            
            # Check if collection exists
            try:
                collections = client.get_collections().collections
                collection_exists = any(col.name == collection_name for col in collections)
                
                if not collection_exists:
                    return f"No vector database found for {subject}. Upload files first."
            except:
                return "Could not check collections."
            
            # Get ALL points without any filters
            try:
                # Use scroll with no filters at all
                all_points, _ = client.scroll(
                    collection_name=collection_name,
                    limit=200,  # Get more points to ensure we find the file
                    with_payload=True,
                    with_vectors=False  # Don't need vectors, just payload
                )
                
                if not all_points or len(all_points) == 0:
                    return "No documents found in this collection."
                
                # Filter for matching file_name in Python (not in Qdrant)
                matching_chunks = []
                for point in all_points:
                    point_file = point.payload.get("file_name", "")
                    # Case-insensitive comparison
                    if point_file.lower() == file_name.lower():
                        chunk_text = point.payload.get("text", "")
                        chunk_index = point.payload.get("chunk_index", 0)
                        matching_chunks.append((chunk_index, chunk_text))
                
                if not matching_chunks:
                    return f"No content found for '{file_name}'. Available files in collection: {len(set(p.payload.get('file_name', 'Unknown') for p in all_points))}"
                
                # Sort by chunk index
                matching_chunks.sort(key=lambda x: x[0])
                
                # Combine first few chunks as summary
                summary_chunks = [text for _, text in matching_chunks[:3]]
                summary = "\n\n".join(summary_chunks)
                
                if len(summary) > 1000:
                    summary = summary[:1000] + "..."
                
                return f"📄 **{file_name}**\n\n{summary}\n\n💡 Contains {len(matching_chunks)} sections total."
                
            except Exception as scroll_error:
                return f"Error reading collection: {str(scroll_error)}"
            
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
                collection_name = f"subject_{subject_name.lower().replace(' ', '_').replace('+', '').replace('(', '').replace(')', '').replace(',', '')}"
                
                if QdrantRAG.create_collection_if_not_exists(collection_name):
                    created.append(subject_name)
            
            return created
            
        except Exception as e:
            st.error(f"Error creating collections: {e}")
            return []