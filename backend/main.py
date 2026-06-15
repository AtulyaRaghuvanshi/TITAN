import sys
import os
# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from services.offer_mart_service import OfferMartService
from services.crm_service import CRMService
from services.credit_bureau_service import CreditBureauService
from services.file_service import FileService
from services.event_bus import EventBus
from services.llm_service import LLMService
from services.otp_service import OTPService
from agents.sales_agent import SalesAgent
from agents.verification_agent import VerificationAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.sanction_agent import SanctionAgent
from agents.master_engine import MasterEngine

app = FastAPI(title="TITAN NBFC Prototype API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
offer_service = OfferMartService()
crm_service = CRMService()
credit_service = CreditBureauService(crm_service)
file_service = FileService()
event_bus = EventBus()
llm_service = LLMService()
otp_service = OTPService()

# Initialize agents
sales_agent = SalesAgent(offer_service, event_bus)
verification_agent = VerificationAgent(crm_service, file_service, event_bus)
underwriting_agent = UnderwritingAgent(credit_service, event_bus)
sanction_agent = SanctionAgent(event_bus)

# Initialize master engine
master_engine = MasterEngine(
    sales_agent,
    verification_agent,
    underwriting_agent,
    sanction_agent
)

class Message(BaseModel):
    customer_id: str
    text: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    context: Dict[str, Any]
    pdf_base64: Optional[str] = None  # Base64 encoded PDF if sanction letter is generated

class SendEmailOTPRequest(BaseModel):
    email: str

class VerifyEmailOTPRequest(BaseModel):
    email: str
    code: str

@app.get("/")
def root():
    return {"message": "TITAN NBFC Prototype API", "status": "running"}

@app.post("/chat", response_model=ChatResponse)
def chat(msg: Message):
    """Main chat endpoint for loan application journey"""
    # Initialize context if not provided
    ctx = msg.context or {
        "customer_id": msg.customer_id,
        "stage": "SALES",
        "kyc_status": "UNKNOWN"
    }
    
    # Ensure customer_id matches
    ctx["customer_id"] = msg.customer_id
    
    # Prioritize user-entered name from context, fallback to database name
    if not ctx.get("customer_name"):
        import json
        import os
        customers_file = os.path.join(os.path.dirname(__file__), "data", "customers.json")
        if os.path.exists(customers_file):
            with open(customers_file, 'r') as f:
                customers = json.load(f)
                customer = next((c for c in customers if c.get("customer_id") == msg.customer_id), None)
                if customer:
                    ctx["customer_name"] = customer.get("name")
    
    # Process message through master engine
    reply, new_ctx = master_engine.handle(msg.text, ctx)
    
    # Extract PDF if sanction letter was generated
    pdf_base64 = new_ctx.get("sanction_letter_pdf")

    # Optionally pass through LLM for more natural phrasing (without changing logic)
    if llm_service.is_enabled():
        reply = llm_service.rewrite_reply(msg.text, reply, new_ctx)
    
    return ChatResponse(reply=reply, context=new_ctx, pdf_base64=pdf_base64)

# Mock API endpoints for services (as per requirements)

@app.get("/offer-mart/offers/{customer_id}")
def get_offers(customer_id: str):
    """Mock Offer Mart server endpoint"""
    offers = offer_service.get_offers(customer_id)
    return {"customer_id": customer_id, "offers": offers}

@app.get("/crm/kyc/{customer_id}")
def get_kyc(customer_id: str):
    """Mock CRM server endpoint"""
    kyc = crm_service.get_kyc(customer_id)
    return kyc if kyc else {"error": "KYC not found"}

@app.get("/credit-bureau/score/{pan}")
def get_credit_score(pan: str):
    """Mock Credit Bureau API endpoint"""
    score = credit_service.get_score_by_pan(pan)
    return {"pan": pan, "credit_score": score} if score else {"error": "Score not found"}

@app.post("/files/upload-salary-slip")
def upload_salary_slip(customer_id: str = None, file: UploadFile | None = File(default=None)):
    """Upload salary slip for a customer (supports real file or placeholder)."""
    if not customer_id:
        return {"error": "customer_id is required"}
    result = file_service.upload_salary_slip(customer_id, file)
    return result

@app.get("/events/{customer_id}")
def get_events(customer_id: str):
    """Get events for a customer"""
    events = event_bus.get_events_by_customer(customer_id)
    return {"customer_id": customer_id, "events": events}

@app.get("/events")
def get_all_events():
    """Get all events"""
    return {"events": event_bus.events}

@app.post("/otp/send-email")
def send_email_otp(payload: SendEmailOTPRequest):
    """Generate and (for demo) 'send' a 6-digit OTP to the provided email.
    In production, integrate with an email provider. Optionally exposes OTP when DEMO_EXPOSE_OTP=true.
    """
    result = otp_service.generate_otp(payload.email)
    return {"status": result.get("status", "sent"), "demo_otp": result.get("otp")}

@app.post("/otp/verify-email")
def verify_email_otp(payload: VerifyEmailOTPRequest):
    """Verify the email OTP code."""
    ok = otp_service.verify_otp(payload.email, payload.code)
    return {"verified": ok}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

