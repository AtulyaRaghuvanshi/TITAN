from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from config import SANCTION_OUTPUT_DIR


def generate_sanction_letter(state: Dict[str, Any]) -> str:
    """Generate a small sanction letter. Falls back to .txt if fpdf is unavailable."""
    SANCTION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    profile = state["profile"]
    customer_id = profile.get("customer_id", "UNKNOWN")
    pdf_path = SANCTION_OUTPUT_DIR / f"{customer_id}_sanction_letter.pdf"

    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(15, 15, 15)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Loan Sanction Letter", ln=1, align="C")
        pdf.ln(8)

        pdf.set_font("Arial", size=11)
        rows = [
            ("Date", datetime.now().strftime("%d/%m/%Y")),
            ("Customer ID", customer_id),
            ("Customer Name", profile.get("name", "Customer")),
            ("Decision", state.get("decision", "PENDING")),
            ("Approved Amount", f"Rs. {state.get('approved_amount', 0):,.0f}"),
            ("Tenure", f"{profile.get('tenure_months', 0)} months"),
            ("Interest Rate", f"{state.get('interest_rate', 0)}% p.a."),
            ("EMI", f"Rs. {state.get('emi', 0):,.2f}"),
            ("FOIR", f"{state.get('foir_percent', 0):.2f}%"),
        ]
        for label, value in rows:
            pdf.cell(55, 8, f"{label}:", border=0)
            pdf.cell(0, 8, str(value), ln=1)

        pdf.ln(6)
        pdf.multi_cell(
            0,
            7,
            "This is a system-generated sanction letter created by the agentic "
            "loan approval pipeline. Final disbursal is subject to bank policy.",
        )
        pdf.output(str(pdf_path))
        return str(pdf_path)
    except Exception:
        txt_path = Path(str(pdf_path).replace(".pdf", ".txt"))
        txt_path.write_text(
            "\n".join(
                [
                    "Loan Sanction Letter",
                    f"Customer: {profile.get('name', 'Customer')}",
                    f"Decision: {state.get('decision', 'PENDING')}",
                    f"Approved Amount: Rs. {state.get('approved_amount', 0):,.0f}",
                    f"EMI: Rs. {state.get('emi', 0):,.2f}",
                ]
            ),
            encoding="utf-8",
        )
        return str(txt_path)

