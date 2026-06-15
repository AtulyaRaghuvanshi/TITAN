from typing import Tuple, Dict, Any
from services.preapproval_service import PreApprovalService
from services.loans_service import LoansService
from services.event_bus import EventBus
from agents.sanction_agent import SanctionAgent

class PreApprovedInstantAgent:
    """
    Handles pre-approved instant approval flow
    - No file uploads required
    - Instant approval if customer confirms
    """
    
    def __init__(self, preapproval: PreApprovalService, 
                 loans: LoansService, event_bus: EventBus,
                 sanction_agent: SanctionAgent):
        self.preapproval = preapproval
        self.loans = loans
        self.event_bus = event_bus
        self.sanction_agent = sanction_agent
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Handle pre-approved instant approval flow"""
        reply = ""
        user_msg_lower = user_msg.lower().strip()
        
        # Step 1: Show pre-approved offer
        if not ctx.get("preapproved_offer_shown"):
            offer = ctx.get("preapproved_offer", {})
            requested_amount = ctx.get("requested_amount", 0)
            preapproved_limit = offer.get("max_amount", 0)
            interest_rate = offer.get("base_interest", 0)
            
            # Calculate eligible amount
            eligible_amount = self.preapproval.calculate_eligible_amount(
                requested_amount, preapproved_limit
            )
            
            ctx["eligible_amount"] = eligible_amount
            ctx["preapproved_offer_shown"] = True
            
            reply = f"""🎉 **Congratulations!** 

Our company already trusts you – you're on our **pre-approved list**! 

You are eligible for an instant loan of **₹{eligible_amount:,.0f}** at **{interest_rate}%** interest.

This is an **instant approval** – no documents or waiting required! ⚡

**Do you want to proceed with this instant loan approval?** (Type 'yes' to confirm, or 'no' to decline)"""
        
        # Step 2: Handle confirmation
        elif not ctx.get("preapproved_confirmed") and not ctx.get("preapproved_declined"):
            if "yes" in user_msg_lower or "confirm" in user_msg_lower or "proceed" in user_msg_lower:
                # Instant approval confirmed
                ctx["preapproved_confirmed"] = True
                
                # Create loan record
                loan = self.loans.create_loan(
                    customer_id=ctx.get("customer_id", "NEW"),
                    customer_name=ctx.get("customer_name"),
                    session_id=ctx.get("session_id"),
                    approved_amount=ctx.get("eligible_amount", 0),
                    interest_rate=ctx.get("preapproved_interest", 0),
                    tenure_months=36,  # Default tenure
                    approval_type="preapproved_instant",
                    emi=None
                )
                
                ctx["loan_id"] = loan["loan_id"]
                
                # Log event
                self.event_bus.publish_event("preapproved_instant_approval_confirmed", {
                    "loan_id": loan["loan_id"],
                    "approved_amount": ctx.get("eligible_amount"),
                    "interest_rate": ctx.get("preapproved_interest")
                }, ctx.get("customer_id", ctx.get("session_id")))
                
                # Generate sanction letter
                pdf_path = self.sanction_agent.generate_sanction_letter_instant(
                    ctx, loan
                )
                
                # Update loan with PDF path
                self.loans.update_sanction_letter_path(ctx.get("session_id"), pdf_path)
                
                # Log sanction letter generation
                self.event_bus.publish_event("sanction_letter_generated", {
                    "loan_id": loan["loan_id"],
                    "pdf_path": pdf_path,
                    "approval_type": "preapproved_instant"
                }, ctx.get("customer_id", ctx.get("session_id")))
                
                ctx["stage"] = "END"
                reply = f"""✅ **Your loan has been approved instantly!** 🎊

**Loan Details:**
- Loan ID: {loan['loan_id']}
- Approved Amount: ₹{ctx.get('eligible_amount', 0):,.0f}
- Interest Rate: {ctx.get('preapproved_interest', 0)}% p.a.
- Approval Type: Instant Pre-Approved

**Sanction Letter:**
Your sanction letter has been generated and saved at:
`{pdf_path}`

Thank you for choosing us! Your loan is ready. 🚀"""
            
            elif "no" in user_msg_lower or "decline" in user_msg_lower:
                ctx["preapproved_declined"] = True
                self.event_bus.publish_event("preapproved_offer_declined", {
                    "requested_amount": ctx.get("requested_amount"),
                    "preapproved_limit": ctx.get("preapproved_limit")
                }, ctx.get("customer_id", ctx.get("session_id")))
                
                ctx["stage"] = "END"
                reply = "Thank you for your interest. If you change your mind or need a different loan amount, feel free to reach out to us anytime! 😊"
            else:
                reply = "Please confirm: Do you want to proceed with this instant loan approval? (Type 'yes' or 'no')"
        
        return reply, ctx

