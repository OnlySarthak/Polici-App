import sys
import os
# Add the project root (App directory) to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import uuid
from datetime import datetime, timedelta
from app.database.config import SessionLocal, engine 
from app.models.insurance import Base, UserModel, VehicleModel, InsuranceModel, ApplicationModel, PolicyDocument, ApplicationStatus

# Connect to Database Engine
session = SessionLocal()()

def seed_insurance_ecosystem():
    print("🚀 --- Initializing Polici Database Seed Script ---")
    
    # Clean drop & create for safe script reruns
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # -------------------------------------------------------------------------
    # STEP 1: Seed Static Public Knowledge & RAG Documents (fed by Admin)
    # -------------------------------------------------------------------------
    health_doc = PolicyDocument(
        document_name="POL-HEALTH-001_Master_Terms.pdf",
        document_text="Premium Health Secure Plus\n\nComprehensive global medical coverage including specialized treatments. Standard exclusions: Cosmetic procedures, self-inflicted injuries, experimental drugs."
    )
    auto_doc = PolicyDocument(
        document_name="POL-AUTO-771_Fleet_Provisions.pdf",
        document_text="Executive Fleet Protection\n\nPremium liability and collision coverage for high-value corporate assets. Excluded Perils: Street racing, track racing events, unlisted commercial haulage, modifications without prior endorsement. Accessories modification sub-limit capped strictly at 50000."
    )
    session.add_all([health_doc, auto_doc])
    session.commit()

    # -------------------------------------------------------------------------
    # STEP 2: Create the 8 Distinct Testing Users
    # -------------------------------------------------------------------------
    users = [
        UserModel(full_name="Alex Riveira (Void Slate)", email="alex.void@polici.in"),          # User 1
        UserModel(full_name="Rahul Sharma (Straight Denied)", email="rahul.denied@polici.in"), # User 2
        UserModel(full_name="Priya Patel (Mixed Fleet)", email="priya.mixed@polici.in"),        # User 3
        UserModel(full_name="Amit Verma (SQL Type Mismatch)", email="amit.sql@polici.in"),      # User 4
        UserModel(full_name="Karan Malhotra (RAG Excluded Peril)", email="karan.rag@polici.in"),# User 5
        UserModel(full_name="Sneha Rao (RAG Aggregation Cap)", email="sneha.math@polici.in"),  # User 6
        UserModel(full_name="Vikram Singh (Metadata Lapsed)", email="vikram.time@polici.in"),   # User 7
        UserModel(full_name="Ananya Iyer (Perfect Approval)", email="ananya.pass@polici.in")    # User 8
    ]
    session.add_all(users)
    session.commit() # Commits users to extract generated integer IDs

    # -------------------------------------------------------------------------
    # STEP 3: Create Underlying Insured Assets (Vehicles)
    # -------------------------------------------------------------------------
    vehicles = [
        # Linked to Rahul (User 2)
        VehicleModel(registration_number="MH-15-AB-1234", vehicle_type="2-wheeler", make="Yamaha", model="R15 V4", year=2024, user_id=users[1].id),
        # Linked to Priya (User 3) - Bike & Car
        VehicleModel(registration_number="MH-15-XY-9999", vehicle_type="2-wheeler", make="Royal Enfield", model="Classic 350", year=2023, user_id=users[2].id),
        VehicleModel(registration_number="MH-15-JK-5555", vehicle_type="4-wheeler", make="Tata", model="Nexon EV", year=2025, fuel_type="EV", user_id=users[2].id),
        # Linked to Amit (User 4)
        VehicleModel(registration_number="MH-15-QQ-1111", vehicle_type="4-wheeler", make="Mahindra", model="Thar", year=2023, user_id=users[3].id),
        # Linked to Karan (User 5)
        VehicleModel(registration_number="MH-15-ZZ-8888", vehicle_type="4-wheeler", make="Hyundai", model="Creta", year=2024, user_id=users[4].id),
        # Linked to Sneha (User 6)
        VehicleModel(registration_number="MH-15-MM-3333", vehicle_type="4-wheeler", make="Maruti", model="Swift", year=2022, user_id=users[5].id),
        # Linked to Vikram (User 7)
        VehicleModel(registration_number="MH-15-LL-7777", vehicle_type="4-wheeler", make="Honda", model="City", year=2021, user_id=users[6].id),
        # Linked to Ananya (User 8)
        VehicleModel(registration_number="MH-15-AA-0001", vehicle_type="4-wheeler", make="BMW", model="3 Series", year=2025, user_id=users[7].id)
    ]
    session.add_all(vehicles)
    session.commit()

    # -------------------------------------------------------------------------
    # STEP 4: Seed Core Insurance Products Templates (linked to instances)
    # -------------------------------------------------------------------------
    insurances = [
        # Standard Health Template
        InsuranceModel(policy_id="POL-HEALTH-001", title="Premium Health Secure Plus", coverage_details="Comprehensive global medical coverage including specialized treatments. Standard exclusions: Cosmetic procedures, self-inflicted injuries, experimental drugs.", user_id=users[7].id, vehicle_id=None),
        # Standard Fleet Auto Template
        InsuranceModel(policy_id="POL-AUTO-771", title="Executive Fleet Protection", coverage_details="Premium liability and collision coverage for high-value corporate assets. Excluded Perils: Street racing, track racing events, unlisted commercial haulage, modifications without prior endorsement. Accessories modification sub-limit capped strictly at 50000.", user_id=users[7].id, vehicle_id=vehicles[7].id)
    ]
    session.add_all(insurances)
    session.commit()

    # Reuse templates for specific user contexts
    priya_car_ins = InsuranceModel(policy_id="POL-AUTO-771-P3C", title="Executive Fleet Protection (Car)", coverage_details=insurances[1].coverage_details, user_id=users[2].id, vehicle_id=vehicles[2].id)
    priya_bike_ins = InsuranceModel(policy_id="POL-AUTO-771-P3B", title="Executive Fleet Protection (Bike)", coverage_details=insurances[1].coverage_details, user_id=users[2].id, vehicle_id=vehicles[1].id)
    sneha_ins = InsuranceModel(policy_id="POL-AUTO-771-S6", title="Swift Protection Package", coverage_details=insurances[1].coverage_details, user_id=users[5].id, vehicle_id=vehicles[5].id)
    
    session.add_all([priya_car_ins, priya_bike_ins, sneha_ins])
    session.commit()

    # -------------------------------------------------------------------------
    # STEP 5: Seed Core Application Flows (Mapping the 8 Scenarios)
    # -------------------------------------------------------------------------
    
    # USER 1: Pure Void Slate. No Applications seeded.
    
    # USER 2: The Clean Rejection (Basic Rule Engine failure)
    app_user2 = ApplicationModel(
        application_id="APP-RHL-002",
        status=ApplicationStatus.DENIED,
        status_code=403,
        denial_tags='["UNDERAGE_APPLICANT", "INSUFFICIENT_CREDIT"]',
        user_id=users[1].id,
        insurance_id=insurances[1].id
    )

    # USER 3: Mixed Fleet (Bike Rejected, Car Approved)
    app_user3_bike = ApplicationModel(
        application_id="APP-PRY-B01",
        status=ApplicationStatus.DENIED,
        status_code=422,
        denial_tags='["VEHICLE_AGE_LIMIT_EXCEEDED"]',
        user_id=users[2].id,
        insurance_id=priya_bike_ins.id
    )
    app_user3_car = ApplicationModel(
        application_id="APP-PRY-C02",
        status=ApplicationStatus.APPROVED,
        status_code=200,
        denial_tags=None,
        user_id=users[2].id,
        insurance_id=priya_car_ins.id
    )

    # USER 4: Structural SQL Rejection (Filing a Health claim layout directly onto an Auto schema instance)
    app_user4 = ApplicationModel(
        application_id="APP-AMT-004",
        status=ApplicationStatus.DENIED,
        status_code=400,
        denial_tags='["POLICY_TYPE_MISMATCH", "INVALID_SCHEMA_LINK"]', # SQL Interceptor instantly fails this
        user_id=users[3].id,
        insurance_id=insurances[1].id # Direct auto link while asking for clinical records
    )

    # USER 5: RAG Document Exception Rejection (Excluded Peril fine-print lookup validation)
    app_user5 = ApplicationModel(
        application_id="APP-KRN-005",
        status=ApplicationStatus.DENIED,
        status_code=412,
        denial_tags='["EXCLUDED_PERIL", "TRACK_RACING_INCIDENT"]', # Text-based check inside PDF details
        user_id=users[4].id,
        insurance_id=insurances[1].id
    )

    # USER 6: Aggregation RAG Rejection (Lookup + Math). User has past approvals that exhaust the active caps.
    past_approved_claim_1 = ApplicationModel(
        application_id="APP-SNH-OLD1",
        status=ApplicationStatus.APPROVED,
        status_code=200,
        user_id=users[5].id,
        insurance_id=sneha_ins.id
    )
    past_approved_claim_2 = ApplicationModel(
        application_id="APP-SNH-OLD2",
        status=ApplicationStatus.APPROVED,
        status_code=200,
        user_id=users[5].id,
        insurance_id=sneha_ins.id
    )
    current_rejected_claim = ApplicationModel(
        application_id="APP-SNH-NEW3",
        status=ApplicationStatus.DENIED,
        status_code=406,
        denial_tags='["MAX_LIMIT_EXCEEDED", "SUB_LIMIT_ACC_EXHAUSTED"]', # Sum calculations exceed 50,000 allowance rule
        user_id=users[5].id,
        insurance_id=sneha_ins.id
    )

    # USER 7: Metadata / Temporal Invalidity Rejection (Lapsed Timeline)
    app_user7 = ApplicationModel(
        application_id="APP-VKR-007",
        status=ApplicationStatus.DENIED,
        status_code=408,
        denial_tags='["POLICY_LAPSED", "EXPIRED_CONTRACT_WINDOW"]',
        status_changed_at=datetime.utcnow() - timedelta(days=90), # Tracks historical expiration frame
        user_id=users[6].id,
        insurance_id=insurances[1].id
    )

    # USER 8: The Pristine Acceptance Path
    app_user8 = ApplicationModel(
        application_id="APP-ANY-008",
        status=ApplicationStatus.APPROVED,
        status_code=200,
        denial_tags=None,
        user_id=users[7].id,
        insurance_id=insurances[0].id
    )

    session.add_all([
        app_user2, app_user3_bike, app_user3_car, app_user4, 
        app_user5, past_approved_claim_1, past_approved_claim_2, 
        current_rejected_claim, app_user7, app_user8
    ])
    session.commit()
    
    print("✅ --- Database Successfully Seeded with 8 Immersive Test Profiles! ---")

if __name__ == "__main__":
    seed_insurance_ecosystem()