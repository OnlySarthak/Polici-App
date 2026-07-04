from sqlalchemy import Numeric, Column, func
from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# 1. Base Class for Postgres Models
class Base(DeclarativeBase):
    pass

# 2. Application Status Enumeration
class ApplicationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"

# =====================================================================
# USER MODEL
# =====================================================================
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    policies: Mapped[list["InsuranceModel"]] = relationship(back_populates="owner")
    applications: Mapped[list["ApplicationModel"]] = relationship(back_populates="applicant")

# =====================================================================
# INSURANCE POLICY MODEL (Static Product Definition)
# =====================================================================
class InsuranceModel(Base):
    __tablename__ = "insurances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # e.g., "POL-HEALTH-001"
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    coverage_details: Mapped[str] = mapped_column(Text, nullable=False) # Maps to heavy document string
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    # Relationships
    owner: Mapped["UserModel"] = relationship(back_populates="policies")
    applications: Mapped[list["ApplicationModel"]] = relationship(back_populates="insurance")

# =====================================================================
# APPLICATION MODEL (Dynamic Operational State)
# =====================================================================
class ApplicationModel(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[ApplicationStatus] = mapped_column(String(20), default=ApplicationStatus.PENDING, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=100, nullable=False) # e.g., 401 for bad medical history
    # Stores structural JSON tags like ["LATE_SUBMISSION", "MAX_LIMIT_EXCEEDED"]
    denial_tags: Mapped[str] = mapped_column(Text, nullable=True) 
    
    # 🌟 NEW: Answers "When was my status last updated?"
    status_changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Foreign Keys linking the core parts together
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    insurance_id: Mapped[int] = mapped_column(Integer, ForeignKey("insurances.id"), nullable=False)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applicant: Mapped["UserModel"] = relationship(back_populates="applications")
    insurance: Mapped["InsuranceModel"] = relationship(back_populates="applications")

class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    
    # 1. Unique ID for every single file row
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 2. The exact string filename sent from your MERN frontend
    # Unique=True ensures you never ingest the same filename twice by mistake!
    document_name = Column(String, unique=True, nullable=False, index=True)
    
    # 3. Optional but highly recommended metadata for tracking updates
    uploaded_at = Column(DateTime, server_default=func.now())