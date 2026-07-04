from llama_index.core.indices import vector_store
import os
import sys
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.schema import Document
from app.models.insurance import PolicyDocument
from app.database.config import SessionLocal
from app.knowledge_base.helper import add_file_name
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =====================================================================
# CONFIGURATION & CONSTANTS
# =====================================================================

# Clean folder targets for strict local storage separation
CHROMA_DIR = os.environ.get("CHROMA_DIR", "./app/chroma_db")                        #for embedded child nodes
DOCSTORE_DIR = os.environ.get("DOCSTORE_DIR", "./app/local_storage_folder")           #for parent nodes map

retriver = None

def verify_storage_locations():
    try:
        # Auto-create directories if they do not exist
        os.makedirs(CHROMA_DIR, exist_ok=True)
        os.makedirs(DOCSTORE_DIR, exist_ok=True)

        # Connect to on-disk ChromaDB instance
        db_client = chromadb.PersistentClient(path=CHROMA_DIR)
        chroma_collection = db_client.get_or_create_collection("insurance_child_vectors")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        return {
            "vector_store": vector_store,
            "chroma_collection": chroma_collection,
            "db_client": db_client
        }

    except Exception as e:
        print(f"ERROR: CRITICAL FAILURE during Phase 2: {e}")
        sys.exit(1)


# =====================================================================
# STAGE 3: WRITE FLOW (RAN ONCE TO GENERATE AND STORE)
# =====================================================================
def initia_ingestion_run(raw_text_from_frontend: str, filename: str):
    store_obj = verify_storage_locations()

    vector_store = store_obj["vector_store"]
    chroma_collection = store_obj["chroma_collection"]
    db_client = store_obj["db_client"]

    print("--- Execution Mode: Writing Data ---")

    #add file name to db
    add_file_name(filename)
    
    # 1. Create a mock single document representing raw policy source
    raw_doc = Document(text=raw_text_from_frontend, metadata={"source": filename})
    
    # 2. Setup 2-level parser: Parent (512 tokens) -> Child (128 tokens)
    parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[512, 128]) 
    all_nodes = parser.get_nodes_from_documents([raw_doc])
    
    # 3. Separate structural leaves (Extracts ONLY the bottom-tier children)
    child_nodes = get_leaf_nodes(all_nodes)
    
    # 4. Construct storage target layout (Parents held in RAM momentarily)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # 5. Build Index: Generates embeddings ONLY for child_nodes, sends to ChromaDB
    index = VectorStoreIndex(nodes=child_nodes, storage_context=storage_context)
    
    # 6. Flush heavy parent node mapping dictionaries out of RAM onto disk as JSON
    storage_context.persist(persist_dir=DOCSTORE_DIR)
    print(f"Ingestion successful! Core components dumped to disk safely.")

    global retriver
    retriver = index.as_retriever(similarity_top_k=3)

    return "file uploaded successfully"

# =====================================================================
# STAGE 4: PRODUCTION READ FLOW (LOAD EXISTING INDEX DISK DATA)
# =====================================================================
def production_read_flow():
    global retriver
    store_obj = verify_storage_locations()

    vector_store = store_obj["vector_store"]
    chroma_collection = store_obj["chroma_collection"]
    db_client = store_obj["db_client"]

    print("--- Execution Mode: Reading Existing Data ---")
    
    try:
        # 1. Rebuild storage context strictly pointing to pre-saved local JSON structures
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
            persist_dir=DOCSTORE_DIR # Reads your parent docstore.json mapping file
        )
        
        # 2. Hydrate the functional index directly from your local folders
        index = load_index_from_storage(storage_context)
    except Exception as e:
        print(f"Index not found or failed to load ({e}).")
        raise FileNotFoundError(
            "The knowledge base index was not found or could not be loaded. "
            "Please upload policy documents first using the admin interface."
        ) from e
    
    # 3. Create the active structural retriever (fetches top-3 matching nodes)
    retriver = index.as_retriever(similarity_top_k=3)

