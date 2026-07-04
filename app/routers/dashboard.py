from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Body   
from sqlalchemy.orm import Session
from typing import Optional

from app.database.config import SessionLocal
from app.models.insurance import UserModel, ApplicationModel, InsuranceModel

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

def get_db():
    db = SessionLocal()() # instantiate session
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(response: Response, username: str = Body(..., embed=True), db: Session = Depends(get_db)):
    # Simple login fetching user by email or name (no password needed as per instructions)
    user = db.query(UserModel).filter(UserModel.email == username).first()
    if not user:
        user = db.query(UserModel).filter(UserModel.full_name == username).first()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    application = db.query(ApplicationModel).filter(ApplicationModel.user_id == user.id).first()
    insurance = db.query(InsuranceModel).filter(InsuranceModel.user_id == user.id).first()
    
    # Set cookies (accessible via JS since httponly is False by default)
    response.set_cookie(key="user_id", value=str(user.id))
    if application:
        response.set_cookie(key="application_id", value=application.application_id)
    if insurance:
        response.set_cookie(key="insurance_id", value=insurance.policy_id)
    
    return {
        "message": "Login successful",
        "user_id": user.id,
        "application_id": application.application_id if application else None,
        "insurance_id": insurance.policy_id if insurance else None
    }

@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="user_id")
    response.delete_cookie(key="application_id")
    response.delete_cookie(key="insurance_id")
    return {
        "message": "Logout successful"
    }


@router.get("/")
def get_dashboard(
    user_id: Optional[int] = Cookie(None), 
    application_id: Optional[str] = Cookie(None), 
    insurance_id: Optional[str] = Cookie(None), 
    db: Session = Depends(get_db)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID cookie missing")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    application = None
    if application_id:
        application = db.query(ApplicationModel).filter(ApplicationModel.application_id == application_id).first()
        
    insurance = None
    if insurance_id:
        insurance = db.query(InsuranceModel).filter(InsuranceModel.policy_id == insurance_id).first()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at
        },
        "application": {
            "application_id": application.application_id,
            "status": application.status,
            "status_code": application.status_code,
            "denial_tags": application.denial_tags
        } if application else None,
        "insurance": {
            "policy_id": insurance.policy_id,
            "title": insurance.title,
            "coverage_details": insurance.coverage_details
        } if insurance else None
    }

