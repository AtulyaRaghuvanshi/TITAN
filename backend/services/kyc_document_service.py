import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

KYC_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "kyc.json")

class KYCDocumentService:
    """Service to manage KYC document uploads"""
    
    def __init__(self):
        self.kyc_records: list = []
        self.load_kyc()
    
    def load_kyc(self):
        """Load KYC records from JSON file"""
        if os.path.exists(KYC_FILE):
            try:
                with open(KYC_FILE, 'r') as f:
                    self.kyc_records = json.load(f)
            except:
                self.kyc_records = []
        else:
            self.kyc_records = []
    
    def save_kyc(self):
        """Save KYC records to JSON file"""
        os.makedirs(os.path.dirname(KYC_FILE), exist_ok=True)
        with open(KYC_FILE, 'w') as f:
            json.dump(self.kyc_records, f, indent=2)
    
    def upload_document(self,
                       customer_id: str,
                       session_id: str,
                       document_type: str,  # ID_PROOF, ADDRESS_PROOF, INCOME_PROOF
                       file_path: str) -> Dict[str, Any]:
        """
        Record a KYC document upload
        """
        kyc_record = {
            "customer_id": customer_id,
            "session_id": session_id,
            "document_type": document_type,
            "file_path": file_path,
            "status": "uploaded",
            "uploaded_at": datetime.now().isoformat()
        }
        
        self.kyc_records.append(kyc_record)
        self.save_kyc()
        return kyc_record
    
    def get_uploaded_documents(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all uploaded documents for a session"""
        return [k for k in self.kyc_records if k.get("session_id") == session_id]
    
    def check_all_documents_uploaded(self, session_id: str) -> bool:
        """Check if all required documents are uploaded"""
        uploaded = self.get_uploaded_documents(session_id)
        uploaded_types = [d.get("document_type") for d in uploaded]
        
        required = ["ID_PROOF", "ADDRESS_PROOF", "INCOME_PROOF"]
        return all(doc_type in uploaded_types for doc_type in required)
    
    def get_kyc_by_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get KYC record by customer_id (for existing customers)"""
        return next((k for k in self.kyc_records if k.get("customer_id") == customer_id), None)

