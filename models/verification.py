from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class VerificationResult(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    request_date = Column(DateTime, server_default=func.now())
    inspection_date = Column(DateTime)
    reference_standard_used = Column(String)
    measured_value = Column(Float)
    expected_value = Column(Float)
    deviation_percentage = Column(Float)
    tolerance_limit = Column(Float)
    result = Column(Enum(VerificationResult))
    remarks = Column(String)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    instrument = relationship("Instrument", back_populates="verifications")
    inspector = relationship("User", backref="verifications")
    certificate = relationship("Certificate", back_populates="verification", uselist=False)
