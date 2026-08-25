from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class VerificationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"

class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class VerificationBase(BaseModel):
    instrument_id: int
    inspector_id: int | None = None
    reference_standard_used: str | None = None
    measured_value: float | None = None
    expected_value: float | None = None
    tolerance_limit: float | None = None
    remarks: str | None = None

class VerificationOut(VerificationBase):
    id: int
    deviation_percentage: float | None = None
    result: VerificationResult | None = None
    status: VerificationStatus
    created_at: datetime

    class Config:
        orm_mode = True
