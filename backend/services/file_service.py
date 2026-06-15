import os
from datetime import datetime
from typing import Dict, Any
from fastapi import UploadFile

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")

class FileService:
    def __init__(self):
        os.makedirs(UPLOADS_DIR, exist_ok=True)
    
    def upload_salary_slip(self, customer_id: str, file: UploadFile = None) -> Dict[str, Any]:
        """Upload salary slip for a customer"""
        # For prototype, we can accept a simple text confirmation or actual file
        file_id = f"{customer_id}_salary_{datetime.now().strftime('%Y-%m-%d')}"
        file_path = os.path.join(UPLOADS_DIR, f"{file_id}.pdf")
        
        # If file is provided, save it
        if file:
            with open(file_path, "wb") as f:
                content = file.file.read()
                f.write(content)
        else:
            # Create a placeholder file for demo purposes
            with open(file_path, "w") as f:
                f.write(f"Salary slip placeholder for {customer_id}")
        
        return {
            "status": "RECEIVED",
            "file_id": file_id,
            "file_path": file_path
        }
    
    def check_salary_slip_uploaded(self, customer_id: str) -> bool:
        """Check if salary slip has been uploaded for a customer"""
        # Check if any salary slip file exists for this customer
        if not os.path.exists(UPLOADS_DIR):
            return False
        
        for filename in os.listdir(UPLOADS_DIR):
            if filename.startswith(f"{customer_id}_salary"):
                return True
        return False
    
    def upload_kyc_document(self, customer_id: str, session_id: str, document_type: str) -> str:
        """
        Upload KYC document (ID_PROOF, ADDRESS_PROOF, INCOME_PROOF)
        For prototype, creates a placeholder file
        """
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{session_id}_{document_type}_{timestamp}.pdf"
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        # Create placeholder file
        with open(file_path, "w") as f:
            f.write(f"KYC Document: {document_type}\n")
            f.write(f"Customer ID: {customer_id}\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Uploaded: {datetime.now().isoformat()}\n")
        
        return file_path

