import json
import os
from typing import Dict, Any, Optional

KYC_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "kyc.json")

class CRMService:
    def __init__(self):
        self.kyc_records: list = []
        self.load_kyc()
    
    def load_kyc(self):
        """Load KYC records from JSON file"""
        if os.path.exists(KYC_FILE):
            with open(KYC_FILE, 'r') as f:
                self.kyc_records = json.load(f)
        else:
            self.kyc_records = []
    
    def get_kyc(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get KYC status for a specific customer"""
        kyc = next((k for k in self.kyc_records if k.get("customer_id") == customer_id), None)
        return kyc
    
    def get_pan_by_customer_id(self, customer_id: str) -> Optional[str]:
        """Get PAN number for a customer"""
        kyc = self.get_kyc(customer_id)
        return kyc.get("pan") if kyc else None

