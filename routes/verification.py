from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.verification import Verification, VerificationStatus, VerificationResult
from models.instrument import Instrument, InstrumentStatus
from models.user import UserRole
from routes.auth import get_current_user

router = APIRouter(prefix="/api/verification", tags=["verification"])

@router.post("/request")
def request_verification(instrument_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can request verification")
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id, Instrument.owner_id == current_user.id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    instrument.status = InstrumentStatus.PENDING_VERIFICATION
    verification = Verification(instrument_id=instrument.id, status=VerificationStatus.PENDING)
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return {"msg": "Verification requested", "verification_id": verification.id}

@router.put("/{verification_id}/result")
def submit_result(verification_id: int, expected_value: float, measured_value: float, tolerance_limit: float,
                  remarks: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != UserRole.INSPECTOR:
        raise HTTPException(status_code=403, detail="Only inspectors can submit results")
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    if expected_value == 0:
        raise HTTPException(status_code=400, detail="Expected value cannot be zero")
    deviation = abs(measured_value - expected_value) / expected_value * 100
    verification.expected_value = expected_value
    verification.measured_value = measured_value
    verification.tolerance_limit = tolerance_limit
    verification.deviation_percentage = deviation
    verification.remarks = remarks
    verification.status = VerificationStatus.COMPLETED
    verification.result = VerificationResult.PASS if deviation <= tolerance_limit else VerificationResult.FAIL
    db.commit()
    return {"result": verification.result, "deviation": deviation}
