from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from database import get_db
from models.verification import Verification, VerificationStatus, VerificationResult
from models.instrument import Instrument, InstrumentStatus
from models.user import User, UserRole
from schemas.verification import (
    VerificationRequest,
    VerificationAssign,
    VerificationComplete,
    VerificationOut,
)
from routes.auth import get_current_user, require_role

router = APIRouter(prefix="/api/verification", tags=["Verification"])


@router.post("/request")
def request_verification(
    data: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OWNER)),
):
    instrument = (
        db.query(Instrument)
        .filter(Instrument.id == data.instrument_id, Instrument.owner_id == current_user.id)
        .first()
    )
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found or not owned by you")

    existing_pending = (
        db.query(Verification)
        .filter(
            Verification.instrument_id == instrument.id,
            Verification.status.in_([VerificationStatus.PENDING, VerificationStatus.IN_PROGRESS]),
        )
        .first()
    )
    if existing_pending:
        raise HTTPException(status_code=409, detail="A pending verification already exists for this instrument")

    instrument.status = InstrumentStatus.PENDING_VERIFICATION
    verification = Verification(
        instrument_id=instrument.id,
        status=VerificationStatus.PENDING,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return {"message": "Verification requested", "verification_id": verification.id}


@router.get("/", response_model=list[VerificationOut])
def list_verifications(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Verification)

    if current_user.role == UserRole.OWNER:
        owner_instrument_ids = [
            i.id for i in db.query(Instrument).filter(Instrument.owner_id == current_user.id).all()
        ]
        query = query.filter(Verification.instrument_id.in_(owner_instrument_ids))
    elif current_user.role == UserRole.INSPECTOR:
        query = query.filter(Verification.inspector_id == current_user.id)
    elif current_user.role == UserRole.ADMIN:
        pass
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    if status:
        query = query.filter(Verification.status == status)

    return query.order_by(Verification.created_at.desc()).all()


@router.get("/{verification_id}", response_model=VerificationOut)
def get_verification(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if current_user.role == UserRole.OWNER:
        instrument = db.query(Instrument).filter(Instrument.id == verification.instrument_id).first()
        if not instrument or instrument.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.INSPECTOR:
        if verification.inspector_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not assigned to this verification")

    return verification


@router.put("/{verification_id}/assign")
def assign_inspector(
    verification_id: int,
    data: VerificationAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.status != VerificationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only assign inspectors to pending verifications")

    inspector = db.query(User).filter(User.id == data.inspector_id, User.role == UserRole.INSPECTOR).first()
    if not inspector:
        raise HTTPException(status_code=404, detail="Inspector not found")

    verification.inspector_id = data.inspector_id
    verification.status = VerificationStatus.IN_PROGRESS
    db.commit()
    db.refresh(verification)
    return {"message": "Inspector assigned", "verification_id": verification.id}


@router.put("/{verification_id}/complete")
def complete_verification(
    verification_id: int,
    data: VerificationComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.INSPECTOR)),
):
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.inspector_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to this verification")

    if verification.status != VerificationStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Verification is not in progress")

    if data.expected_value == 0:
        raise HTTPException(status_code=400, detail="Expected value cannot be zero")

    deviation = abs(data.measured_value - data.expected_value) / abs(data.expected_value) * 100
    result = VerificationResult.PASS if deviation <= data.tolerance_limit else VerificationResult.FAIL

    verification.reference_standard_used = data.reference_standard_used
    verification.expected_value = data.expected_value
    verification.measured_value = data.measured_value
    verification.tolerance_limit = data.tolerance_limit
    verification.deviation_percentage = round(deviation, 6)
    verification.result = result
    verification.remarks = data.remarks
    verification.inspection_date = datetime.now(timezone.utc)
    verification.status = VerificationStatus.COMPLETED

    instrument = db.query(Instrument).filter(Instrument.id == verification.instrument_id).first()
    if instrument:
        if result == VerificationResult.FAIL:
            instrument.status = InstrumentStatus.FAILED
        else:
            instrument.status = InstrumentStatus.VERIFIED

    db.commit()
    db.refresh(verification)
    return {
        "verification_id": verification.id,
        "result": result.value,
        "deviation_percentage": round(deviation, 6),
    }


@router.post("/{verification_id}/result")
def submit_verification_result(
    verification_id: int,
    data: VerificationComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.INSPECTOR)),
):
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.inspector_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to this verification")

    if verification.status != VerificationStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Verification is not in progress")

    if data.expected_value == 0:
        raise HTTPException(status_code=400, detail="Expected value cannot be zero")

    deviation = abs(data.measured_value - data.expected_value) / abs(data.expected_value) * 100
    result = VerificationResult.PASS if deviation <= data.tolerance_limit else VerificationResult.FAIL

    verification.reference_standard_used = data.reference_standard_used
    verification.expected_value = data.expected_value
    verification.measured_value = data.measured_value
    verification.tolerance_limit = data.tolerance_limit
    verification.deviation_percentage = round(deviation, 6)
    verification.result = result
    verification.remarks = data.remarks
    verification.inspection_date = datetime.now(timezone.utc)
    verification.status = VerificationStatus.COMPLETED

    instrument = db.query(Instrument).filter(Instrument.id == verification.instrument_id).first()
    if instrument:
        if result == VerificationResult.FAIL:
            instrument.status = InstrumentStatus.FAILED
        else:
            instrument.status = InstrumentStatus.VERIFIED

    db.commit()
    db.refresh(verification)
    return {
        "verification_id": verification.id,
        "result": result.value,
        "deviation_percentage": round(deviation, 6),
    }
