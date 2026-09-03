from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class CustomerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"


class CustomerResponse(BaseModel):
    id: str
    company_name: str
    company_type: str
    tax_code: str
    address: str
    contact_name: str
    contact_email: str
    contact_phone: str
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
