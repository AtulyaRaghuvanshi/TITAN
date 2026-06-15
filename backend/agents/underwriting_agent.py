import math
from typing import Tuple, Dict, Any
from services.credit_bureau_service import CreditBureauService
from services.event_bus import EventBus

def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Calculate EMI using standard formula"""
    if months == 0 or annual_rate == 0:
        return principal / months if months > 0 else 0
    
    r = annual_rate / (12 * 100)  # Monthly interest rate
    if r == 0:
        return principal / months
    
    emi = principal * r * math.pow(1 + r, months) / (math.pow(1 + r, months) - 1)
    return round(emi, 2)

class UnderwritingAgent:
    def __init__(self, credit_service: CreditBureauService, event_bus: EventBus):
        self.credit_service = credit_service
        self.event_bus = event_bus
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Handle underwriting agent logic"""
        reply = ""
        
        # Step 1: Get credit score
        if ctx.get("credit_score") is None:
            score = self.credit_service.get_score_by_customer(ctx["customer_id"])
            ctx["credit_score"] = score
        
        # Step 2: Get customer financial data
        customer_data = self.credit_service.get_customer_data(ctx["customer_id"])
        if not customer_data:
            reply = "Error: Customer data not found."
            return reply, ctx
        
        monthly_income = customer_data.get("monthly_income", 0)
        existing_emi = customer_data.get("existing_emi", 0)
        
        # Step 3: Calculate EMI and FOIR
        loan_amount = ctx.get("loan_amount_requested", 0)
        tenure = ctx.get("loan_tenure_requested", 0)
        offer = ctx.get("chosen_offer", {})
        interest_rate = offer.get("base_interest", 0)
        
        emi = calculate_emi(loan_amount, interest_rate, tenure)
        total_obligation = existing_emi + emi
        foir = total_obligation / monthly_income if monthly_income > 0 else 1.0
        
        # Step 4: Apply underwriting rules
        credit_score = ctx.get("credit_score", 0)
        
        # Policy thresholds
        min_score_auto_approve = 725
        min_score_refer = 650
        max_foir_auto_approve = 0.5
        max_foir_refer = 0.6
        
        decision = None
        reason = ""
        
        if credit_score >= min_score_auto_approve and foir <= max_foir_auto_approve:
            decision = "APPROVED"
            reason = f"Credit score {credit_score} >= {min_score_auto_approve} and FOIR {foir:.2%} <= {max_foir_auto_approve:.0%}"
        elif credit_score >= min_score_refer and foir <= max_foir_refer:
            decision = "REFERRED"
            reason = f"Credit score {credit_score} >= {min_score_refer} but needs human review (FOIR: {foir:.2%})"
        else:
            decision = "REJECTED"
            if credit_score < min_score_refer:
                reason = f"Credit score {credit_score} below minimum threshold {min_score_refer}"
            elif foir > max_foir_refer:
                reason = f"FOIR {foir:.2%} exceeds maximum threshold {max_foir_refer:.0%}"
            else:
                reason = "Application does not meet approval criteria"
        
        ctx["decision"] = decision
        ctx["underwriting_result"] = {
            "emi": emi,
            "foir": round(foir, 4),
            "credit_score": credit_score,
            "monthly_income": monthly_income,
            "existing_emi": existing_emi,
            "total_obligation": total_obligation,
            "reason": reason
        }
        
        # Step 5: Generate response
        if decision == "APPROVED":
            reply = f"""✅ **Loan Approved!**

Your loan application has been approved with the following details:

📊 **Loan Details:**
- Loan Amount: ₹{loan_amount:,.0f}
- Tenure: {tenure} months
- Interest Rate: {interest_rate}% p.a.
- EMI: ₹{emi:,.2f}

📈 **Eligibility Metrics:**
- Credit Score: {credit_score}
- FOIR: {foir:.2%}
- Monthly Income: ₹{monthly_income:,.0f}
- Existing EMI: ₹{existing_emi:,.0f}

Proceeding to generate your sanction letter..."""
        
        elif decision == "REFERRED":
            reply = f"""⚠️ **Application Referred for Review**

Your application needs human underwriter review:

📊 **Application Details:**
- Credit Score: {credit_score}
- FOIR: {foir:.2%}
- EMI: ₹{emi:,.2f}
- Reason: {reason}

Our team will review your application and get back to you within 24-48 hours."""
        
        else:  # REJECTED
            reply = f"""❌ **Application Rejected**

Unfortunately, your loan application has been rejected based on our policy rules.

📊 **Application Details:**
- Credit Score: {credit_score}
- FOIR: {foir:.2%}
- Reason: {reason}

Please contact our support team for more information or to discuss alternative options."""
        
        # Publish event
        self.event_bus.publish_event("UNDERWRITING_DECISION", ctx.copy(), ctx["customer_id"])
        
        return reply, ctx

