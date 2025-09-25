from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class ContactInquiry(Base):
    __tablename__ = "contact_inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    preferred_contact_method = Column(String(20), nullable=False)  # Phone/Email/WhatsApp
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())