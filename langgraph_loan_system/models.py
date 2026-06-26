from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    customer_id: str = "CUST-001"
    name: str = "Demo Customer"
    age: int = 30
    monthly_income: float = 85000
    existing_monthly_emi: float = 18000
    requested_amount: float = 700000
    tenure_months: int = 48
    credit_score: int = 735
    employment_type: str = "salaried"
    documents: Dict[str, bool] = Field(
        default_factory=lambda: {
            "pan": True,
            "aadhaar": True,
            "bank_statement": True,
        }
    )


class LoanDecisionResponse(BaseModel):
    decision: str
    reason: str
    approved_amount: float = 0
    interest_rate: float = 0
    emi: float = 0
    foir_percent: float = 0
    sanction_letter_path: Optional[str] = None
    pipeline: List[str]
    state: Dict[str, Any]


class LoanState(TypedDict, total=False):
    profile: Dict[str, Any]
    pipeline: List[str]
    profile_status: str
    credit_status: str
    document_status: str
    underwriting_status: str
    decision: str
    reason: str
    approved_amount: float
    interest_rate: float
    emi: float
    foir_percent: float
    sanction_letter_path: str
    errors: List[str]

