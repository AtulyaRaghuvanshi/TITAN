from typing import Tuple, Dict, Any
from services.crm_service import CRMService
from services.file_service import FileService
from services.event_bus import EventBus
import os, json, re

class VerificationAgent:
    def __init__(self, crm_service: CRMService, file_service: FileService, event_bus: EventBus):
        self.crm_service = crm_service
        self.file_service = file_service
        self.event_bus = event_bus
        # Load FAQs once (shared knowledge for answering Help questions)
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

    def answer_help(self, user_msg: str, ctx: Dict[str, Any]) -> str | None:
        try:
            user_lower = (user_msg or '').strip().lower()
            text = user_lower.strip('?!. ')
            answered_text = None
            if self.faqs:
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
            if not answered_text and ("emi" in text or "installment" in text):
                # Try FAQ first
                for item in self.faqs:
                    if 'emi' in (item.get('q') or '').lower():
                        answered_text = item.get('a') or None
                        break
                # Fallback: compute EMI explanation from context
                if not answered_text:
                    try:
                        amt = float(ctx.get("loan_amount_requested") or 0)
                        tenure = int(ctx.get("loan_tenure_requested") or 0)
                        rate = float((ctx.get("chosen_offer") or {}).get("base_interest") or 0)
                        r = rate / (12 * 100.0)
                        emi_val = 0.0
                        if r > 0 and tenure > 0 and amt > 0:
                            from math import pow
                            emi_val = amt * r * pow(1 + r, tenure) / (pow(1 + r, tenure) - 1)
                        answered_text = (
                            "EMI (Equated Monthly Instalment) is calculated using your loan amount, interest rate, and tenure.\n"
                            f"Formula: EMI = P × r × (1+r)^n / ((1+r)^n − 1), where P = principal (₹{amt:,.0f}), r = monthly interest rate ({rate}% ÷ 12), n = months ({tenure}).\n"
                            + (f"For your request, the estimated EMI is around ₹{emi_val:,.2f}." if emi_val > 0 else "Once amount, rate, and tenure are set, I’ll show your EMI.")
                        )
                    except Exception:
                        answered_text = (
                            "EMI (Equated Monthly Instalment) depends on loan amount, interest rate, and tenure."
                        )
        except Exception:
            answered_text = None

        if not answered_text:
            return None

        is_self = str(ctx.get("employment_type", "")).lower().startswith("self")
        hint = ""
        if ctx.get("awaiting_verification_confirm"):
            hint = "\n\n🔒 When you’re ready, please type **`i confirm`** to continue."
        elif not ctx.get("bank_statement_uploaded"):
            hint = "\n\n📄 Please upload your bank statement and type **`bank uploaded`** to continue."
        elif not ctx.get("id_address_proof_uploaded"):
            hint = "\n\n🪪 Please upload your ID with address and type **`id uploaded`** to continue."
        elif (is_self and not ctx.get("business_docs_uploaded")) or (not is_self and not ctx.get("salary_slip_uploaded")):
            if is_self:
                hint = "\n\n📑 Please upload your ITR or GST return and type **`itr uploaded`** or **`gst uploaded`** to continue."
            else:
                hint = "\n\n📑 Please upload your salary slip and type **`uploaded`** to continue."
        elif not ctx.get("pan_card_uploaded"):
            hint = "\n\n🧾 Please upload your PAN card and type **`pan uploaded`** to continue."
        else:
            hint = "\n\n➡️ When everything looks good, please type **`proceed`** to generate your sanction letter."

        footer = (
            "\n\nYou can ask another question, or if everything seems good, please type **`proceed`** to generate your sanction letter."
        )
        return (answered_text or "") + hint + footer
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Handle verification agent logic"""
        reply = ""
        user_lower = (user_msg or '').strip().lower()

        # Fast-path: if awaiting final confirmation, handle immediately
        if ctx.get("awaiting_sanction_confirm") and user_lower in ["confirm", "confirm.", "yes", "generate", "proceed"]:
            ctx["awaiting_sanction_confirm"] = False
            ctx["awaiting_bank_details"] = False
            ctx["verification_done"] = True
            ctx["stage"] = "UNDERWRITING"
            return "Great! Proceeding to the next step and generating your sanction letter...", ctx

        # Early: if the user asked a question via Help, try to answer without changing flow
        help_answer = self.answer_help(user_msg, ctx)
        if help_answer:
            return help_answer, ctx
        
        # Step 1: Check KYC status
        if ctx.get("kyc_status") == "UNKNOWN" or ctx.get("kyc_status") is None:
            kyc = self.crm_service.get_kyc(ctx["customer_id"])
            if kyc:
                ctx["kyc_status"] = kyc.get("kyc_status", "UNKNOWN")
                ctx["pan"] = kyc.get("pan")
                ctx["aadhaar_masked"] = kyc.get("aadhaar_masked")
            else:
                ctx["kyc_status"] = "NOT_FOUND"
        
        # Step 2: Handle incomplete KYC
        if ctx.get("kyc_status") != "COMPLETED":
            if "confirm" in user_msg.lower() or "verified" in user_msg.lower() or "done" in user_msg.lower():
                # For prototype, mark as completed when user confirms
                ctx["kyc_status"] = "COMPLETED"
                reply = (
                    "Great, thanks for confirming your details.\n\n"
                    "Next, I just need your most recent salary slip so we can complete the verification.\n"
                    "👉 You can either attach the file using the upload button, "
                    "or simply type **`uploaded`** once you’ve shared it."
                )
            else:
                pan_info = f"PAN: {ctx.get('pan', 'N/A')}" if ctx.get('pan') else ""
                aadhaar_info = f"Aadhaar: {ctx.get('aadhaar_masked', 'N/A')}" if ctx.get('aadhaar_masked') else ""
                reply_lines = [
                    f"Here’s what I have for your KYC status: **{ctx.get('kyc_status', 'PENDING')}**."
                ]
                if pan_info:
                    reply_lines.append(pan_info)
                if aadhaar_info:
                    reply_lines.append(aadhaar_info)

                reply_lines.append(
                    "\nIf everything looks correct, please type **`confirm`** so we can move ahead."
                )

                reply = "\n".join(reply_lines)
        
        # Step 3: Documents collection (avoid saying 'verification') and final confirmation
        elif True:
            lower_msg = user_msg.lower().strip()
            # 1) Bank statement first
            if not ctx.get("bank_statement_uploaded", False):
                if ("bank" in lower_msg and ("uploaded" in lower_msg or "done" in lower_msg)):
                    session_id = ctx.get("session_id", "demo")
                    _ = self.file_service.upload_kyc_document(ctx["customer_id"], session_id, "BANK_STATEMENT")
                    ctx["bank_statement_uploaded"] = True
                    reply = (
                        "Bank statement received. ✅\n"
                        "Next, please share a government ID with address (Aadhaar/Passport/DL).\n"
                        "Type **`id uploaded`** after you’ve shared it."
                    )
                else:
                    reply = (
                        "Please upload your last 6 months bank statement.\n"
                        "Type **`bank uploaded`** after you’ve shared it."
                    )
            # 2) ID with address
            elif not ctx.get("id_address_proof_uploaded", False):
                if ("id" in lower_msg and ("uploaded" in lower_msg or "done" in lower_msg)):
                    session_id = ctx.get("session_id", "demo")
                    _ = self.file_service.upload_kyc_document(ctx["customer_id"], session_id, "ID_ADDRESS_PROOF")
                    ctx["id_address_proof_uploaded"] = True
                    is_self = str(ctx.get("employment_type", "")).lower().startswith("self")
                    if is_self:
                        reply = (
                            "Thanks — your ID with address has been received. ✅\n"
                            "Now, please share your ITR or GST return.\n"
                            "Type **`itr uploaded`** or **`gst uploaded`** after you’ve shared it."
                        )
                    else:
                        reply = (
                            "Thanks — your ID with address has been received. ✅\n"
                            "Now, please share your most recent salary slip.\n"
                            "Type **`uploaded`** after you’ve shared it."
                        )
                else:
                    reply = (
                        "Please share a government ID with address (Aadhaar/Passport/DL).\n"
                        "Type **`id uploaded`** after you’ve shared it."
                    )
            # 3) Income proof (Salary slip for salaried; ITR/GST for self-employed)
            elif (
                (str(ctx.get("employment_type", "")).lower().startswith("self") and not ctx.get("business_docs_uploaded", False))
                or ((not str(ctx.get("employment_type", "")).lower().startswith("self")) and not ctx.get("salary_slip_uploaded", False))
            ):
                is_self = str(ctx.get("employment_type", "")).lower().startswith("self")
                if is_self and not ctx.get("business_docs_uploaded", False):
                    if (("itr" in lower_msg or "gst" in lower_msg) and ("uploaded" in lower_msg or "done" in lower_msg)):
                        session_id = ctx.get("session_id", "demo")
                        _ = self.file_service.upload_kyc_document(ctx["customer_id"], session_id, "ITR_GST")
                        ctx["business_docs_uploaded"] = True
                        reply = (
                            "ITR/GST document received. ✅\n"
                            "Finally, please share your PAN card.\n"
                            "Type **`pan uploaded`** after you’ve shared it."
                        )
                    else:
                        reply = (
                            "Please share your ITR or GST return.\n"
                            "Type **`itr uploaded`** or **`gst uploaded`** after you’ve shared it."
                        )
                elif (not is_self) and (not ctx.get("salary_slip_uploaded", False)):
                    if any(k in lower_msg for k in ["uploaded", "upload", "done"]):
                        result = self.file_service.upload_salary_slip(ctx["customer_id"])
                        ctx["salary_slip_uploaded"] = True
                        ctx["salary_slip_file_id"] = result.get("file_id")
                        reply = (
                            f"Got it — your salary slip is received (File ID: {result['file_id']}). ✅\n"
                            "Finally, please share your PAN card.\n"
                            "Type **`pan uploaded`** after you’ve shared it."
                        )
                    else:
                        reply = (
                            "Please share your most recent salary slip.\n"
                            "👉 In this demo, either attach a file using the upload button, or type **`uploaded`** after you’ve shared it."
                        )
                
            # 4) PAN card
            elif not ctx.get("pan_card_uploaded", False):
                if ("pan" in lower_msg and ("uploaded" in lower_msg or "done" in lower_msg)):
                    session_id = ctx.get("session_id", "demo")
                    _ = self.file_service.upload_kyc_document(ctx["customer_id"], session_id, "PAN_CARD")
                    ctx["pan_card_uploaded"] = True

                    # If all required documents are now uploaded, show the requested congratulations message
                    docs_ok = (
                        ctx.get("bank_statement_uploaded")
                        and ctx.get("id_address_proof_uploaded")
                        and (ctx.get("salary_slip_uploaded") or ctx.get("business_docs_uploaded"))
                        and ctx.get("pan_card_uploaded")
                    )
                    if docs_ok:
                        # Present final offer and wait for explicit user proceed before moving on
                        ctx["kyc_status"] = ctx.get("kyc_status") or "COMPLETED"
                        ctx["credit_check_consent"] = True
                        ctx["awaiting_proceed"] = True

                        # Build final offer summary from context
                        offer = ctx.get("chosen_offer", {})
                        amt = ctx.get("loan_amount_requested") or 0
                        tenure = ctx.get("loan_tenure_requested") or 0
                        rate = offer.get("base_interest", 0)
                        proc_pct = offer.get("processing_fee_pct", 0)
                        try:
                            proc_fee = round(float(amt) * float(proc_pct) / 100.0) if amt and proc_pct else 0
                        except Exception:
                            proc_fee = 0
                        emi_val = None
                        try:
                            emi_val = (ctx.get("underwriting_result") or {}).get("emi")
                        except Exception:
                            emi_val = None

                        summary = [
                            "Congratulations!",
                            "Your KYC details and submitted documents have been successfully verified through CIBIL and authorized government sources.",
                            "",
                            "Here is your final offer:",
                            f"• Loan Amount: ₹{amt:,.0f}",
                            f"• Tenure: {int(tenure)} months",
                            f"• Interest Rate: {rate}% p.a.",
                            f"• Processing Fee: ₹{proc_fee:,.0f} ({proc_pct}%)",
                        ]
                        if isinstance(emi_val, (int, float)) and emi_val > 0:
                            summary.append(f"• Estimated EMI: ₹{emi_val:,.2f}")
                        summary += [
                            "",
                            "You’ve cleared this verification step, and your loan application is now moving forward to the final approval stage.",
                            "",
                            "Do you have any questions about the offer? You can ask them now, or click the Help button (the little question mark at the bottom-right) and type your query.",
                            "When you’re ready to continue, please type **`proceed`** to generate your sanction letter.",
                        ]
                        reply = "\n".join(summary)
                    else:
                        # Build a friendly loan summary using chosen offer (if available)
                        offer = ctx.get("chosen_offer", {})
                        amt = ctx.get("loan_amount_requested") or 0
                        tenure = ctx.get("loan_tenure_requested") or 0
                        rate = offer.get("base_interest", 0)
                        proc_pct = offer.get("processing_fee_pct", 0)
                        try:
                            proc_fee = round(float(amt) * float(proc_pct) / 100.0) if amt and proc_pct else 0
                        except Exception:
                            proc_fee = 0
                        # Life insurance fee (0.5%) if opted in
                        life_fee = 0
                        try:
                            if str(ctx.get("life_insurance", "")).lower() in ["opted in", "yes", "true"]:
                                life_fee = round(float(amt) * 0.005)
                        except Exception:
                            life_fee = 0
                        # Compose summary
                        summary_lines = [
                            "All documents are received. ✅",
                            "",
                            "Here’s a quick summary of your loan:",
                            f"• Loan Amount: ₹{amt:,.0f}",
                            f"• Tenure: {int(tenure)} months",
                            f"• Interest Rate: {rate}% p.a.",
                            f"• Processing Fee: ₹{proc_fee:,.0f} ({proc_pct}%)",
                        ]
                        if life_fee > 0:
                            summary_lines.append(f"• Life Insurance Fee: ₹{life_fee:,.0f} (if you opt in)")
                        summary_lines += [
                            "",
                            "💬 **Questions?** You can click the Help (question mark) button at the bottom-right and type your query — I’ll answer without interrupting your journey.",
                            "",
                            "🔒 **Next step (required):** Please type **`i confirm`** so I can use your information to fetch your credit score (CIBIL) and continue your loan application.",
                            "💡 After that, when everything looks good, please type **`proceed`** so we can generate your sanction letter.",
                            "(Tip: just type exactly: `i confirm`, then later type exactly: `proceed`)",
                        ]
                        reply = "\n".join(summary_lines)
                        ctx["awaiting_verification_confirm"] = True
                else:
                    reply = (
                        "Please upload your PAN card.\n"
                        "Type **`pan uploaded`** after you’ve shared it."
                    )
            # 5) Final confirmation to proceed
            else:
                if ctx.get("awaiting_verification_confirm"):
                    if lower_msg.strip() in ["i confirm", "confirm", "i confirm."]:
                        ctx["credit_check_consent"] = True
                        ctx["awaiting_verification_confirm"] = False
                        ctx["awaiting_proceed"] = True
                        reply = (
                            "✅ Thank you for confirming.\n\n"
                            "I have noted your consent and prepared your application.\n\n"
                            "If you have any questions about your offer, please ask now.\n\n"
                            "When you’re ready, type **`proceed`** and I will move forward to generate your sanction letter."
                        )
                    else:
                        reply = (
                            "Please type **`i confirm`** to allow me to use your information to fetch your credit score (CIBIL) and proceed."
                        )
                elif lower_msg.strip() == "proceed" and (ctx.get("awaiting_proceed") or ctx.get("verification_done") is False or ctx.get("verification_done") is None):
                    # Start bank details collection before proceeding to sanction
                    ctx["awaiting_proceed"] = False
                    ctx["awaiting_bank_details"] = True
                    ctx.pop("bank_ifsc", None)
                    ctx.pop("bank_account", None)
                    reply = (
                        "Before we generate your sanction letter, please share your bank details for disbursal.\n\n"
                        "1) Please provide your IFSC code (e.g., HDFC0001234)."
                    )

                # While awaiting bank details, capture IFSC and account number step-by-step
                elif ctx.get("awaiting_bank_details"):
                    import re as _re
                    if not ctx.get("bank_ifsc"):
                        # Try to extract IFSC: 4 letters + 0 + 6 alphanumerics (standard pattern)
                        m = _re.search(r"\b([A-Za-z]{4}0[0-9A-Za-z]{6})\b", user_msg or "")
                        if m:
                            ctx["bank_ifsc"] = m.group(1).upper()
                            reply = (
                                f"Thanks. IFSC set to {ctx['bank_ifsc']}.\n\n"
                                "2) Now please provide your bank account number (9 to 18 digits)."
                            )
                        else:
                            reply = (
                                "I didn't catch a valid IFSC. It should look like 4 letters, a zero, then 6 characters (e.g., SBIN0001234).\n"
                                "Please re-enter your IFSC code."
                            )
                    elif not ctx.get("bank_account"):
                        # Extract account number: 9-18 digits
                        m = _re.search(r"\b(\d{9,18})\b", user_msg or "")
                        if m:
                            ctx["bank_account"] = m.group(1)
                            # Ask for final confirmation before generating the sanction letter
                            ctx["awaiting_sanction_confirm"] = True
                            reply = (
                                "Thanks. I've recorded your bank details.\n\n"
                                f"IFSC: {ctx['bank_ifsc']}\n"
                                f"Account: ****{ctx['bank_account'][-4:]}\n\n"
                                "Please type **`confirm`** to generate your sanction letter, or re-enter details to correct them."
                            )
                        else:
                            reply = (
                                "Please enter a valid bank account number (9 to 18 digits)."
                            )

                # Final confirmation to generate sanction letter
                elif ctx.get("awaiting_sanction_confirm") and lower_msg.strip() in ["confirm", "confirm.", "yes", "generate", "proceed"]:
                    ctx["awaiting_sanction_confirm"] = False
                    ctx["awaiting_bank_details"] = False
                    ctx["verification_done"] = True
                    ctx["stage"] = "UNDERWRITING"
                    reply = "Great! Proceeding to the next step and generating your sanction letter..."
            
        # Step 4: Only mark verification as done when all items are complete AND user has finished bank details and confirmed
        if (
            ctx.get("kyc_status") == "COMPLETED"
            and (ctx.get("salary_slip_uploaded") or ctx.get("business_docs_uploaded"))
            and ctx.get("id_address_proof_uploaded")
            and ctx.get("bank_statement_uploaded")
            and ctx.get("credit_check_consent")
            and not ctx.get("awaiting_proceed")
            and not ctx.get("awaiting_bank_details")
            and not ctx.get("awaiting_sanction_confirm")
        ):
            if not ctx.get("verification_done"):
                ctx["verification_done"] = True
                if not reply:
                    reply = "Verification completed successfully! Moving to eligibility check..."
        
        # Publish event
        self.event_bus.publish_event("VERIFICATION_UPDATE", ctx.copy(), ctx["customer_id"])
        
        return reply, ctx

