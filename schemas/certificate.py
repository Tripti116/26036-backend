from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class CertificateStatus(str, Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class CertificateOut(BaseModel):
    id: int
    certificate_number: str
    instrument_id: int
    verification_id: int
    issued_to: str
    issued_by: str
    issue_date: datetime
    valid_until: datetime | None
    status: CertificateStatus

    class Config:
        orm_mode = True
