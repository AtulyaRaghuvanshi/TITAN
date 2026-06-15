import json
import os
from typing import Optional, Dict, Any

OFFERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "offers.json")

class PreApprovalService:
    """Service to check and retrieve pre-approved offers"""
    
    def __init__(self):
        self.offers: list = []
        self.load_offers()
    
    def load_offers(self):
        """Load offers from JSON file"""
        if os.path.exists(OFFERS_FILE):
            with open(OFFERS_FILE, 'r') as f:
                self.offers = json.load(f)
        else:
            self.offers = []
    
    def find_preapproved_offer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Find pre-approved offer for a customer
        Returns None if no pre-approved offer exists
        """
        return next((o for o in self.offers if o.get("customer_id") == customer_id), None)
    
    def calculate_eligible_amount(self, requested_amount: float, preapproved_limit: float) -> float:
        """
        Calculate eligible amount as min(requested_amount, preapproved_limit)
        """
        return min(requested_amount, preapproved_limit)

