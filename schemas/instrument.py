from pydantic import BaseModel
from enum import Enum
from datetime import datetime

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
    manufacturer: str | None = None
    model_number: str | None = None
    serial_number: str
    capacity: str | None = None
    accuracy_class: str | None = None
    location: str | None = None

class InstrumentCreate(InstrumentBase):
    pass

class InstrumentOut(InstrumentBase):
    id: int
    owner_id: int
    status: InstrumentStatus
    created_at: datetime

    class Config:
        orm_mode = True
