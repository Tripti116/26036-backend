from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.instrument import Instrument, InstrumentStatus
from models.verification import Verification, VerificationResult, VerificationStatus


def calculate_risk_score(db: Session, instrument: Instrument) -> dict:
    """
    Prototype risk-scoring service.
    NOT an official government formula. Modular so an ML model can replace it later.
    Returns risk_score (0-100), risk_level (LOW/MEDIUM/HIGH), and risk_factors as human-readable strings.
    """
    score = 0
    risk_factors = []

    verifications = (
        db.query(Verification)
        .filter(Verification.instrument_id == instrument.id)
        .all()
    )

    failed_count = sum(
        1 for v in verifications if v.result == VerificationResult.FAIL
    )
    if failed_count > 0:
        score += min(failed_count * 15, 45)
        risk_factors.append(f"Previous verification failure{'s' if failed_count > 1 else ''} ({failed_count})")

    completed = [v for v in verifications if v.status == VerificationStatus.COMPLETED]
    latest_deviation = None
    if completed:
        latest = max(completed, key=lambda v: v.inspection_date or datetime.min.replace(tzinfo=timezone.utc))
        latest_deviation = latest.deviation_percentage
        if latest.deviation_percentage is not None:
            if latest.deviation_percentage > 5:
                score += 25
                risk_factors.append(f"High measurement deviation ({latest.deviation_percentage:.2f}%)")
            elif latest.deviation_percentage > 2:
                score += 15
                risk_factors.append(f"Moderate measurement deviation ({latest.deviation_percentage:.2f}%)")
            elif latest.deviation_percentage > 1:
                score += 5

    if instrument.purchase_date:
        purchase_date = instrument.purchase_date
        if purchase_date.tzinfo is None:
            purchase_date = purchase_date.replace(tzinfo=timezone.utc)
        age_years = (datetime.now(timezone.utc) - purchase_date).days / 365.25
        if age_years > 10:
            score += 15
            risk_factors.append(f"Instrument age over 10 years ({age_years:.1f} years)")
        elif age_years > 5:
            score += 8

    if instrument.next_verification_date:
        next_ver = instrument.next_verification_date
        if next_ver.tzinfo is None:
            next_ver = next_ver.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if next_ver < now:
            overdue_days = (now - next_ver).days
            if overdue_days > 180:
                score += 20
                risk_factors.append(f"Verification overdue by {overdue_days} days")
            elif overdue_days > 90:
                score += 12
                risk_factors.append(f"Verification overdue by {overdue_days} days")
            elif overdue_days > 30:
                score += 5
                risk_factors.append(f"Verification overdue by {overdue_days} days")

    score = min(score, 100)

    if score >= 60:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "instrument_id": instrument.instrument_id,
        "risk_score": score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
    }
