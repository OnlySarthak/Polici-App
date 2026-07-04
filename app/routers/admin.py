import os
from app.schemas.state import RoutingState
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.knowledge_base.kb import initia_ingestion_run
from app.knowledge_base.helper import delete_doc, list_files


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

class DocumentSubmitRequest(BaseModel):
    raw_text_from_frontend: str
    filename: str

@router.post("/submit-doc")
def submit_doc(request: DocumentSubmitRequest):
        #get, chunk, embed document
        #store vector
    try:
        # Issue 3 fixed: passing data via Pydantic model (JSON Body)
        result = initia_ingestion_run(request.raw_text_from_frontend, request.filename)
        
        response = {
            "status": "success",
            "message": result
        }
        return response
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.delete("/delete-doc")
def delete_document(filename: str):
    try:
        # Issue 5 fixed: Changed from @router.get to @router.delete
        # Issue 4 fixed for delete (assuming delete_doc could be vulnerable too):
        safe_filename = os.path.basename(filename)
        result = delete_doc(safe_filename)
        return {
            "status": "success",
            "message": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/doc-list")
def list_docs():
    try:
        result = list_files()
        return {
            "status": "success",
            "message": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/document/{filename}")
def get_document(filename: str):
    try:
        from app.knowledge_base.kb import DOCSTORE_DIR, verify_storage_locations
        from llama_index.core import StorageContext
        from llama_index.core.schema import NodeRelationship
        
        store_obj = verify_storage_locations()
        storage_context = StorageContext.from_defaults(
            vector_store=store_obj["vector_store"],
            persist_dir=DOCSTORE_DIR
        )
        
        docstore = storage_context.docstore
        matching_text = []
        
        # Search the docstore for nodes originating from this filename
        for node_id, node in docstore.docs.items():
            if node.metadata.get("source") == filename:
                # To avoid duplicating text, we only extract the top-level parent chunks 
                # (nodes that don't have a PARENT relationship)
                parent_rel = node.relationships.get(NodeRelationship.PARENT)
                if not parent_rel:
                    matching_text.append(node.get_content())
                    
        # Fallback: if we didn't find any root parents, just append whatever chunks we have
        if not matching_text:
            for node_id, node in docstore.docs.items():
                if node.metadata.get("source") == filename:
                    matching_text.append(node.get_content())
                    
        if not matching_text:
            return {"status": "error", "message": "Document not found in the LlamaIndex docstore."}
            
        # Reconstruct the document by joining the chunks
        full_text = "\n\n".join(matching_text)
        
        return {
            "status": "success",
            "message": full_text
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }