from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.user import User, UserRole
from models.instrument import Instrument, InstrumentStatus
from models.verification import Verification, VerificationStatus, VerificationResult
from models.certificate import Certificate, CertificateStatus
from routes.auth import require_role

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_instruments = db.query(func.count(Instrument.id)).scalar() or 0

    pending_verifications = (
        db.query(func.count(Verification.id))
        .filter(Verification.status == VerificationStatus.PENDING)
        .scalar()
        or 0
    )
    in_progress_verifications = (
        db.query(func.count(Verification.id))
        .filter(Verification.status == VerificationStatus.IN_PROGRESS)
        .scalar()
        or 0
    )
    completed_verifications = (
        db.query(func.count(Verification.id))
        .filter(Verification.status == VerificationStatus.COMPLETED)
        .scalar()
        or 0
    )

    passed_instruments = (
        db.query(func.count(Instrument.id))
        .filter(Instrument.status == InstrumentStatus.VERIFIED)
        .scalar()
        or 0
    )
    failed_instruments = (
        db.query(func.count(Instrument.id))
        .filter(Instrument.status == InstrumentStatus.FAILED)
        .scalar()
        or 0
    )

    valid_certificates = (
        db.query(func.count(Certificate.id))
        .filter(Certificate.status == CertificateStatus.VALID)
        .scalar()
        or 0
    )
    expired_certificates = (
        db.query(func.count(Certificate.id))
        .filter(Certificate.status == CertificateStatus.EXPIRED)
        .scalar()
        or 0
    )
    revoked_certificates = (
        db.query(func.count(Certificate.id))
        .filter(Certificate.status == CertificateStatus.REVOKED)
        .scalar()
        or 0
    )

    users_by_role = (
        db.query(User.role, func.count(User.id))
        .group_by(User.role)
        .all()
    )

    instruments_by_status = (
        db.query(Instrument.status, func.count(Instrument.id))
        .group_by(Instrument.status)
        .all()
    )

    return {
        "total_users": total_users,
        "users_by_role": {role.value: count for role, count in users_by_role},
        "total_instruments": total_instruments,
        "instruments_by_status": {status.value: count for status, count in instruments_by_status},
        "pending_verifications": pending_verifications,
        "in_progress_verifications": in_progress_verifications,
        "completed_verifications": completed_verifications,
        "passed_instruments": passed_instruments,
        "failed_instruments": failed_instruments,
        "valid_certificates": valid_certificates,
        "expired_certificates": expired_certificates,
        "revoked_certificates": revoked_certificates,
    }
