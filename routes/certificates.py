import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from config import CERTIFICATES_DIR
from models.certificate import Certificate, CertificateStatus
from models.verification import Verification, VerificationStatus, VerificationResult
from models.instrument import Instrument
from models.user import User, UserRole
from schemas.certificate import CertificateOut
from routes.auth import get_current_user, require_role
from services.certificate_service import create_certificate

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.post("/generate/{verification_id}")
def generate_certificate(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.INSPECTOR)),
):
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.status != VerificationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Verification must be completed before generating certificate")

    if verification.result != VerificationResult.PASS:
        raise HTTPException(status_code=400, detail="Cannot generate certificate for a failed verification")

    existing_cert = (
        db.query(Certificate).filter(Certificate.verification_id == verification.id).first()
    )
    if existing_cert:
        raise HTTPException(status_code=409, detail="Certificate already exists for this verification")

    certificate = create_certificate(db, verification)
    return {
        "message": "Certificate generated successfully",
        "certificate_id": certificate.id,
        "certificate_number": certificate.certificate_number,
    }


@router.get("/", response_model=list[CertificateOut])
def list_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Certificate)

    if current_user.role == UserRole.OWNER:
        owner_instrument_ids = [
            i.id
            for i in db.query(Instrument).filter(Instrument.owner_id == current_user.id).all()
        ]
        query = query.filter(Certificate.instrument_id.in_(owner_instrument_ids))
    elif current_user.role == UserRole.INSPECTOR:
        pass
    elif current_user.role == UserRole.ADMIN:
        pass
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    return query.order_by(Certificate.created_at.desc()).all()


@router.get("/{certificate_id}", response_model=CertificateOut)
def get_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if current_user.role == UserRole.OWNER:
        instrument = db.query(Instrument).filter(Instrument.id == cert.instrument_id).first()
        if not instrument or instrument.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    return cert


@router.get("/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if current_user.role == UserRole.OWNER:
        instrument = db.query(Instrument).filter(Instrument.id == cert.instrument_id).first()
        if not instrument or instrument.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    if not cert.pdf_path or not os.path.exists(cert.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    real_cert_dir = os.path.realpath(CERTIFICATES_DIR)
    real_pdf_path = os.path.realpath(cert.pdf_path)
    if not real_pdf_path.startswith(real_cert_dir):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        cert.pdf_path,
        media_type="application/pdf",
        filename=f"{cert.certificate_number}.pdf",
    )
