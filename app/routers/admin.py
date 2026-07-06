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
        filenames = [doc.document_name for doc in result]
        return {
            "status": "success",
            "message": filenames
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/document/{filename}")
def get_document(filename: str):
    try:
        from app.database.config import SessionLocal
        from app.models.insurance import PolicyDocument
        
        db_session = SessionLocal()()
        try:
            doc = db_session.query(PolicyDocument).filter_by(document_name=filename).first()
            if not doc:
                return {
                    "status": "error",
                    "message": "Document not found in the registry."
                }
            return {
                "status": "success",
                "message": doc.document_text or "[Document contains no text content]"
            }
        finally:
            db_session.close()
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }