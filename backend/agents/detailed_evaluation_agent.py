import re
from typing import Tuple, Dict, Any
from services.eligibility_service import EligibilityService
from services.kyc_document_service import KYCDocumentService
from services.loans_service import LoansService
from services.file_service import FileService
from services.event_bus import EventBus
from agents.sanction_agent import SanctionAgent

class DetailedEvaluationAgent:
    """
    Handles detailed evaluation flow for non-pre-approved customers
    - Collects employment, income, EMIs, tenure
    - Handles KYC document uploads
    - Evaluates eligibility
    - Approves/rejects based on policies
    """
    
    def __init__(self, eligibility: EligibilityService,
                 kyc_service: KYCDocumentService,
                 loans: LoansService,
                 file_service: FileService,
                 event_bus: EventBus,
                 sanction_agent: SanctionAgent):
        self.eligibility = eligibility
        self.kyc_service = kyc_service
        self.loans = loans
        self.file_service = file_service
        self.event_bus = event_bus
        self.sanction_agent = sanction_agent
    
    def extract_number(self, text: str) -> float:
        """Extract number from text"""
        numbers = re.findall(r'\d+', text.replace(",", ""))
        if numbers:
            return float(numbers[0])
        return None
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Handle detailed evaluation flow"""
        reply = ""
        user_msg_lower = user_msg.lower().strip()
        
        # Step 1: Initial message
        if not ctx.get("detailed_evaluation_started"):
            ctx["detailed_evaluation_started"] = True
            reply = """We could not find you in our pre-approved list. 

Don't worry, we can still process your loan – we just need a few more details and documents. 😊

Let's start with some basic information:

**What is your employment type?**
- Salaried
- Self-employed  
- Student
- Other

