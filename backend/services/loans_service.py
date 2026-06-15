import json
import os
from datetime import datetime
from typing import Dict, Any, List

LOANS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "loans.json")

class LoansService:
    """Service to manage approved loans"""
    
    def __init__(self):
        self.loans: list = []
        self.load_loans()
    
    def load_loans(self):
        """Load loans from JSON file"""
        if os.path.exists(LOANS_FILE):
            try:
                with open(LOANS_FILE, 'r') as f:
                    self.loans = json.load(f)
            except:
                self.loans = []
        else:
            self.loans = []
    
    def save_loans(self):
        """Save loans to JSON file"""
        os.makedirs(os.path.dirname(LOANS_FILE), exist_ok=True)
        with open(LOANS_FILE, 'w') as f:
            json.dump(self.loans, f, indent=2)
    
    def create_loan(self, 
                   customer_id: str,
                   customer_name: str,
                   session_id: str,
                   approved_amount: float,
                   interest_rate: float,
                   tenure_months: int,
                   approval_type: str,  # "preapproved_instant" or "evaluated"
                   emi: float = None) -> Dict[str, Any]:
        """
        Create a new loan record
        """
        loan = {
            "loan_id": f"LOAN_{len(self.loans) + 1:04d}",
            "customer_id": customer_id,
            "customer_name": customer_name,
            "session_id": session_id,
            "approved_amount": approved_amount,
            "interest_rate": interest_rate,
            "tenure_months": tenure_months,
            "emi": emi,
            "approval_type": approval_type,
            "status": "APPROVED",
            "approved_date": datetime.now().isoformat(),
            "sanction_letter_path": None
        }
        
        self.loans.append(loan)
        self.save_loans()
        return loan
    
    def get_loan_by_session(self, session_id: str) -> Dict[str, Any]:
        """Get loan by session ID"""
        return next((l for l in self.loans if l.get("session_id") == session_id), None)
    
    def update_sanction_letter_path(self, session_id: str, pdf_path: str):
        """Update sanction letter path for a loan"""
        loan = self.get_loan_by_session(session_id)
        if loan:
            loan["sanction_letter_path"] = pdf_path
            self.save_loans()

