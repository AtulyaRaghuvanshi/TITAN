import re
import os
import json
from typing import Tuple, Dict, Any
from services.offer_mart_service import OfferMartService
from services.event_bus import EventBus

class SalesAgent:
    def __init__(self, offer_service: OfferMartService, event_bus: EventBus):
        self.offer_service = offer_service
        self.event_bus = event_bus
        # Load FAQs once
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            faq_path = os.path.join(data_dir, 'faqs.json')
            if os.path.exists(faq_path):
                with open(faq_path, 'r', encoding='utf-8') as f:
                    self.faqs = json.load(f)
            else:
                self.faqs = []
        except Exception:
            self.faqs = []
    
    def extract_amount(self, text: str) -> float:
        """Extract loan amount from user message"""
        # Look for numbers followed by common loan amount keywords
        patterns = [
            r'(\d+)\s*(?:lakh|lac|L)',
            r'(\d+)\s*(?:thousand|k|K)',
            r'₹\s*(\d+)',
            r'(\d{4,7})',  # 4-7 digit numbers (likely amounts)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                # Convert lakh to actual amount
                if 'lakh' in text.lower() or 'lac' in text.lower():
                    amount *= 100000
                elif 'thousand' in text.lower() or 'k' in text.lower():
                    amount *= 1000
                return amount
        
        # Try to find any large number
        numbers = re.findall(r'\d+', text)
        for num in numbers:
            num_val = float(num)
            if 10000 <= num_val <= 10000000:  # Reasonable loan amount range
                return num_val
        
        return None
    
    def extract_tenure(self, text: str) -> int:
        """Extract loan tenure in months from user message"""
        # Look for tenure mentions
        patterns = [
            r'(\d+)\s*(?:year|years|yr|yrs)',
            r'(\d+)\s*(?:month|months|mon)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if 'year' in text.lower() or 'yr' in text.lower():
                    return value * 12
                elif 'month' in text.lower() or 'mon' in text.lower():
                    return value
        
        # Look for standalone numbers that might be months
        numbers = re.findall(r'\b(\d+)\b', text)
        for num in numbers:
            num_val = int(num)
            if num_val in [12, 24, 36, 48, 60]:  # Common tenure options
                return num_val
        
        return None
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Handle sales agent logic"""
        reply = ""
        user_lower = (user_msg or '').strip().lower()

        # Early: answer FAQs (Help) without changing flow
        answered_text = None
        try:
            text = user_lower.strip('?!. ')
            if getattr(self, 'faqs', None):
                best_score = 0
                best_answer = None
                for item in self.faqs:
                    q = (item.get('q') or '').lower()
                    a = item.get('a') or ''
                    if not q:
                        continue
                    import re as _re
                    keywords = [w for w in _re.findall(r"[a-zA-Z]+", q) if len(w) > 3]
                    score = sum(1 for kw in keywords if kw in text)
                    if score > best_score and score >= 1:
                        best_score = score
                        best_answer = a
                if best_answer:
                    answered_text = best_answer
            # Heuristic for EMI if no direct match
            if not answered_text and ("emi" in text or "installment" in text):
                for item in (self.faqs or []):
                    if 'emi' in (item.get('q') or '').lower():
                        answered_text = item.get('a') or None
                        break
        except Exception:
            answered_text = None

        if answered_text:
            # Append a next-step hint based on state
            hint = ""
            collecting = ctx.get("collecting_field")
            if ctx.get("stage") == "VERIFICATION":
                hint = "\n\n📄 We’ll continue with documents in chat. If everything looks good, please follow the prompts there."
            elif collecting == "address":
                hint = "\n\n🏠 Please type your address (include city and PIN)."
            elif collecting == "gender":
                hint = "\n\n👤 Please type one: Male, Female, or Third gender."
            elif collecting == "nationality":
                hint = "\n\n🌏 Please type your nationality."
            elif collecting == "employment_type":
                hint = "\n\n💼 Please type one: salaried or self employed."
            elif collecting == "life_insurance":
                hint = "\n\n🛡️ Do you want to opt for life insurance (0.5% of loan amount)? Please type **`yes`** or **`no`**."
            elif ctx.get("loan_amount_requested") is None:
                hint = "\n\n💡 Please type the loan amount (e.g., 3 lakh or 300000)."
            elif ctx.get("loan_tenure_requested") is None:
                hint = "\n\n⏱️ Please type the tenure in months (e.g., 36)."
            elif ctx.get("chosen_offer") and not ctx.get("sales_done"):
                hint = "\n\n➡️ If everything looks good, please type **`yes`** to proceed."
            else:
                hint = "\n\nℹ️ I’ll keep guiding you."
            return answered_text + hint, ctx
        
        # If verification just completed and we need to present the offer now
        if (
            ctx.get("offer_pending")
            and ctx.get("verification_done")
            and ctx.get("loan_amount_requested")
            and ctx.get("loan_tenure_requested")
            and not ctx.get("chosen_offer")
        ):
            offers = self.offer_service.get_offers(ctx["customer_id"])
            if offers:
                offer = self.offer_service.get_offer_by_amount(
                    ctx["customer_id"], ctx["loan_amount_requested"]
                )
                if offer:
                    ctx["chosen_offer"] = offer
                    ctx["offer_pending"] = False
                    processing_fee = ctx["loan_amount_requested"] * (offer["processing_fee_pct"] / 100)
                    reply = (
                        "🎉 Congratulations! Your verification has been completed successfully via government sources and CIBIL.\n\n"
                        "Based on your preferences, here is your final personalized offer:\n\n"
                        f"• Loan Amount: ₹{ctx['loan_amount_requested']:,.0f}\n"
                        f"• Tenure: {ctx['loan_tenure_requested']} months\n"
                        f"• Interest Rate: {offer['base_interest']}% p.a.\n"
                        f"• Processing Fee: ₹{processing_fee:,.0f} ({offer['processing_fee_pct']}%)\n\n"
                        "If you would like to proceed, please type **`yes`** to confirm."
                        "||SPLIT||"
                        "If you have any questions, please feel free to ask. I’m here to help.\n\n"
                        "Tip: You can ask queries by clicking the Help (question mark) button at the bottom-right — I’ll answer without interrupting your flow.\n\n"
                        "After your queries, we’ll proceed with next steps."
                    )
                    self.event_bus.publish_event("SALES_UPDATE", ctx.copy(), ctx["customer_id"])
                    return reply, ctx
            # Fallbacks
            reply = (
                "I couldn't find any offers matching your profile right now.\n"
                "Please try again later or contact support for assistance."
            )
            ctx["offer_pending"] = False
            self.event_bus.publish_event("SALES_UPDATE", ctx.copy(), ctx["customer_id"])
            return reply, ctx
        
        # If we are in the middle of collecting extra details after amount & tenure
        collecting = ctx.get("collecting_field")
        if collecting:
            lower = user_msg.strip().lower()
            # Address: take free text
            if collecting == "address":
                ctx["customer_address"] = user_msg.strip()
                ctx["collecting_field"] = "gender"
                return (
                    "Thank you. Please select your gender:\n- Male\n- Female\n- Third gender\n\nYou can type one of the options.",
                    ctx,
                )
            # Gender: accept male/female/third
            if collecting == "gender":
                gender_val = None
                if "male" in lower:
                    gender_val = "Male"
                elif "female" in lower:
                    gender_val = "Female"
                elif "third" in lower:
                    gender_val = "Third gender"
                if not gender_val:
                    return ("Please choose one of the options:\n- Male\n- Female\n- Third gender", ctx)
                ctx["customer_gender"] = gender_val
                ctx["collecting_field"] = "nationality"
                return ("Thanks. What is your nationality?", ctx)
            # Nationality: free text
            if collecting == "nationality":
                ctx["customer_nationality"] = user_msg.strip()
                ctx["collecting_field"] = "employment_type"
                return (
                    "What is your employment type?\n- Salaried\n- Self employed\n\nPlease type **`salaried`** or **`self employed`**.",
                    ctx,
                )
            # Employment Type: salaried or self employed
            if collecting == "employment_type":
                emp = None
                if "salaried" in lower:
                    emp = "Salaried"
                elif "self" in lower or "business" in lower:
                    emp = "Self Employed"
                if not emp:
                    return ("Please type **`salaried`** or **`self employed`**.", ctx)
                ctx["employment_type"] = emp
                # Done collecting – silently prep offer, then move to verification/documents
                ctx.pop("collecting_field", None)
                try:
                    offers = self.offer_service.get_offers(ctx["customer_id"])
                    if offers and ctx.get("loan_amount_requested"):
                        offer = self.offer_service.get_offer_by_amount(
                            ctx["customer_id"], ctx["loan_amount_requested"]
                        )
                        if offer:
                            ctx["chosen_offer"] = offer
                except Exception:
                    pass
                # Move to verification/documents
                ctx["offer_pending"] = True
                ctx["stage"] = "VERIFICATION"
                # Conditional document line for income proof
                income_line = (
                    "- Income proof (salary slip if salaried; ITR/GST if self-employed)\n"
                    "  • For salary slip: type **`uploaded`** after sharing\n"
                    "  • For ITR/GST: type **`itr uploaded`** or **`gst uploaded`** after sharing\n"
                )
                reply = (
                    "Great, thanks. To continue, please share these documents:\n\n"
                    "- Last 6 months bank statement (type **`bank uploaded`**)\n"
                    "- Government ID with address (type **`id uploaded`**)\n"
                    f"{income_line}"
                    "- PAN card (type **`pan uploaded`**)\n\n"
                    "I’ll guide you step by step."
                )
                self.event_bus.publish_event("SALES_UPDATE", ctx.copy(), ctx["customer_id"])
                return reply, ctx
            # Life insurance: yes/no
            if collecting == "life_insurance":
                if lower in ["yes","y","true"]:
                    ctx["life_insurance"] = "Opted In"
                elif lower in ["no","n","false"]:
                    ctx["life_insurance"] = "Not opted"
                else:
                    return ("Please type Yes or No for life insurance.", ctx)
                # Done collecting – mark sales done and move to verification
                ctx.pop("collecting_field", None)
                ctx["sales_done"] = True
                # Silently select an offer now so later summaries can use interest and fee details
                try:
                    offers = self.offer_service.get_offers(ctx["customer_id"])
                    if offers and ctx.get("loan_amount_requested"):
                        offer = self.offer_service.get_offer_by_amount(
                            ctx["customer_id"], ctx["loan_amount_requested"]
                        )
                        if offer:
                            ctx["chosen_offer"] = offer
                except Exception:
                    pass
                ctx["offer_pending"] = True
                ctx["stage"] = "VERIFICATION"
                reply = (
                    "Thanks. We will now move to verification to review your documents.\n\n"
                    "Please share these documents:\n\n"
                    "- Last 6 months bank statement (type **`bank uploaded`**)\n"
                    "- Government ID with address (type **`id uploaded`**)\n"
                    "- Income proof (salary slip if salaried; ITR/GST if self-employed)\n"
                    "  • For salary slip: type **`uploaded`** after sharing\n"
                    "  • For ITR/GST: type **`itr uploaded`** or **`gst uploaded`** after sharing\n"
                    "- PAN card (type **`pan uploaded`**)\n\n"
                    "I’ll guide you step by step."
                )
                self.event_bus.publish_event("SALES_UPDATE", ctx.copy(), ctx["customer_id"])
                return reply, ctx

        # Step 1: Get loan amount
        if ctx.get("loan_amount_requested") is None:
            amount = self.extract_amount(user_msg)
            if amount:
                ctx["loan_amount_requested"] = amount
                reply = (
                    f"Great! You've requested ₹{amount:,.0f}.\n\n"
                    "Now please tell me the **tenure in months only**.\n"
                    "👉 Example: type `36` for 36 months."
                )
            else:
                reply = (
                    "Hello! I'm here to help you with your personal loan.\n\n"
                    "First, please type the **loan amount you need**.\n"
                    "👉 Example: `3 lakh` or `300000`."
                )
        
        # Step 2: Get loan tenure
        elif ctx.get("loan_tenure_requested") is None:
            tenure = self.extract_tenure(user_msg)
            if tenure:
                ctx["loan_tenure_requested"] = tenure
                # Before getting offers, ensure we collect extra details first
                missing_details = []
                for field in ["customer_address","customer_gender","customer_nationality","employment_type"]:
                    if not ctx.get(field):
                        missing_details.append(field)
                if missing_details:
                    # Start collection sequence at the first missing field (no life insurance here)
                    next_field = (
                        "address" if "customer_address" in missing_details else
                        "gender" if "customer_gender" in missing_details else
                        "nationality" if "customer_nationality" in missing_details else
                        "employment_type" if "employment_type" in missing_details else
                        None
                    )
                    if next_field:
                        ctx["collecting_field"] = next_field
                        if next_field == "address":
                            reply = (
                                "Before I present the offer, could you please share your current residential address (including city and PIN code)?"
                            )
                        elif next_field == "gender":
                            reply = (
                                "Please select your gender:\n- Male\n- Female\n- Third gender\n\nYou can type one of the options."
                            )
                        elif next_field == "nationality":
                            reply = "Thanks. What is your nationality?"
                        elif next_field == "employment_type":
                            reply = (
                                "What is your employment type?\n- Salaried\n- Self employed\n\nPlease type **`salaried`** or **`self employed`**."
                            )
                        # Publish event and return prompt
                        self.event_bus.publish_event("SALES_UPDATE", ctx.copy(), ctx["customer_id"])
                        return reply, ctx
                
                # All details available – silently select offer and move to verification/documents now
                try:
                    offers = self.offer_service.get_offers(ctx["customer_id"])
                    if offers and ctx.get("loan_amount_requested"):
                        offer = self.offer_service.get_offer_by_amount(
                            ctx["customer_id"], ctx["loan_amount_requested"]
                        )
                        if offer:
                            ctx["chosen_offer"] = offer
                except Exception:
                    pass
                # Move to verification/documents now
                ctx["offer_pending"] = True
                ctx["stage"] = "VERIFICATION"
                income_line = (
                    "- Income proof (salary slip if salaried; ITR/GST if self-employed)\n"
                    "  • For salary slip: type **`uploaded`** after sharing\n"
                    "  • For ITR/GST: type **`itr uploaded`** or **`gst uploaded`** after sharing\n"
                )
                reply = (
                    "Great, thanks. To continue, please share these documents:\n\n"
                    "- Last 6 months bank statement (type **`bank uploaded`**)\n"
                    "- Government ID with address (type **`id uploaded`**)\n"
                    f"{income_line}"
                    "- PAN card (type **`pan uploaded`**)\n\n"
                    "I’ll guide you step by step."
                )
                self.event_bus.publish_event("SALES_UPDATE", ctx.copy(), ctx["customer_id"])
                return reply, ctx
            else:
                reply = (
                    "Please specify the **loan tenure in months only**.\n"
                    "👉 Example: type `12`, `24`, or `36`."
                )
        
        # Step 3: Confirm offer acceptance
        elif ctx.get("chosen_offer") and not ctx.get("sales_done"):
            user_msg_lower = user_msg.lower()
            if "yes" in user_msg_lower or "confirm" in user_msg_lower or "proceed" in user_msg_lower:
                # Ask life insurance immediately after offer confirmation
                ctx["collecting_field"] = "life_insurance"
                reply = (
                    "Before we proceed, would you like to opt for life insurance (0.5% of the loan amount)?\n"
                    "Please type **`yes`** or **`no`**."
                )
            else:
                # Try to answer a FAQ if the user asked a question
                answered_text = None
                try:
                    text = user_msg_lower.strip('?!. ')
                    if self.faqs:
                        best_score = 0
                        best_answer = None
                        for item in self.faqs:
                            q = (item.get('q') or '').lower()
                            a = item.get('a') or ''
                            if not q:
                                continue
                            keywords = [w for w in re.findall(r"[a-zA-Z]+", q) if len(w) > 3]
                            score = sum(1 for kw in keywords if kw in text)
                            if score > best_score and score >= 1:
                                best_score = score
                                best_answer = a
                        if best_answer:
                            answered_text = best_answer
                        # Heuristic for EMI questions
                        if not answered_text and ("emi" in text or "installment" in text):
                            for item in self.faqs:
                                if 'emi' in (item.get('q') or '').lower():
                                    answered_text = item.get('a') or None
                                    break
                except Exception:
                    answered_text = None

                if answered_text:
                    reply = answered_text + "\n\nIf everything looks good, please type **`yes`** to proceed."
                else:
                    reply = (
                        "Thank you for your message. If you have a question, please let me know. "
                        "Otherwise, to proceed with this offer, please type **`yes`**."
                    )
        
        else:
            reply = "Sales process completed. Moving to next stage..."
        
        # Publish event
        self.event_bus.publish_event("SALES_UPDATE", ctx.copy(), ctx["customer_id"])
        
        return reply, ctx

