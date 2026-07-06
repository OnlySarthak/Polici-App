from app.models.insurance import PolicyDocument
from app.database.config import SessionLocal

def delete_doc(target_filename : str):
    import os
    from app.knowledge_base.kb import verify_storage_locations, DOCSTORE_DIR
    from llama_index.core import StorageContext
    
    store_obj = verify_storage_locations()
    chroma_collection = store_obj["chroma_collection"]
    db_session = SessionLocal()()
    try:
        # 💥 1. Wipe out the LlamaIndex child nodes inside Chroma
        chroma_collection.delete(where={"source": target_filename})

        # 📁 2. Wipe out all parent/child chunks from LlamaIndex docstore on disk
        if os.path.exists(os.path.join(DOCSTORE_DIR, "docstore.json")):
            storage_context = StorageContext.from_defaults(
                vector_store=store_obj["vector_store"],
                persist_dir=DOCSTORE_DIR
            )
            docstore = storage_context.docstore
            nodes_to_delete = []
            for node_id, node in list(docstore.docs.items()):
                if node.metadata.get("source") == target_filename:
                    nodes_to_delete.append(node_id)
            
            for node_id in nodes_to_delete:
                docstore.delete_document(node_id)
                
            storage_context.persist(persist_dir=DOCSTORE_DIR)

        # 📊 3. Wipe out the tracking row inside Postgres
        db_session.query(PolicyDocument).filter_by(document_name=target_filename).delete()
        db_session.commit()
        return "File deleted successfully"
    finally:
        db_session.close()

def list_files():
    db_session = SessionLocal()()
    try:
        return db_session.query(PolicyDocument).all()
    finally:
        db_session.close()

def add_file_name(filename : str, text : str = None):
    #add document name to db
    db_session = SessionLocal()()
    try:
        #check if same name file exist
        # Returns a clean list: ['policy_v1.pdf', 'user_manual.txt']
        all_names = [doc.document_name for doc in db_session.query(PolicyDocument).all()]
        if filename in all_names:
            print("file already exist")
            raise Exception("file already exist")

        new_doc = PolicyDocument(document_name=filename, document_text=text)
        db_session.add(new_doc)
        db_session.commit()
    finally:
        db_session.close()