Please type one of the above options."""
        
        # Step 2: Get employment type
        elif not ctx.get("employment_type"):
            employment_types = ["salaried", "self-employed", "student", "other"]
            for emp_type in employment_types:
                if emp_type in user_msg_lower:
                    ctx["employment_type"] = emp_type.title()
                    self.event_bus.publish_event("employment_details_collected", {
                        "employment_type": ctx["employment_type"]
                    }, ctx.get("customer_id", ctx.get("session_id")))
                    
                    reply = f"Great! Employment type: {ctx['employment_type']}\n\n" \
                           f"**What is your monthly income?** (e.g., ₹50,000)"
                    break
            else:
                reply = "Please select one: Salaried, Self-employed, Student, or Other"
        
        # Step 3: Get monthly income
        elif not ctx.get("monthly_income"):
            income = self.extract_number(user_msg)
            if income and income > 0:
                ctx["monthly_income"] = income
                self.event_bus.publish_event("income_details_collected", {
                    "monthly_income": income
                }, ctx.get("customer_id", ctx.get("session_id")))
                
                reply = f"Thank you! Monthly income: ₹{income:,.0f}\n\n" \
                       f"**Do you have any existing EMIs or monthly loan obligations?**\n" \
                       f"If yes, please enter the total monthly EMI amount. If no, type '0' or 'none'."
            else:
                reply = "Please enter a valid monthly income amount (e.g., ₹50,000)"
        
        # Step 4: Get existing EMIs
        elif not ctx.get("existing_emi") and ctx.get("existing_emi") != 0:
            if "none" in user_msg_lower or "no" in user_msg_lower or user_msg == "0":
                ctx["existing_emi"] = 0
            else:
                emi = self.extract_number(user_msg)
                if emi is not None and emi >= 0:
                    ctx["existing_emi"] = emi
                else:
                    reply = "Please enter a valid EMI amount or type '0' if you have no existing loans."
                    return reply, ctx
            
            if ctx.get("existing_emi") is not None:
                reply = f"Noted! Existing EMIs: ₹{ctx['existing_emi']:,.0f}\n\n" \
                       f"**What loan tenure would you prefer?** (in months, e.g., 12, 24, 36, 48, 60)"
        
        # Step 5: Get preferred tenure
        elif not ctx.get("preferred_tenure"):
            tenure = self.extract_number(user_msg)
            if tenure and 6 <= tenure <= 60:
                ctx["preferred_tenure"] = int(tenure)
                reply = f"Perfect! Preferred tenure: {int(tenure)} months\n\n" \
                       f"**Do you consent to a credit bureau check?** (Type 'yes' or 'no')"
            else:
                reply = "Please enter a valid tenure between 6 and 60 months"
        
        # Step 6: Get credit bureau consent
        elif not ctx.get("credit_bureau_consent"):
            if "yes" in user_msg_lower:
                ctx["credit_bureau_consent"] = True
            elif "no" in user_msg_lower:
                ctx["credit_bureau_consent"] = False
            else:
                reply = "Please type 'yes' or 'no' for credit bureau consent"
                return reply, ctx
            
            if ctx.get("credit_bureau_consent") is not None:
                reply = "Thank you! Now we need to collect some documents for KYC verification.\n\n" \
                       f"**Please upload your ID proof** (PAN/Aadhaar).\n" \
                       f"For this demo, type 'uploaded' after you've uploaded the file."
                ctx["kyc_stage"] = "ID_PROOF"
        
        # Step 7: Handle KYC document uploads
        elif ctx.get("kyc_stage"):
            if "uploaded" in user_msg_lower or "upload" in user_msg_lower:
                current_stage = ctx.get("kyc_stage")
                
                # Simulate file upload
                file_path = self.file_service.upload_kyc_document(
                    ctx.get("customer_id", "NEW"),
                    ctx.get("session_id"),
                    current_stage
                )
                
                # Record in KYC service
                self.kyc_service.upload_document(
                    ctx.get("customer_id", "NEW"),
                    ctx.get("session_id"),
                    current_stage,
                    file_path
                )
                
                # Move to next document
                if current_stage == "ID_PROOF":
                    ctx["kyc_stage"] = "ADDRESS_PROOF"
                    reply = "✅ ID proof received!\n\n" \
                           f"**Please upload your address proof** (Aadhaar/Utility bill).\n" \
                           f"Type 'uploaded' when done."
                elif current_stage == "ADDRESS_PROOF":
                    ctx["kyc_stage"] = "INCOME_PROOF"
                    reply = "✅ Address proof received!\n\n" \
                           f"**Please upload your income proof** (Latest salary slip or 3-month bank statement).\n" \
                           f"Type 'uploaded' when done."
                elif current_stage == "INCOME_PROOF":
                    ctx["kyc_stage"] = None
                    ctx["all_documents_uploaded"] = True
                    
                    # Log KYC documents uploaded
                    self.event_bus.publish_event("kyc_documents_uploaded", {
                        "document_types": ["ID_PROOF", "ADDRESS_PROOF", "INCOME_PROOF"],
                        "session_id": ctx.get("session_id")
                    }, ctx.get("customer_id", ctx.get("session_id")))
                    
                    reply = "✅ All documents received! Thank you.\n\n" \
                           f"Now let me evaluate your eligibility based on our policies..."
                    
                    # Proceed to eligibility evaluation
                    ctx["ready_for_evaluation"] = True
            else:
                reply = f"Please upload your {ctx.get('kyc_stage', 'document')}. Type 'uploaded' when done."
        
        # Step 8: Evaluate eligibility
        elif ctx.get("ready_for_evaluation") and not ctx.get("evaluation_done"):
            # Get credit score (use from customer if exists, else default low score)
            credit_score = ctx.get("credit_score", 600)  # Default for new customers
            
            # Evaluate eligibility
            evaluation = self.eligibility.evaluate_eligibility(
                credit_score=credit_score,
                monthly_income=ctx.get("monthly_income", 0),
                existing_emi=ctx.get("existing_emi", 0),
                requested_amount=ctx.get("requested_amount", 0),
                tenure_months=ctx.get("preferred_tenure", 36),
                interest_rate=14.0  # Default interest rate for non-pre-approved
            )
            
            ctx["evaluation_result"] = evaluation
            ctx["evaluation_done"] = True
            
            # Log evaluation
            self.event_bus.publish_event("eligibility_evaluated", {
                "credit_score": credit_score,
                "emi_to_income_ratio": evaluation.get("emi_to_income_ratio"),
                "decision": "APPROVED" if evaluation.get("approved") else "REJECTED",
                "reason": evaluation.get("reason"),
                "suggested_amount": evaluation.get("suggested_amount")
            }, ctx.get("customer_id", ctx.get("session_id")))
            
            # Handle evaluation result
            if evaluation.get("approved"):
                # Approved - create loan and generate sanction letter
                loan = self.loans.create_loan(
                    customer_id=ctx.get("customer_id", "NEW"),
                    customer_name=ctx.get("customer_name"),
                    session_id=ctx.get("session_id"),
                    approved_amount=ctx.get("requested_amount", 0),
                    interest_rate=14.0,
                    tenure_months=ctx.get("preferred_tenure", 36),
                    approval_type="evaluated",
                    emi=evaluation.get("emi")
                )
                
                ctx["loan_id"] = loan["loan_id"]
                
                # Generate sanction letter
                pdf_path = self.sanction_agent.generate_sanction_letter_evaluated(
                    ctx, loan, evaluation
                )
                
                self.loans.update_sanction_letter_path(ctx.get("session_id"), pdf_path)
                
                # Log approval
                self.event_bus.publish_event("loan_approved_after_evaluation", {
                    "loan_id": loan["loan_id"],
                    "approved_amount": ctx.get("requested_amount"),
                    "emi": evaluation.get("emi")
                }, ctx.get("customer_id", ctx.get("session_id")))
                
                self.event_bus.publish_event("sanction_letter_generated", {
                    "loan_id": loan["loan_id"],
                    "pdf_path": pdf_path,
                    "approval_type": "evaluated"
                }, ctx.get("customer_id", ctx.get("session_id")))
                
                ctx["stage"] = "END"
                reply = f"""✅ **Good news!** Based on your details and documents, your loan is **approved**! 🎉

