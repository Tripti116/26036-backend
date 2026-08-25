from pydantic import BaseModel, ConfigDict
from enum import Enum
from datetime import datetime
from typing import Optional


class VerificationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class VerificationRequest(BaseModel):
    instrument_id: int


class VerificationAssign(BaseModel):
    inspector_id: int


class VerificationComplete(BaseModel):
    reference_standard_used: str
    expected_value: float
    measured_value: float
    tolerance_limit: float
    remarks: Optional[str] = None


class VerificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instrument_id: int
    inspector_id: Optional[int] = None
    request_date: Optional[datetime] = None
    inspection_date: Optional[datetime] = None
    reference_standard_used: Optional[str] = None
    measured_value: Optional[float] = None
    expected_value: Optional[float] = None
    deviation_percentage: Optional[float] = None
    tolerance_limit: Optional[float] = None
    result: Optional[VerificationResult] = None
    remarks: Optional[str] = None
    status: VerificationStatus
    created_at: Optional[datetime] = None
