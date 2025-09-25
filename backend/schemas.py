from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re

class ContactInquiryBase(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    preferred_contact_method: str
    message: Optional[str] = None

    @validator('preferred_contact_method')
    def validate_contact_method(cls, v):
        if v not in ['Phone', 'Email', 'WhatsApp']:
            raise ValueError('Preferred contact method must be Phone, Email, or WhatsApp')
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic international phone validation
        pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(pattern, v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")):
            raise ValueError('Invalid phone number format')
        return v

class ContactInquiryCreate(ContactInquiryBase):
    pass

class ContactInquiryResponse(ContactInquiryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Add these new schemas AFTER ContactInquiryResponse is defined
class ContactStats(BaseModel):
    period: str
    total_contacts: int
    contact_methods: dict
    recent_contacts_count: int
    recent_contacts: List[dict]

class ContactExport(BaseModel):
    format: str
    count: Optional[int] = None
    data: Optional[str] = None
    filename: Optional[str] = None
    contacts: Optional[List[ContactInquiryResponse]] = None

class SearchResponse(BaseModel):
    search_term: str
    field: str
    count: int
    results: List[ContactInquiryResponse]

class PaginatedResponse(BaseModel):
    skip: int
    limit: int
    total: int
    contacts: List[ContactInquiryResponse]

class ContactStats(BaseModel):
    period: str
    total_contacts: int
    contact_methods: dict
    recent_contacts_count: int
    recent_contacts: List[dict]

class ContactExport(BaseModel):
    format: str
    count: Optional[int] = None
    data: Optional[str] = None
    filename: Optional[str] = None
    contacts: Optional[List[ContactInquiryResponse]] = None

class SearchResponse(BaseModel):
    search_term: str
    field: str
    count: int
    results: List[ContactInquiryResponse]

class PaginatedResponse(BaseModel):
    skip: int
    limit: int
    total: int
    contacts: List[ContactInquiryResponse]

class ContactInquiryBase(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    preferred_contact_method: str
    message: Optional[str] = None

    @validator('preferred_contact_method')
    def validate_contact_method(cls, v):
        if v not in ['Phone', 'Email', 'WhatsApp']:
            raise ValueError('Preferred contact method must be Phone, Email, or WhatsApp')
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic international phone validation
        pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(pattern, v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")):
            raise ValueError('Invalid phone number format')
        return v

class ContactInquiryCreate(ContactInquiryBase):
    pass

class ContactInquiryResponse(ContactInquiryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True