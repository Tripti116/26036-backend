from pydantic import BaseModel, ConfigDict
from enum import Enum
from datetime import datetime
from typing import Optional


class InstrumentStatus(str, Enum):
    REGISTERED = "REGISTERED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


class InstrumentBase(BaseModel):
    instrument_id: str
    instrument_type: str
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: str
    capacity: Optional[str] = None
    accuracy_class: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[datetime] = None


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    instrument_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    capacity: Optional[str] = None
    accuracy_class: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[datetime] = None
    last_verification_date: Optional[datetime] = None
    next_verification_date: Optional[datetime] = None
    status: Optional[InstrumentStatus] = None


class InstrumentOut(InstrumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    status: InstrumentStatus
    last_verification_date: Optional[datetime] = None
    next_verification_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
