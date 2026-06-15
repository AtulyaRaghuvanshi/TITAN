import json
import os
import math
from typing import Dict, Any, Optional

POLICIES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "policies.json")

def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Calculate EMI using standard formula"""
    if months == 0 or annual_rate == 0:
        return principal / months if months > 0 else 0
    
    r = annual_rate / (12 * 100)  # Monthly interest rate
    if r == 0:
        return principal / months
    
    emi = principal * r * math.pow(1 + r, months) / (math.pow(1 + r, months) - 1)
    return round(emi, 2)

class EligibilityService:
    """Service to evaluate loan eligibility based on policies"""
    
    def __init__(self):
        self.policies: list = []
        self.load_policies()
    
    def load_policies(self):
        """Load policies from JSON file"""
        if os.path.exists(POLICIES_FILE):
            with open(POLICIES_FILE, 'r') as f:
                self.policies = json.load(f)
        else:
            self.policies = []
    
    def get_policy_value(self, policy_name: str, config_key: str, default=None):
        """Get a specific policy configuration value"""
        for policy in self.policies:
            if policy.get("policy_name") == policy_name:
                config = policy.get("config", {})
                if isinstance(config, dict) and config_key in config:
                    return config.get(config_key, default)
                # Handle old format where config is at root level
                if config_key in policy:
                    return policy.get(config_key, default)
        return default
    
    def evaluate_eligibility(self, 
                           credit_score: int,
                           monthly_income: float,
                           existing_emi: float,
                           requested_amount: float,
                           tenure_months: int,
                           interest_rate: float = 14.0) -> Dict[str, Any]:
        """
        Evaluate loan eligibility based on policies
        
        Returns:
        {
            "approved": bool,
            "reason": str,
            "suggested_amount": float (if applicable),
            "emi": float,
            "emi_to_income_ratio": float,
            "credit_score": int
        }
        """
        # Get policy thresholds
        min_credit_score = self.get_policy_value("Credit Score Threshold", "min_credit_score_auto_approve", 720)
        max_emi_to_income_ratio = self.get_policy_value("FOIR Limits", "max_foir_auto_approve", 0.5)
        min_monthly_income = self.get_policy_value("Minimum Income", "min_monthly_income", 30000)
        max_tenure = self.get_policy_value("Maximum Tenure", "max_tenure_months", 60)
        
        # Calculate EMI
        emi = calculate_emi(requested_amount, interest_rate, tenure_months)
        total_obligation = existing_emi + emi
        emi_to_income_ratio = total_obligation / monthly_income if monthly_income > 0 else 1.0
        
        result = {
            "approved": False,
            "reason": "",
            "suggested_amount": None,
            "emi": emi,
            "emi_to_income_ratio": round(emi_to_income_ratio, 4),
            "credit_score": credit_score,
            "tenure_months": tenure_months,
            "interest_rate": interest_rate
        }
        
        # Check minimum income
        if monthly_income < min_monthly_income:
            result["reason"] = f"Monthly income ₹{monthly_income:,.0f} is below minimum requirement of ₹{min_monthly_income:,.0f}"
            return result
        
        # Check maximum tenure
        if tenure_months > max_tenure:
            result["reason"] = f"Requested tenure {tenure_months} months exceeds maximum allowed {max_tenure} months"
            return result
        
        # Check credit score
        if credit_score < min_credit_score:
            result["reason"] = f"Credit score {credit_score} is below minimum requirement of {min_credit_score}"
            return result
        
        # Check EMI to income ratio
        if emi_to_income_ratio > max_emi_to_income_ratio:
            # Try to suggest a lower amount
            suggested_amount = self._suggest_lower_amount(
                monthly_income, existing_emi, tenure_months, 
                interest_rate, max_emi_to_income_ratio
            )
            
            if suggested_amount and suggested_amount > 0:
                result["suggested_amount"] = suggested_amount
                result["reason"] = f"EMI to income ratio {emi_to_income_ratio:.2%} exceeds maximum {max_emi_to_income_ratio:.0%}. We can offer ₹{suggested_amount:,.0f} instead."
            else:
                result["reason"] = f"EMI to income ratio {emi_to_income_ratio:.2%} exceeds maximum {max_emi_to_income_ratio:.0%}"
            return result
        
        # All checks passed
        result["approved"] = True
        result["reason"] = "All eligibility criteria met"
        return result
    
    def _suggest_lower_amount(self, 
                              monthly_income: float,
                              existing_emi: float,
                              tenure_months: int,
                              interest_rate: float,
                              max_ratio: float) -> Optional[float]:
        """Suggest a lower loan amount that would pass eligibility"""
        max_total_emi = monthly_income * max_ratio
        max_new_emi = max_total_emi - existing_emi
        
        if max_new_emi <= 0:
            return None
        
        # Binary search for maximum principal that gives this EMI
        low = 0
        high = monthly_income * 10  # Reasonable upper bound
        tolerance = 1000
        
        while high - low > tolerance:
            mid = (low + high) / 2
            test_emi = calculate_emi(mid, interest_rate, tenure_months)
            
            if test_emi <= max_new_emi:
                low = mid
            else:
                high = mid
        
        return round(low, -3)  # Round to nearest thousand

