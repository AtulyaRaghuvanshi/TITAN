from math import pow
from typing import Any, Dict

from config import MAX_FOIR_PERCENT, MIN_CREDIT_SCORE, MIN_MONTHLY_INCOME, REQUIRED_DOCUMENTS
from pdf_service import generate_sanction_letter


def add_step(state: Dict[str, Any], step: str) -> Dict[str, Any]:
    state.setdefault("pipeline", []).append(step)
    return state


class ProfileAgent:
    name = "profile_agent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        add_step(state, self.name)
        profile = state["profile"]
        if profile.get("age", 0) < 21:
            state.update(profile_status="FAILED", decision="REJECTED", reason="Applicant age is below policy minimum.")
        elif profile.get("monthly_income", 0) < MIN_MONTHLY_INCOME:
            state.update(profile_status="FAILED", decision="REJECTED", reason="Monthly income is below policy minimum.")
        else:
            state["profile_status"] = "PASSED"
        return state


class CreditAgent:
    name = "credit_agent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        add_step(state, self.name)
        score = int(state["profile"].get("credit_score", 0))
        if score < MIN_CREDIT_SCORE:
            state.update(credit_status="FAILED", decision="REJECTED", reason=f"Credit score {score} is below {MIN_CREDIT_SCORE}.")
        else:
            state["credit_status"] = "PASSED"
        return state


class DocumentVerificationAgent:
    name = "document_verification_agent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        add_step(state, self.name)
        documents = state["profile"].get("documents", {})

        stage_1_identity = all(documents.get(doc) for doc in ("pan", "aadhaar") if doc in REQUIRED_DOCUMENTS)
        stage_2_income = documents.get("bank_statement", False) if "bank_statement" in REQUIRED_DOCUMENTS else True
        stage_3_fraud = not documents.get("fraud_flag", False)

        state["document_checks"] = {
            "stage_1_identity": stage_1_identity,
            "stage_2_income": stage_2_income,
            "stage_3_fraud": stage_3_fraud,
        }

        if not all(state["document_checks"].values()):
            state.update(document_status="FAILED", decision="REJECTED", reason="Document verification failed.")
        else:
            state["document_status"] = "PASSED"
        return state


class UnderwritingAgent:
    name = "underwriting_agent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        add_step(state, self.name)
        profile = state["profile"]
        amount = float(profile.get("requested_amount", 0))
        tenure = int(profile.get("tenure_months", 0))
        score = int(profile.get("credit_score", 0))
        annual_rate = 10.5 if score >= 760 else 12.5 if score >= 720 else 14.0
        emi = self.calculate_emi(amount, annual_rate, tenure)
        income = float(profile.get("monthly_income", 0))
        existing_emi = float(profile.get("existing_monthly_emi", 0))
        foir = ((existing_emi + emi) / income) * 100 if income else 100

        state.update(
            interest_rate=annual_rate,
            emi=round(emi, 2),
            foir_percent=round(foir, 2),
        )

        if foir > MAX_FOIR_PERCENT:
            eligible_emi = max(0, income * (MAX_FOIR_PERCENT / 100) - existing_emi)
            state.update(
                underwriting_status="REVIEW",
                decision="REVIEW",
                reason=f"FOIR is {foir:.2f}%, above {MAX_FOIR_PERCENT}%. Lower amount or manual review required.",
                approved_amount=round(self.amount_from_emi(eligible_emi, annual_rate, tenure), 0),
            )
        else:
            state.update(
                underwriting_status="PASSED",
                decision="APPROVED",
                reason="Customer passed credit, FOIR, and document checks.",
                approved_amount=amount,
            )
        return state

    @staticmethod
    def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
        if principal <= 0 or tenure_months <= 0:
            return 0
        monthly_rate = annual_rate / (12 * 100)
        if monthly_rate == 0:
            return principal / tenure_months
        return principal * monthly_rate * pow(1 + monthly_rate, tenure_months) / (pow(1 + monthly_rate, tenure_months) - 1)

    @staticmethod
    def amount_from_emi(emi: float, annual_rate: float, tenure_months: int) -> float:
        if emi <= 0 or tenure_months <= 0:
            return 0
        monthly_rate = annual_rate / (12 * 100)
        if monthly_rate == 0:
            return emi * tenure_months
        return emi * (pow(1 + monthly_rate, tenure_months) - 1) / (monthly_rate * pow(1 + monthly_rate, tenure_months))


class SanctionAgent:
    name = "sanction_agent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        add_step(state, self.name)
        if state.get("decision") == "APPROVED":
            state["sanction_letter_path"] = generate_sanction_letter(state)
        return state


profile_agent = ProfileAgent()
credit_agent = CreditAgent()
document_agent = DocumentVerificationAgent()
underwriting_agent = UnderwritingAgent()
sanction_agent = SanctionAgent()

