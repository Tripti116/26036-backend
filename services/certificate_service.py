import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

from config import CERTIFICATES_DIR, PUBLIC_BASE_URL
from models.certificate import Certificate, CertificateStatus
from models.verification import Verification, VerificationStatus, VerificationResult
from models.instrument import Instrument, InstrumentStatus
from models.user import User
from services.qr_service import generate_qr_image, get_verify_url


def generate_certificate_number(db: Session) -> str:
    year = datetime.now().year
    last_cert = (
        db.query(Certificate)
        .filter(Certificate.certificate_number.like(f"CERT-{year}-%"))
        .order_by(Certificate.id.desc())
        .first()
    )
    if last_cert:
        last_num = int(last_cert.certificate_number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f"CERT-{year}-{next_num:06d}"


def generate_certificate_pdf(cert_data: dict, qr_path: str, output_path: str) -> str:
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 72

    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 80, "Certificate of Verification")

    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 100, "Weighing & Measuring Instruments Verification System")
    c.drawCentredString(width / 2, height - 115, "Smart India Hackathon 2026 - SIH26036")

    y = height - 160
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, f"Certificate Number: {cert_data['certificate_number']}")
    y -= 30

    c.setFont("Helvetica", 11)
    fields = [
        ("Instrument ID", cert_data.get("instrument_id_text", "")),
        ("Instrument Type", cert_data.get("instrument_type", "")),
        ("Manufacturer", cert_data.get("manufacturer", "")),
        ("Model Number", cert_data.get("model_number", "")),
        ("Serial Number", cert_data.get("serial_number", "")),
        ("Owner", cert_data.get("owner_name", "")),
        ("Verification Date", cert_data.get("verification_date", "")),
        ("Issue Date", cert_data.get("issue_date", "")),
        ("Valid Until", cert_data.get("valid_until", "")),
        ("Inspector", cert_data.get("inspector_name", "")),
        ("Expected Value", cert_data.get("expected_value", "")),
        ("Measured Value", cert_data.get("measured_value", "")),
        ("Deviation (%)", cert_data.get("deviation_percentage", "")),
        ("Tolerance Limit (%)", cert_data.get("tolerance_limit", "")),
        ("Result", cert_data.get("result", "")),
        ("Remarks", cert_data.get("remarks", "")),
    ]

    for label, value in fields:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(margin + 150, y, str(value))
        y -= 22

    if qr_path and os.path.exists(qr_path):
        c.drawImage(qr_path, margin, y - 100, width=120, height=120)
        c.setFont("Helvetica", 8)
        c.drawString(margin, y - 115, "Scan to verify this certificate")

    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width / 2, 40, "This is a system-generated certificate. Prototype for SIH2026.")
    c.drawCentredString(width / 2, 28, "Tolerance values are configurable and NOT official legal standards.")

    c.save()
    return output_path


def create_certificate(db: Session, verification: Verification, base_url: str = None) -> Certificate:
    if base_url is None:
        base_url = PUBLIC_BASE_URL
    instrument = db.query(Instrument).filter(Instrument.id == verification.instrument_id).first()
    inspector = db.query(User).filter(User.id == verification.inspector_id).first()
    owner = db.query(User).filter(User.id == instrument.owner_id).first()

    certificate_number = generate_certificate_number(db)
    issue_date = datetime.now()
    valid_until = issue_date + timedelta(days=365)

    qr_path = generate_qr_image(certificate_number, base_url)

    os.makedirs(CERTIFICATES_DIR, exist_ok=True)
    pdf_filename = f"{certificate_number}.pdf"
    pdf_path = os.path.join(CERTIFICATES_DIR, pdf_filename)

    cert_data = {
        "certificate_number": certificate_number,
        "instrument_id_text": instrument.instrument_id,
        "instrument_type": instrument.instrument_type,
        "manufacturer": instrument.manufacturer or "",
        "model_number": instrument.model_number or "",
        "serial_number": instrument.serial_number,
        "owner_name": owner.full_name if owner else "",
        "verification_date": verification.inspection_date.strftime("%Y-%m-%d") if verification.inspection_date else "",
        "issue_date": issue_date.strftime("%Y-%m-%d"),
        "valid_until": valid_until.strftime("%Y-%m-%d"),
        "inspector_name": inspector.full_name if inspector else "",
        "expected_value": str(verification.expected_value),
        "measured_value": str(verification.measured_value),
        "deviation_percentage": f"{verification.deviation_percentage:.4f}",
        "tolerance_limit": str(verification.tolerance_limit),
        "result": verification.result.value if verification.result else "",
        "remarks": verification.remarks or "",
    }

    generate_certificate_pdf(cert_data, qr_path, pdf_path)

    certificate = Certificate(
        certificate_number=certificate_number,
        instrument_id=instrument.id,
        verification_id=verification.id,
        issued_to=owner.full_name if owner else "",
        issued_by=inspector.full_name if inspector else "",
        issue_date=issue_date,
        valid_until=valid_until,
        status=CertificateStatus.VALID,
        qr_token=uuid.uuid4().hex,
        pdf_path=pdf_path,
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    instrument.status = InstrumentStatus.VERIFIED
    instrument.last_verification_date = verification.inspection_date
    instrument.next_verification_date = valid_until
    db.commit()

    return certificate
