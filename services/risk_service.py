from datetime import datetime
from sqlalchemy.orm import Session
from models.instrument import Instrument, InstrumentStatus
from models.verification import Verification, VerificationResult, VerificationStatus
from models.certificate import Certificate, CertificateStatus


def calculate_risk_score(db: Session, instrument: Instrument) -> dict:
    """
    Prototype risk-scoring service.
    NOT an official government formula. Modular so an ML model can replace it later.
    Returns risk_score (0-100) and risk_level (LOW/MEDIUM/HIGH).
    """
    score = 0

    verifications = (
        db.query(Verification)
        .filter(Verification.instrument_id == instrument.id)
        .all()
    )

    failed_count = sum(
        1 for v in verifications if v.result == VerificationResult.FAIL
    )
    score += min(failed_count * 15, 45)

    completed = [v for v in verifications if v.status == VerificationStatus.COMPLETED]
    if completed:
        latest = max(completed, key=lambda v: v.inspection_date or datetime.min)
        if latest.deviation_percentage is not None:
            if latest.deviation_percentage > 5:
                score += 25
            elif latest.deviation_percentage > 2:
                score += 15
            elif latest.deviation_percentage > 1:
                score += 5

    if instrument.purchase_date:
        age_years = (datetime.now() - instrument.purchase_date).days / 365.25
        if age_years > 10:
            score += 15
        elif age_years > 5:
            score += 8

    if instrument.next_verification_date and instrument.next_verification_date < datetime.now():
        overdue_days = (datetime.now() - instrument.next_verification_date).days
        if overdue_days > 180:
            score += 20
        elif overdue_days > 90:
            score += 12
        elif overdue_days > 30:
            score += 5

    score = min(score, 100)

    if score >= 60:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "factors": {
            "failed_verifications": failed_count,
            "latest_deviation": completed[-1].deviation_percentage if completed else None,
            "instrument_age_years": round(
                (datetime.now() - instrument.purchase_date).days / 365.25, 1
            ) if instrument.purchase_date else None,
            "overdue_verification": bool(
                instrument.next_verification_date and instrument.next_verification_date < datetime.now()
            ),
        },
    }
