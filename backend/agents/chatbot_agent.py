import re
from typing import Tuple, Dict, Any
from services.customer_matching_service import CustomerMatchingService
from services.preapproval_service import PreApprovalService
from services.event_bus import EventBus

class ChatbotAgent:
    """
    Initial chatbot agent that collects basic information:
    - Full name
    - Mobile number
    - City
    - Desired loan amount
    - Purpose (optional)
    """
    
    def __init__(self, customer_matching: CustomerMatchingService, 
                 preapproval: PreApprovalService, event_bus: EventBus):
        self.customer_matching = customer_matching
        self.preapproval = preapproval
        self.event_bus = event_bus
    
    def extract_amount(self, text: str) -> float:
        """Extract loan amount from user message"""
        patterns = [
            r'(\d+)\s*(?:lakh|lac|L)',
            r'(\d+)\s*(?:thousand|k|K)',
            r'₹\s*(\d+)',
            r'(\d{4,7})',  # 4-7 digit numbers
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                if 'lakh' in text.lower() or 'lac' in text.lower():
                    amount *= 100000
                elif 'thousand' in text.lower() or 'k' in text.lower():
                    amount *= 1000
                return amount
        
        # Try to find any large number
        numbers = re.findall(r'\d+', text)
        for num in numbers:
            num_val = float(num)
            if 10000 <= num_val <= 10000000:
                return num_val
        
        return None
    
    def extract_mobile(self, text: str) -> str:
        """Extract mobile number from text"""
        # Look for 10-digit numbers
        patterns = [
            r'(\d{10})',
            r'(\d{5}[\s-]?\d{5})',
            r'\+91[\s-]?(\d{10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                mobile = match.group(1).replace(" ", "").replace("-", "")
                if len(mobile) == 10:
                    return mobile
        
        return None
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Handle initial conversation to collect user details"""
        reply = ""
        user_msg_lower = user_msg.lower().strip()
        
        # Step 1: Get full name
        if not ctx.get("customer_name"):
            if len(user_msg.split()) >= 2:  # Assume full name has at least 2 words
                ctx["customer_name"] = user_msg.strip()
                reply = f"Nice to meet you, {ctx['customer_name']}! 👋\n\n" \
                       f"Could you please share your registered mobile number?"
            else:
                reply = "Hello! Welcome to our loan application service. 😊\n\n" \
                       f"To get started, could you please tell me your **full name**?"
        
        # Step 2: Get mobile number
        elif not ctx.get("mobile"):
            mobile = self.extract_mobile(user_msg)
            if mobile:
                ctx["mobile"] = mobile
                reply = f"Thank you! Mobile number registered: {mobile}\n\n" \
                       f"Which **city** are you located in?"
            else:
                reply = "I couldn't find a valid mobile number. Please share your 10-digit registered mobile number."
        
        # Step 3: Get city
        elif not ctx.get("city"):
            ctx["city"] = user_msg.strip()
            reply = f"Great! City noted: {ctx['city']}\n\n" \
                   f"What **loan amount** are you looking for? (e.g., ₹3,00,000 or 3 lakh)"
        
        # Step 4: Get loan amount
        elif not ctx.get("requested_amount"):
            amount = self.extract_amount(user_msg)
            if amount:
                ctx["requested_amount"] = amount
                reply = f"Perfect! You're looking for ₹{amount:,.0f}.\n\n" \
                       f"**Optional:** What is the purpose of this loan? (e.g., Home renovation, Education, etc.)\n" \
                       f"Or just type 'skip' to proceed."
            else:
                reply = "I couldn't understand the loan amount. Please specify the amount (e.g., ₹3,00,000 or 3 lakh)"
        
        # Step 5: Get purpose (optional)
        elif not ctx.get("purpose") and not ctx.get("purpose_skipped"):
            if "skip" in user_msg_lower:
                ctx["purpose_skipped"] = True
                ctx["purpose"] = "Not specified"
            else:
                ctx["purpose"] = user_msg.strip()
            
            # Now try to match customer
            matched_customer = self.customer_matching.find_customer(
                ctx["customer_name"], 
                ctx["mobile"]
            )
            
            if matched_customer:
                ctx["customer_id"] = matched_customer["customer_id"]
                ctx["matched_customer"] = matched_customer
                ctx["credit_score"] = matched_customer.get("credit_score", 0)
                reply = f"Thank you! I found your account in our system. ✅\n\n" \
                       f"Let me check if you have any pre-approved offers..."
            else:
                # New customer
                ctx["customer_id"] = None
                ctx["is_new_customer"] = True
                ctx["credit_score"] = 0  # Default low score for new customers
                reply = f"Thank you! I don't see you in our existing customer database, but that's okay! 😊\n\n" \
                       f"Let me check for any pre-approved offers..."
            
            # Check for pre-approved offer
            if ctx.get("customer_id"):
                offer = self.preapproval.find_preapproved_offer(ctx["customer_id"])
                if offer:
                    ctx["preapproved_offer"] = offer
                    ctx["preapproved_limit"] = offer.get("max_amount", 0)
                    ctx["preapproved_interest"] = offer.get("base_interest", 0)
                    ctx["stage"] = "PREAPPROVED_CHECK"
                else:
                    ctx["stage"] = "DETAILED_EVALUATION"
            else:
                ctx["stage"] = "DETAILED_EVALUATION"
        
        # Log session start event
        if ctx.get("customer_name") and ctx.get("mobile") and ctx.get("requested_amount") and not ctx.get("session_started"):
            session_id = self.customer_matching.create_session_id()
            ctx["session_id"] = session_id
            
            self.event_bus.publish_event("session_started", {
                "name": ctx["customer_name"],
                "mobile": ctx["mobile"],
                "city": ctx.get("city"),
                "requested_amount": ctx["requested_amount"],
                "purpose": ctx.get("purpose", "Not specified"),
                "customer_id": ctx.get("customer_id"),
                "is_new_customer": ctx.get("is_new_customer", False)
            }, ctx.get("customer_id", session_id))
            
            ctx["session_started"] = True
        
        return reply, ctx