**Loan Details:**
- Loan ID: {loan['loan_id']}
- Approved Amount: ₹{ctx.get('requested_amount', 0):,.0f}
- Interest Rate: 14.0% p.a.
- Tenure: {ctx.get('preferred_tenure', 36)} months
- EMI: ₹{evaluation.get('emi', 0):,.2f}
- Approval Type: After Evaluation

**Sanction Letter:**
Your sanction letter has been generated: `{pdf_path}`

Thank you for choosing us! 🚀"""
            
            elif evaluation.get("suggested_amount"):
                # Suggest lower amount
                suggested = evaluation.get("suggested_amount")
                ctx["suggested_amount"] = suggested
                ctx["stage"] = "SUGGEST_AMOUNT"
                reply = f"""We cannot approve ₹{ctx.get('requested_amount', 0):,.0f}, but we can offer **₹{suggested:,.0f}** based on your profile.

**Would you like to proceed with ₹{suggested:,.0f}?** (Type 'yes' to accept, 'no' to decline)"""
            
            else:
                # Rejected
                ctx["stage"] = "END"
                self.event_bus.publish_event("loan_rejected", {
                    "reason": evaluation.get("reason"),
                    "requested_amount": ctx.get("requested_amount")
                }, ctx.get("customer_id", ctx.get("session_id")))
                
                reply = f"""We're sorry, but we are unable to approve a loan at this moment based on our current policies.

**Reason:** {evaluation.get('reason', 'Eligibility criteria not met')}

Please feel free to reach out to us again in the future. 😊"""
        
        # Step 9: Handle suggested amount
        elif ctx.get("stage") == "SUGGEST_AMOUNT":
            if "yes" in user_msg_lower:
                # Accept suggested amount
                suggested = ctx.get("suggested_amount", 0)
                ctx["requested_amount"] = suggested
                ctx["ready_for_evaluation"] = True
                ctx["evaluation_done"] = False
                ctx["stage"] = "DETAILED_EVALUATION"
                # Re-evaluate with suggested amount
                return self.handle("", ctx)
            elif "no" in user_msg_lower:
                ctx["stage"] = "END"
                reply = "Thank you for your interest. Feel free to reach out if you need assistance in the future! 😊"
            else:
                reply = "Please type 'yes' to accept the suggested amount or 'no' to decline."
        
        return reply, ctx

