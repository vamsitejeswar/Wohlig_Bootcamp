from pydantic import BaseModel, EmailStr, Field


class Address(BaseModel):
    city: str
    pincode: str = Field(..., min_length=6, max_length=6)


class ContactCard(BaseModel):
    name: str
    email: str
    phone: str = Field(..., min_length=10, max_length=10)
    address: Address