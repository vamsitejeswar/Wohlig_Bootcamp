from pydantic import BaseModel, Field
from typing import Optional


class PANExtraction(BaseModel):
    pan_number: Optional[str] = Field(
        default=None,
        description="PAN card number"
    )

    full_name: Optional[str] = Field(
        default=None,
        description="Full name on PAN card"
    )

    father_name: Optional[str] = Field(
        default=None,
        description="Father name on PAN card"
    )

    dob: Optional[str] = Field(
        default=None,
        description="Date of birth"
    )

    confidence: float = Field(
        default=0.0,
        description="Confidence score between 0 and 1"
    )