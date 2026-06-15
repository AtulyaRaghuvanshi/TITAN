from typing import Tuple, Dict, Any
from agents.sales_agent import SalesAgent
from agents.verification_agent import VerificationAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.sanction_agent import SanctionAgent

class MasterEngine:
    def __init__(self, sales_agent: SalesAgent, verification_agent: VerificationAgent, 
                 underwriting_agent: UnderwritingAgent, sanction_agent: SanctionAgent):
        self.sales_agent = sales_agent
        self.verification_agent = verification_agent
        self.underwriting_agent = underwriting_agent
        self.sanction_agent = sanction_agent
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Orchestrate the loan journey workflow"""
        # Initialize context if needed
        if not ctx:
            ctx = {}
        
        # Set default stage if not present
        stage = ctx.get("stage", "SALES")
        
        reply = ""
        
        # Route to appropriate agent based on stage
        if stage == "SALES":
            reply, ctx = self.sales_agent.handle(user_msg, ctx)
            if ctx.get("sales_done"):
                ctx["stage"] = "VERIFICATION"
                reply += (
                    "\n\n✅ Sales stage completed. We will now move to the **verification stage**.\n"
                    "To continue once your KYC details are shown, please type **`confirm`** to move to the next step."
                )
        
        elif stage == "VERIFICATION":
            reply, ctx = self.verification_agent.handle(user_msg, ctx)
            # If verification is completed OR the verification agent already set stage to UNDERWRITING, proceed immediately
            if ctx.get("verification_done") or ctx.get("stage") == "UNDERWRITING":
                ctx["stage"] = "UNDERWRITING"
                # Add a small status line if not already present
                if "eligibility check" not in reply:
                    reply += "\n\n✅ Verification completed. Moving to eligibility check..."
                # Immediately run underwriting and, if approved, generate sanction letter in the same turn
                uw_reply, ctx = self.underwriting_agent.handle(user_msg, ctx)
                if ctx.get("decision") == "APPROVED":
                    sanction_reply, ctx = self.sanction_agent.handle(user_msg, ctx)
                    reply = f"{reply}\n\n{uw_reply}\n\n{sanction_reply}"
                    ctx["stage"] = ctx.get("stage", "END")
                else:
                    reply = f"{reply}\n\n{uw_reply}"
        
        elif stage == "UNDERWRITING":
            # Run underwriting rules
            reply, ctx = self.underwriting_agent.handle(user_msg, ctx)

            if ctx.get("decision") == "APPROVED":
                # Immediately generate sanction letter in the same interaction
                sanction_reply, ctx = self.sanction_agent.handle(user_msg, ctx)
                # Combine responses so user sees approval details + sanction info together
                reply = f"{reply}\n\n{sanction_reply}"
                # Sanction agent will usually set stage to END
                ctx["stage"] = ctx.get("stage", "END")

            elif ctx.get("decision") in ["REJECTED", "REFERRED"]:
                # Journey ends for rejected / referred cases
                ctx["stage"] = "END"
        
        elif stage == "SANCTION":
            reply, ctx = self.sanction_agent.handle(user_msg, ctx)
            if ctx.get("stage") == "END":
                reply += "\n\n🎊 Your loan journey is complete!"
        
        else:  # END or unknown stage
            # Allow user to restart a new journey after completion
            lower_msg = user_msg.lower()
            if any(kw in lower_msg for kw in ["restart", "new loan", "start again", "another loan"]):
                # Reset minimal context for a fresh journey, but keep customer_id if present
                customer_id = ctx.get("customer_id")
                ctx = {
                    "customer_id": customer_id,
                    "stage": "SALES",
                    "kyc_status": "UNKNOWN"
                }
                reply = (
                    "No problem, we can start a new loan journey.\n\n"
                    "Please tell me how much loan amount you need. "
                    "Example: `3 lakh` or `300000`."
                )
            elif not reply:
                reply = (
                    "Your loan journey is complete. ✅\n\n"
                    "If you would like to start **another** application, "
                    "you can type `restart` or `new loan`."
                )
        
        # Global safeguard: if verification is done but decision not made, run underwriting now
        if ctx.get("verification_done") and not ctx.get("decision"):
            ctx["stage"] = "UNDERWRITING"
            uw_reply, ctx = self.underwriting_agent.handle(user_msg, ctx)
            if ctx.get("decision") == "APPROVED":
                sanction_reply, ctx = self.sanction_agent.handle(user_msg, ctx)
                reply = f"{reply}\n\n{uw_reply}\n\n{sanction_reply}" if reply else f"{uw_reply}\n\n{sanction_reply}"
                ctx["stage"] = ctx.get("stage", "END")
            else:
                reply = f"{reply}\n\n{uw_reply}" if reply else uw_reply

        return reply, ctx

