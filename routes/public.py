from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.certificate import Certificate, CertificateStatus
from models.instrument import Instrument
from models.verification import Verification

router = APIRouter(prefix="/api/public", tags=["Public Verification"])


@router.get("/verify/{certificate_number}")
def public_verify_certificate(certificate_number: str, db: Session = Depends(get_db)):
    cert = (
        db.query(Certificate)
        .filter(Certificate.certificate_number == certificate_number)
        .first()
    )
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if cert.valid_until and cert.valid_until < datetime.now():
        if cert.status == CertificateStatus.VALID:
            cert.status = CertificateStatus.EXPIRED
            db.commit()

    instrument = db.query(Instrument).filter(Instrument.id == cert.instrument_id).first()
    verification = db.query(Verification).filter(Verification.id == cert.verification_id).first()

    result = None
    if verification:
        result = verification.result.value if verification.result else None

    return {
        "certificate_number": cert.certificate_number,
        "instrument_id": instrument.instrument_id if instrument else None,
        "instrument_type": instrument.instrument_type if instrument else None,
        "manufacturer": instrument.manufacturer if instrument else None,
        "model_number": instrument.model_number if instrument else None,
        "serial_number": instrument.serial_number if instrument else None,
        "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
        "valid_until": cert.valid_until.isoformat() if cert.valid_until else None,
        "status": cert.status.value,
        "result": result,
    }
