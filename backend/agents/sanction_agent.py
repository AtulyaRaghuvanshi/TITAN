import os
import base64
from typing import Tuple, Dict, Any
from services.event_bus import EventBus
from fpdf import FPDF
from io import BytesIO

SANCTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "sanctions")

class SanctionAgent:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        os.makedirs(SANCTIONS_DIR, exist_ok=True)
    
    def generate_sanction_letter_instant(self, ctx: Dict[str, Any], loan: Dict[str, Any]) -> str:
        """Generate PDF sanction letter for instant pre-approved loan"""
        session_id = ctx.get("session_id", "UNKNOWN")
        customer_name = ctx.get("customer_name", "Customer")
        letter_path = os.path.join(SANCTIONS_DIR, f"{session_id}_sanction_instant.pdf")
        
        # Create PDF with proper margins
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(15, 15, 15)  # Left, Top, Right margins
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Get page width minus margins
        page_width = pdf.w - 30  # Total width minus left and right margins
        
        pdf.set_font("Arial", "B", 16)
        
        # Title
        pdf.cell(0, 10, "INSTANT LOAN SANCTION LETTER", ln=1, align="C")
        pdf.ln(10)
        
        # Customer details
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"Loan ID: {loan.get('loan_id', 'N/A')}", ln=1)
        pdf.cell(0, 8, f"Customer Name: {customer_name}", ln=1)
        if ctx.get("customer_id"):
            pdf.cell(0, 8, f"Customer ID: {ctx.get('customer_id')}", ln=1)
        pdf.ln(5)
        
        # Loan details
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Loan Details:", ln=1)
        pdf.set_font("Arial", size=11)
        
        approved_amount = loan.get("approved_amount", 0)
        interest_rate = loan.get("interest_rate", 0)
        tenure = loan.get("tenure_months", 36)
        
        pdf.cell(0, 8, f"Sanctioned Amount: Rs. {approved_amount:,.0f}", ln=1)
        pdf.cell(0, 8, f"Loan Tenure: {tenure} months", ln=1)
        pdf.cell(0, 8, f"Interest Rate: {interest_rate}% per annum", ln=1)
        pdf.ln(5)
        
        # Approval type
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Approval Type: Pre-Approved Instant Approval", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(page_width, 6, "This loan was approved instantly based on your pre-approved status.", 0, "L")
        pdf.ln(5)
        
        # Terms and conditions
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Terms & Conditions:", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(page_width, 6, "1. This sanction is valid for 30 days from the date of issue.", 0, "L")
        pdf.multi_cell(page_width, 6, "2. The loan is subject to completion of all documentation.", 0, "L")
        pdf.multi_cell(page_width, 6, "3. Interest rates are subject to change as per market conditions.", 0, "L")
        pdf.ln(5)
        
        # Footer
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "This is a system-generated document for instant approval.", ln=1, align="C")
        pdf.cell(0, 10, f"Generated on: {loan.get('approved_date', 'N/A')}", ln=1, align="C")
        
        pdf.output(letter_path)
        return letter_path
    
    def generate_sanction_letter(self, ctx: Dict[str, Any], customer_name: str) -> Tuple[str, str]:
        """Generate a single, fully-formatted Sanction Letter matching strict spec.
        - No Part 2, no APR mentions
        - Interest Type: Fixed
        - Foreclosure: 3%
        - Includes: General Details, Loan Details, Fees & Charges (A and B), Contingent Charges, Repayment Schedule, Borrower Declaration
        Returns file path and base64 string.
        """
        from datetime import datetime
        import json
        import os as os_module

        customer_id = ctx.get("customer_id", "UNKNOWN")
        letter_path = os.path.join(SANCTIONS_DIR, f"{customer_id}_sanction.pdf")

        # Pull dynamic data
        offer = ctx.get("chosen_offer", {})
        underwriting = ctx.get("underwriting_result", {})
        loan_amount = ctx.get("loan_amount_requested", 0)
        tenure_months = ctx.get("loan_tenure_requested", 0)
        interest_rate = offer.get("base_interest", 0)
        processing_fee_pct = offer.get("processing_fee_pct", 0)

        # Single source of truth for EMI: compute here with the same formula as underwriting
        try:
            from math import pow
            principal = float(loan_amount or 0)
            n = int(tenure_months or 0)
            r = float(interest_rate or 0) / (12 * 100.0)
            if principal > 0 and n > 0 and r > 0:
                emi = round(principal * r * pow(1 + r, n) / (pow(1 + r, n) - 1), 2)
            elif principal > 0 and n > 0:
                emi = round(principal / n, 2)
            else:
                emi = 0
        except Exception:
            emi = float(underwriting.get("emi", 0) or 0)

        # Persist back to context to keep UI and letter aligned
        underwriting = underwriting or {}
        underwriting["emi"] = emi
        ctx["underwriting_result"] = underwriting

        # Optional info
        customer_mobile = ctx.get("customer_mobile", "")
        if not customer_mobile:
            customers_file = os_module.path.join(os_module.path.dirname(__file__), "..", "data", "customers.json")
            if os_module.path.exists(customers_file):
                with open(customers_file, "r") as f:
                    customers = json.load(f)
                    customer = next((c for c in customers if c.get("customer_id") == customer_id), None)
                    if customer:
                        customer_mobile = str(customer.get("mobile", ""))

        current_date = datetime.now().strftime("%d/%m/%Y")
        from datetime import timedelta
        validity_from = datetime.now().strftime("%d/%m/%Y")
        validity_to = (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y")

        # Helpers
        from math import ceil

        def _num_lines(pdf_obj: FPDF, text: str, width: float, line_height: float) -> int:
            """Estimate number of lines a multi_cell would take for given width and text."""
            if text is None:
                return 1
            text = str(text)
            if text.strip() == "":
                return 1
            avg_char_width = pdf_obj.get_string_width("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") / 52.0
            if avg_char_width <= 0:
                avg_char_width = 1.0
            chars_per_line = max(1, int(width / max(avg_char_width, 0.1)))
            import textwrap
            wrapped = []
            for paragraph in text.split("\n"):
                wrapped += textwrap.wrap(paragraph, width=chars_per_line) or [""]
            return max(1, len(wrapped))

        def table_row(pdf_obj: FPDF, cols, widths, height=7, header=False, align_list=None):
            """Draw one table row. Ensure full row fits on page; otherwise add a page first."""
            if align_list is None:
                align_list = ["L"] * len(cols)

            font_style = "B" if header else ""
            pdf_obj.set_font("Arial", font_style, 10)

            # Pre-calc required height for the row
            lines_per_col = []
            for i, text in enumerate(cols):
                w = widths[i]
                lines = _num_lines(pdf_obj, text, w, height)
                lines_per_col.append(lines)
            max_lines = max(lines_per_col) if lines_per_col else 1
            required_height = max_lines * height

            bottom_y = pdf_obj.h - pdf_obj.b_margin
            cur_y = pdf_obj.get_y()

            if cur_y + required_height > bottom_y:
                pdf_obj.add_page()
                cur_y = pdf_obj.get_y()

            x0 = pdf_obj.get_x()
            y0 = cur_y

            # Write each cell starting at the same y0
            for i, text in enumerate(cols):
                w = widths[i]
                a = align_list[i] if i < len(align_list) else "L"
                pdf_obj.set_xy(x0 + sum(widths[:i]), y0)
                pdf_obj.multi_cell(w, height, str(text) if text is not None else "", border=1, align=a)

            # Move cursor to the end of the tallest cell
            pdf_obj.set_xy(x0, y0 + required_height)

        def section_header(pdf_obj: FPDF, text):
            pdf_obj.set_font("Arial", "B", 12)
            pdf_obj.cell(0, 8, text, ln=1)

        # Build PDF
        pdf = FPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)

        # ========== Page: Sanction Letter per Spec ==========
        pdf.add_page()
        page_width = pdf.w - (pdf.l_margin + pdf.r_margin)

        # Title
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Sanction Letter", ln=1, align="C")
        pdf.ln(2)

        # Header details
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Customer Name: {customer_name}", ln=1)
        if customer_mobile:
            pdf.cell(0, 6, f"Mobile Number: {customer_mobile}", ln=1)
        else:
            pdf.cell(0, 6, f"Mobile Number: ", ln=1)
        pdf.cell(0, 6, f"Sanction Letter Validity: From {validity_from} to {validity_to}", ln=1)
        pdf.ln(2)

        # KFS Part 1 heading
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 7, "Key Facts Statement - Part 1 (Interest rate & Fees/Charges)", ln=1)

        # General Details
        section_header(pdf, "General Details")
        col_w = [page_width * 0.12, page_width * 0.38, page_width * 0.5]
        table_row(pdf, ["Sl. No", "Field", "Value"], col_w, header=True, align_list=["C", "L", "L"])
        table_row(pdf, ["1", "Date of KFS", current_date], col_w)
        table_row(pdf, ["2", "Name of Lender", "Titan Bank"], col_w)
        table_row(pdf, ["3", "KFS Validity", f"From {validity_from} to {validity_to}"], col_w)
        address = ctx.get("customer_address", "")
        borrower_details = f"Name: {customer_name}\nConstitution: Individual\nAddress: {address}" if address else f"Name: {customer_name}\nConstitution: Individual"
        table_row(pdf, ["4", "Borrower Details", borrower_details], col_w)

        pdf.ln(2)
        # Loan Details Table
        section_header(pdf, "Loan Details Table")
        table_row(pdf, ["Sl. No", "Field", "Value"], col_w, header=True, align_list=["C", "L", "L"])
        proposal_number = ctx.get("proposal_number", f"APP-{customer_id}-{datetime.now().strftime('%Y%m%d')}")
        table_row(pdf, ["1", "Loan Proposal / Account / Unique Proposal Number", proposal_number + "\nType of Loan: Personal Loan"], col_w)
        table_row(pdf, ["2", "Sanctioned Loan Amount (Rs)", f"Rs {loan_amount:,.0f}"], col_w)
        table_row(pdf, ["3", "Disbursal Schedule", "100% upfront"], col_w)
        table_row(pdf, ["4", "Loan Term (months/years)", f"{tenure_months} months"], col_w)
        # Instalment details composite
        table_row(pdf, ["5", "Instalment Details", "Type of Instalments: EPI\nNumber of EPIs: {0}\nEPI Amount (Rs): {1}\nCommencement of Repayment: {2}".format(
            tenure_months, f"Rs {emi:,.2f}", validity_to
        )], col_w)
        table_row(pdf, ["6", "Interest Rate (per annum)", f"{interest_rate}%\nInterest Type: Fixed"], col_w)
        table_row(pdf, ["7", "Additional Floating-Rate Info", "Not Applicable (Loan is Fixed Rate)"], col_w)

        pdf.ln(2)
        # Fees & Charges A
        section_header(pdf, "Fees & Charges - Payable to Titan Bank (A)")
        fee_w = [page_width * 0.5, page_width * 0.2, page_width * 0.3]
        table_row(pdf, ["Fee Type", "One-time/Recurring", "Amount"], fee_w, header=True, align_list=["L", "C", "R"])

        def fmt_amount(val):
            if isinstance(val, (int, float)):
                return f"Rs {val:,.0f}"
            return val or ""

        # Processing Fee: prefer explicit value, else compute from pct (ctx or offer)
        proc_fee_val = ctx.get("processing_fee")
        if not isinstance(proc_fee_val, (int, float)):
            pct = ctx.get("processing_fee_pct")
            if not isinstance(pct, (int, float)):
                pct = processing_fee_pct
            if isinstance(pct, (int, float)) and isinstance(loan_amount, (int, float)):
                proc_fee_val = round(loan_amount * (pct / 100.0))
        table_row(pdf, ["Processing Fees", "One-time", fmt_amount(proc_fee_val)], fee_w)

        # Insurance – Life: compute fee if opted-in (0.5% of loan amount); else show Not opted / guidance
        life_ins = ctx.get("life_insurance")
        life_opted = False
        try:
            # Accept various truthy indicators like 'Opted In', 'Yes', True
            if isinstance(life_ins, str):
                lower_val = life_ins.strip().lower()
                life_opted = ("opted" in lower_val and "not" not in lower_val) or lower_val in ["yes", "y", "true"]
            elif isinstance(life_ins, bool):
                life_opted = life_ins
        except Exception:
            life_opted = False

        life_ins_amount = None
        if life_opted and isinstance(loan_amount, (int, float)):
            try:
                life_ins_amount = round(loan_amount * 0.005)  # 0.5% of loan amount
            except Exception:
                life_ins_amount = None

        if life_ins_amount is not None:
            table_row(pdf, ["Insurance Charges - Life", "One-time", fmt_amount(life_ins_amount)], fee_w)
        else:
            # Default textual status if no amount is computed
            status = life_ins if life_ins not in (None, "") else "Customer elected / Not opted"
            table_row(pdf, ["Insurance Charges - Life", "One-time", fmt_amount(status)], fee_w)

        # Insurance – General
        gen_ins = ctx.get("general_insurance")
        table_row(pdf, ["Insurance Charges - General", "One-time", fmt_amount(gen_ins)], fee_w)

        # Valuation Fees: N/A default for personal loans
        val_fee = ctx.get("valuation_fees")
        if val_fee in (None, ""):
            val_fee = "N/A for personal loan"
        table_row(pdf, ["Valuation Fees", "One-time", fmt_amount(val_fee)], fee_w)

        # Stamp Duty: placeholder if unknown
        stamp_duty = ctx.get("stamp_duty")
        if stamp_duty in (None, ""):
            stamp_duty = "To be charged as per Stamp Act (state)"
        table_row(pdf, ["Stamp Duty", "One-time", fmt_amount(stamp_duty)], fee_w)

        # Broken Period Interest (BPI): compute if bpi_days provided or sanction/disbursal dates known
        bpi_val = ctx.get("BPI")
        if not isinstance(bpi_val, (int, float)):
            days = ctx.get("bpi_days")
            try:
                if days is None and ctx.get("disbursal_date") and ctx.get("sanction_date"):
                    from datetime import datetime as dt
                    sd = dt.strptime(ctx.get("sanction_date"), "%d/%m/%Y")
                    dd = dt.strptime(ctx.get("disbursal_date"), "%d/%m/%Y")
                    days = max(0, (dd - sd).days)
                if isinstance(days, int) and days > 0 and isinstance(loan_amount, (int, float)) and isinstance(interest_rate, (int, float)):
                    bpi_val = round(loan_amount * (interest_rate/100.0) / 365.0 * days)
            except Exception:
                pass
        table_row(pdf, ["Broken Period Interest", "One-time", fmt_amount(bpi_val)], fee_w)

        # Add-on products
        table_row(pdf, ["One Assist Plan Amount", "One-time", fmt_amount(ctx.get("one_assist"))], fee_w)
        table_row(pdf, ["Documentation Charges", "One-time", fmt_amount(ctx.get("documentation_charges"))], fee_w)

        pdf.ln(2)
        # Fees & Charges B
        section_header(pdf, "Fees & Charges - Payable to Third Party through Titan Bank (B)")
        table_row(pdf, ["Fee Type", "One-time/Recurring", "Amount"], fee_w, header=True, align_list=["L", "C", "R"])
        table_row(pdf, ["CPP Plan Amount", "One-time", fmt_amount(ctx.get("cpp"))], fee_w)
        table_row(pdf, ["Health Insurance", "One-time", fmt_amount(ctx.get("health_insurance"))], fee_w)
        table_row(pdf, ["Tata AIG 360", "One-time", fmt_amount(ctx.get("tata_aig"))], fee_w)

        pdf.ln(2)
        # Contingent Charges
        section_header(pdf, "Contingent Charges")
        sub_w = [page_width * 0.6, page_width * 0.4]
        table_row(pdf, ["Penal Charges", ""], sub_w, header=True)
        table_row(pdf, ["Charge Type", "Value"], sub_w, header=True)
        table_row(pdf, ["Late payment", "3% per month on defaulted amount"], sub_w)

        pdf.ln(1)
        table_row(pdf, ["Other Penal Charges", ""], sub_w, header=True)
        table_row(pdf, ["Item", "Charge"], sub_w, header=True)
        table_row(pdf, ["Cheque Dishonour", "Rs 600 per instance"], sub_w)
        table_row(pdf, ["Mandate Rejection", "Rs 450"], sub_w)

        pdf.ln(1)
        table_row(pdf, ["Foreclosure Charges (Override everything to: 3% flat)", ""], sub_w, header=True)
        table_row(pdf, ["Condition", "Charge"], sub_w, header=True)
        table_row(pdf, ["Anytime during tenure", "3% of principal outstanding"], sub_w)

        pdf.ln(1)
        table_row(pdf, ["Other Charges", ""], sub_w, header=True)
        table_row(pdf, ["Type", "Amount"], sub_w, header=True)
        table_row(pdf, ["Payment Instrument Swapping", "Rs 550"], sub_w)
        table_row(pdf, ["Cancellation Charges", "2% of loan amount or Rs 5750 (whichever higher)"], sub_w)
        table_row(pdf, ["Duplicate Repayment Schedule", "Rs 550"], sub_w)
        table_row(pdf, ["Duplicate NOC", "Rs 550"], sub_w)
        table_row(pdf, ["Statement of Account (SOA)", "Customer Portal - Nil | Branch Walk-in - Rs 250"], sub_w)
        table_row(pdf, ["Foreclosure Report", "Nil (Portal) / Rs 199 (Branch)"], sub_w)
        table_row(pdf, ["Switch Fee", "Not applicable (Loan is fixed rate)"], sub_w)

        # Repayment Schedule
        pdf.add_page()
        section_header(pdf, "Repayment Schedule")
        sched_w = [page_width * 0.12, page_width * 0.18, page_width * 0.18, page_width * 0.18, page_width * 0.18, page_width * 0.16]
        table_row(pdf, ["Instalment No.", "Due Date", "Principal Component", "Interest Component", "Outstanding Principal", "EMI Amount"], sched_w, header=True, align_list=["C"]*6)

        # Build amortization schedule
        from math import pow
        principal = float(loan_amount or 0)
        annual_rate = float(interest_rate or 0)
        n = int(tenure_months or 0)
        r = annual_rate / (12 * 100.0)
        emi_amt = float(emi or 0)
        # If emi not provided (edge case), compute
        if emi_amt <= 0 and r > 0 and n > 0:
            emi_amt = principal * r * pow(1 + r, n) / (pow(1 + r, n) - 1)
        from datetime import datetime as dt
        start_date = dt.strptime(validity_to, "%d/%m/%Y")  # start from validity end (as provided)
        outstanding = principal
        for i in range(1, n + 1):
            interest_comp = round(outstanding * r, 2)
            principal_comp = round(emi_amt - interest_comp, 2) if emi_amt > 0 else 0
            # Avoid negative on last row due to rounding
            if i == n:
                principal_comp = round(outstanding, 2)
                emi_show = round(principal_comp + interest_comp, 2)
            else:
                emi_show = round(emi_amt, 2)
            outstanding = max(0.0, round(outstanding - principal_comp, 2))
            due_date = (start_date.replace(day=min(start_date.day, 28)) + timedelta(days=30 * i)).strftime("%d/%m/%Y")
            table_row(
                pdf,
                [str(i), due_date, f"Rs {principal_comp:,.2f}", f"Rs {interest_comp:,.2f}", f"Rs {outstanding:,.2f}", f"Rs {emi_show:,.2f}"],
                sched_w,
                align_list=["C", "C", "R", "R", "R", "R"],
            )

        pdf.ln(2)
        # Borrower Declaration
        section_header(pdf, "Borrower Declaration")
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(page_width, 6, "I hereby confirm that I have thoroughly read and understood the above Key Facts Statement and accept the terms of the sanctioned loan.")
        pdf.ln(2)
        decl_w = [page_width * 0.7, page_width * 0.3]
        table_row(pdf, ["Borrower Signature: __________________________", f"Date: {current_date}"], decl_w)

        # Save & base64
        pdf.output(letter_path)

        # Robustly get bytes from fpdf2 output (may be bytearray or str depending on version)
        pdf_out = pdf.output(dest='S')
        if isinstance(pdf_out, (bytes, bytearray)):
            pdf_bytes = bytes(pdf_out)
        else:
            pdf_bytes = str(pdf_out).encode('latin1')
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return letter_path, pdf_base64
    
    def generate_sanction_letter_evaluated(self, ctx: Dict[str, Any], loan: Dict[str, Any], evaluation: Dict[str, Any]) -> str:
        """Generate PDF sanction letter for evaluated loan"""
        session_id = ctx.get("session_id", "UNKNOWN")
        customer_name = ctx.get("customer_name", "Customer")
        letter_path = os.path.join(SANCTIONS_DIR, f"{session_id}_sanction_evaluated.pdf")
        
        # Create PDF with proper margins
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(15, 15, 15)  # Left, Top, Right margins
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Get page width minus margins
        page_width = pdf.w - 30  # Total width minus left and right margins
        
        pdf.set_font("Arial", "B", 16)
        
        # Title
        pdf.cell(0, 10, "LOAN SANCTION LETTER", ln=1, align="C")
        pdf.ln(10)
        
        # Customer details
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"Loan ID: {loan.get('loan_id', 'N/A')}", ln=1)
        pdf.cell(0, 8, f"Customer Name: {customer_name}", ln=1)
        if ctx.get("customer_id"):
            pdf.cell(0, 8, f"Customer ID: {ctx.get('customer_id')}", ln=1)
        pdf.ln(5)
        
        # Loan details
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Loan Details:", ln=1)
        pdf.set_font("Arial", size=11)
        
        approved_amount = loan.get("approved_amount", 0)
        interest_rate = loan.get("interest_rate", 0)
        tenure = loan.get("tenure_months", 36)
        emi = evaluation.get("emi", 0)
        
        pdf.cell(0, 8, f"Sanctioned Amount: Rs. {approved_amount:,.0f}", ln=1)
        pdf.cell(0, 8, f"Loan Tenure: {tenure} months", ln=1)
        pdf.cell(0, 8, f"Interest Rate: {interest_rate}% per annum", ln=1)
        pdf.cell(0, 8, f"EMI: Rs. {emi:,.2f}", ln=1)
        pdf.ln(5)
        
        # Approval type
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Approval Type: After Evaluation", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(page_width, 6, "This loan was approved after detailed evaluation of your profile, documents, and eligibility criteria.", 0, "L")
        pdf.ln(5)
        
        # Terms and conditions
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Terms & Conditions:", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(page_width, 6, "1. This sanction is valid for 30 days from the date of issue.", 0, "L")
        pdf.multi_cell(page_width, 6, "2. The loan is subject to completion of all documentation.", 0, "L")
        pdf.multi_cell(page_width, 6, "3. Interest rates are subject to change as per market conditions.", 0, "L")
        pdf.ln(5)
        
        # Footer
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "This is a system-generated document after evaluation.", ln=1, align="C")
        pdf.cell(0, 10, f"Generated on: {loan.get('approved_date', 'N/A')}", ln=1, align="C")
        
        pdf.output(letter_path)
        return letter_path
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Handle sanction agent logic"""
        reply = ""
        
        # Get customer name (for demo, we'll use customer_id if name not available)
        customer_name = ctx.get("customer_name", f"Customer {ctx['customer_id']}")
        
        # Generate sanction letter
        if ctx.get("decision") == "APPROVED" and not ctx.get("sanction_letter_url"):
            letter_path, pdf_base64 = self.generate_sanction_letter(ctx, customer_name)
            ctx["sanction_letter_url"] = letter_path
            ctx["sanction_letter_pdf"] = pdf_base64  # Store base64 PDF in context
            
            reply = f"""🎉 **Congratulations! Your Loan is Sanctioned!**

Your sanction letter PDF has been generated successfully.

📄 Your sanction letter is attached below. You can download it directly from the chat.

**Next Steps:**
1. Review your sanction letter PDF
2. Complete the documentation process
3. Funds will be disbursed within 2-3 business days

Thank you for choosing us for your financial needs!

Your loan journey is now complete. 🎊"""
            
            ctx["stage"] = "END"
        
        elif ctx.get("sanction_letter_url"):
            reply = "Your sanction letter has already been generated. Please check the link provided earlier."
        
        else:
            reply = "Sanction letter generation is in progress..."
        
        # Publish event
        self.event_bus.publish_event("SANCTION_GENERATED", ctx.copy(), ctx["customer_id"])
        
        return reply, ctx

