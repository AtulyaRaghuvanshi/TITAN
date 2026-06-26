from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME
from graph_pipeline import run_loan_pipeline
from langchain_helper import build_decision_summary
from models import CustomerProfile, LoanDecisionResponse


app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": APP_NAME,
        "status": "running",
        "agents": [
            "profile_agent",
            "credit_agent",
            "document_verification_agent",
            "underwriting_agent",
            "sanction_agent",
        ],
    }


@app.post("/loan/decide", response_model=LoanDecisionResponse)
def decide_loan(profile: CustomerProfile):
    state = run_loan_pipeline(profile.model_dump())
    state["summary"] = build_decision_summary(state)
    return LoanDecisionResponse(
        decision=state.get("decision", "PENDING"),
        reason=state.get("reason", "Pipeline completed."),
        approved_amount=state.get("approved_amount", 0),
        interest_rate=state.get("interest_rate", 0),
        emi=state.get("emi", 0),
        foir_percent=state.get("foir_percent", 0),
        sanction_letter_path=state.get("sanction_letter_path"),
        pipeline=state.get("pipeline", []),
        state=state,
    )


@app.get("/demo/customers")
def demo_customers():
    return {
        "approved": CustomerProfile().model_dump(),
        "review": CustomerProfile(
            customer_id="CUST-REVIEW",
            name="Review Customer",
            requested_amount=1800000,
            existing_monthly_emi=22000,
        ).model_dump(),
        "rejected": CustomerProfile(
            customer_id="CUST-REJECT",
            name="Rejected Customer",
            credit_score=640,
        ).model_dump(),
    }


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8010")),
        reload=True,
    )
