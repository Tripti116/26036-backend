from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class CertificateStatus(str, enum.Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    certificate_number = Column(String, unique=True, nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    verification_id = Column(Integer, ForeignKey("verifications.id"))
    issued_to = Column(String)
    issued_by = Column(String)
    issue_date = Column(DateTime, server_default=func.now())
    valid_until = Column(DateTime)
    status = Column(Enum(CertificateStatus), default=CertificateStatus.VALID)
    qr_token = Column(String, unique=True)
    pdf_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
