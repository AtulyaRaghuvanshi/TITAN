import json
import os
from typing import Optional
from services.crm_service import CRMService

CUSTOMERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "customers.json")

class CreditBureauService:
    def __init__(self, crm_service: CRMService):
        self.crm_service = crm_service
        self.customers: list = []
        self.load_customers()
    
    def load_customers(self):
        """Load customer data from JSON file"""
        if os.path.exists(CUSTOMERS_FILE):
            with open(CUSTOMERS_FILE, 'r') as f:
                self.customers = json.load(f)
        else:
            self.customers = []
    
    def get_score_by_pan(self, pan: str) -> Optional[int]:
        """Get credit score by PAN number"""
        # Find customer by PAN via CRM
        kyc_records = self.crm_service.kyc_records
        customer_id = None
        for kyc in kyc_records:
            if kyc.get("pan") == pan:
                customer_id = kyc.get("customer_id")
                break
        
        if not customer_id:
            return None
        
        # Get credit score from customers.json
        customer = next((c for c in self.customers if c.get("customer_id") == customer_id), None)
        return customer.get("credit_score") if customer else None
    
    def get_score_by_customer(self, customer_id: str) -> Optional[int]:
        """Get credit score by customer ID"""
        customer = next((c for c in self.customers if c.get("customer_id") == customer_id), None)
        return customer.get("credit_score") if customer else None
    
    def get_customer_data(self, customer_id: str) -> Optional[dict]:
        """Get full customer data"""
        return next((c for c in self.customers if c.get("customer_id") == customer_id), None)

