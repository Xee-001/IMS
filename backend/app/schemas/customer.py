import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class CustomerCreate(BaseModel):
    customer_code: str
    name: str
    email: str
    phone: str

    @field_validator("customer_code")
    @classmethod
    def code_must_not_be_empty(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Customer code cannot be empty")
        return v

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email format")
        return v


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().lower()
            if not _EMAIL_RE.match(v):
                raise ValueError("Invalid email format")
        return v


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_code: str
    name: str
    email: str
    phone: str
