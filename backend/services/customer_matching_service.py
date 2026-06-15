import json
import os
from typing import Optional, Dict, Any
import uuid

CUSTOMERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "customers.json")

class CustomerMatchingService:
    """Service to find customers by name and mobile number"""
    
    def __init__(self):
        self.customers: list = []
        self.load_customers()
    
    def load_customers(self):
        """Load customers from JSON file"""
        if os.path.exists(CUSTOMERS_FILE):
            with open(CUSTOMERS_FILE, 'r') as f:
                self.customers = json.load(f)
        else:
            self.customers = []
    
    def find_customer(self, name: str, mobile: str) -> Optional[Dict[str, Any]]:
        """
        Find customer by name and mobile number
        Matching rule: Both name and mobile must match (case-insensitive)
        """
        name_lower = name.lower().strip()
        mobile_clean = mobile.strip().replace(" ", "").replace("-", "")
        
        for customer in self.customers:
            customer_name = customer.get("name", "").lower().strip()
            customer_mobile = str(customer.get("mobile", "")).strip().replace(" ", "").replace("-", "")
            
            # Match if both name and mobile match
            if customer_name == name_lower and customer_mobile == mobile_clean:
                return customer
        
        return None
    
    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by customer_id"""
        return next((c for c in self.customers if c.get("customer_id") == customer_id), None)
    
    def create_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"SESS_{uuid.uuid4().hex[:8].upper()}"

