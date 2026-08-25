from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import os
from database import get_db
from models.certificate import Certificate
from routes.auth import get_current_user

router = APIRouter(prefix="/api/certificates", tags=["certificates"])

@router.get("/public/verify/{certificate_number}")
def public_verify(certificate_number: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.certificate_number == certificate_number).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {
        "certificate_number": cert.certificate_number,
        "instrument_id": cert.instrument_id,
        "verification_id": cert.verification_id,
        "issue_date": cert.issue_date,
        "valid_until": cert.valid_until,
        "status": cert.status,
    }

@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if not cert.pdf_path or not os.path.exists(cert.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(cert.pdf_path, filename=f"{cert.certificate_number}.pdf")
