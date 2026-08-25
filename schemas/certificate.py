from pydantic import BaseModel, ConfigDict
from enum import Enum
from datetime import datetime
from typing import Optional


class CertificateStatus(str, Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    certificate_number: str
    instrument_id: int
    verification_id: int
    issued_to: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: CertificateStatus
    pdf_path: Optional[str] = None


class PublicCertificateOut(BaseModel):
    certificate_number: str
    instrument_id: Optional[int] = None
    instrument_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    issue_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: str
    result: Optional[str] = None
