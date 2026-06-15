import sys
import os
# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from services.customer_matching_service import CustomerMatchingService
from services.preapproval_service import PreApprovalService
from services.eligibility_service import EligibilityService
from services.kyc_document_service import KYCDocumentService
from services.loans_service import LoansService
from services.file_service import FileService
from services.event_bus import EventBus
from agents.chatbot_agent import ChatbotAgent
from agents.preapproved_instant_agent import PreApprovedInstantAgent
from agents.detailed_evaluation_agent import DetailedEvaluationAgent
from agents.sanction_agent import SanctionAgent
from agents.hackathon_master_engine import HackathonMasterEngine

app = FastAPI(title="Hackathon Loan Approval Chatbot API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
customer_matching = CustomerMatchingService()
preapproval_service = PreApprovalService()
eligibility_service = EligibilityService()
kyc_service = KYCDocumentService()
loans_service = LoansService()
file_service = FileService()
event_bus = EventBus()

# Initialize sanction agent
sanction_agent = SanctionAgent(event_bus)

# Initialize agents
chatbot_agent = ChatbotAgent(customer_matching, preapproval_service, event_bus)
preapproved_agent = PreApprovedInstantAgent(preapproval_service, loans_service, event_bus, sanction_agent)
detailed_eval_agent = DetailedEvaluationAgent(
    eligibility_service, kyc_service, loans_service, 
    file_service, event_bus, sanction_agent
)

# Initialize master engine
master_engine = HackathonMasterEngine(
    chatbot_agent,
    preapproved_agent,
    detailed_eval_agent
)

class Message(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    context: Dict[str, Any]

@app.get("/")
def root():
    return {
        "message": "Hackathon Loan Approval Chatbot API",
        "status": "running",
        "description": "Chat-style loan approval system with pre-approved instant approval and detailed evaluation paths"
    }

@app.post("/chat", response_model=ChatResponse)
def chat(msg: Message):
    """
    Main chat endpoint for hackathon loan application journey
    
    Flow:
    1. Collects: name, mobile, city, loan amount, purpose
    2. Matches customer in database
    3. If pre-approved → instant approval path
    4. If not pre-approved → detailed evaluation path (employment, income, KYC docs, eligibility)
    """
    # Initialize context if not provided
    ctx = msg.context or {
        "stage": "INITIAL"
    }
    
    # Process message through master engine
    reply, new_ctx = master_engine.handle(msg.text, ctx)
    
    return ChatResponse(reply=reply, context=new_ctx)

# API endpoints for debugging/testing

@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    """Get customer by ID"""
    customer = customer_matching.get_customer_by_id(customer_id)
    return customer if customer else {"error": "Customer not found"}

@app.get("/offers/{customer_id}")
def get_offer(customer_id: str):
    """Get pre-approved offer for customer"""
    offer = preapproval_service.find_preapproved_offer(customer_id)
    return offer if offer else {"error": "No pre-approved offer found"}

@app.get("/loans/{session_id}")
def get_loan(session_id: str):
    """Get loan by session ID"""
    loan = loans_service.get_loan_by_session(session_id)
    return loan if loan else {"error": "Loan not found"}

@app.get("/events/{session_id}")
def get_events(session_id: str):
    """Get events for a session"""
    events = event_bus.get_events_by_customer(session_id)
    return {"session_id": session_id, "events": events}

@app.get("/events")
def get_all_events():
    """Get all events"""
    return {"events": event_bus.events}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Hackathon Loan Approval Chatbot Starting...")
    print("=" * 60)
    print("📝 Flow:")
    print("  1. Collect: name, mobile, city, loan amount")
    print("  2. Match customer in database")
    print("  3. Pre-approved → Instant approval (no docs)")
    print("  4. Not pre-approved → Detailed evaluation (with docs)")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)

