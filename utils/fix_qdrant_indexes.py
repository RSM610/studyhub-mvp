import streamlit as st
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

def fix_qdrant_indexes():
    """Add missing payload indexes to all existing Qdrant collections"""
    
    st.title("🔧 Fix Qdrant Indexes")
    st.write("This will add missing payload indexes to your existing Qdrant collections")
    
    try:
        # Get Qdrant client
        client = QdrantClient(
            url=st.secrets["qdrant"]["url"],
            api_key=st.secrets["qdrant"]["api_key"]
        )
        
        # Get all collections
        collections = client.get_collections().collections
        
        st.info(f"Found {len(collections)} collections")
        
        if st.button("🔨 Fix All Collections", type="primary"):
            fixed_count = 0
            error_count = 0
            
            progress_bar = st.progress(0)
            
            for idx, collection in enumerate(collections):
                collection_name = collection.name
                st.write(f"Processing: {collection_name}")
                
                try:
                    # Try to create indexes (will skip if they already exist)
                    try:
                        client.create_payload_index(
                            collection_name=collection_name,
                            field_name="file_name",
                            field_schema=PayloadSchemaType.KEYWORD
                        )
                        st.success(f"✅ Added file_name index to {collection_name}")
                        fixed_count += 1
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            st.info(f"ℹ️ file_name index already exists in {collection_name}")
                        else:
                            st.warning(f"⚠️ Could not add file_name index: {e}")
                    
                    try:
                        client.create_payload_index(
                            collection_name=collection_name,
                            field_name="subject",
                            field_schema=PayloadSchemaType.KEYWORD
                        )
                        st.success(f"✅ Added subject index to {collection_name}")
                        fixed_count += 1
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            st.info(f"ℹ️ subject index already exists in {collection_name}")
                        else:
                            st.warning(f"⚠️ Could not add subject index: {e}")
                    
                    try:
                        client.create_payload_index(
                            collection_name=collection_name,
                            field_name="doc_id",
                            field_schema=PayloadSchemaType.KEYWORD
                        )
                        st.success(f"✅ Added doc_id index to {collection_name}")
                        fixed_count += 1
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            st.info(f"ℹ️ doc_id index already exists in {collection_name}")
                        else:
                            st.warning(f"⚠️ Could not add doc_id index: {e}")
                    
                except Exception as e:
                    st.error(f"❌ Error processing {collection_name}: {e}")
                    error_count += 1
                
                progress_bar.progress((idx + 1) / len(collections))
            
            st.success(f"""
                ✨ Done!
                
                - Fixed: {fixed_count} indexes
                - Errors: {error_count}
            """)
            st.balloons()
    
    except Exception as e:
        st.error(f"Error connecting to Qdrant: {e}")
        st.exception(e)

if __name__ == "__main__":
    fix_qdrant_indexes()
