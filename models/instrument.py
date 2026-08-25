from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class InstrumentStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    instrument_type = Column(String, nullable=False)
    manufacturer = Column(String)
    model_number = Column(String)
    serial_number = Column(String, unique=True, nullable=False)
    capacity = Column(String)
    accuracy_class = Column(String)
    location = Column(String)
    purchase_date = Column(DateTime)
    last_verification_date = Column(DateTime)
    next_verification_date = Column(DateTime)
    status = Column(Enum(InstrumentStatus), default=InstrumentStatus.REGISTERED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", backref="instruments")
