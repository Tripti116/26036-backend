from pydantic import BaseModel, EmailStr
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    INSPECTOR = "INSPECTOR"
    OWNER = "OWNER"

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    role: UserRole
    organization: str | None = None
    address: str | None = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True
