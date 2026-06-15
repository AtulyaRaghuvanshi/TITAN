import json
import os
from typing import List, Dict, Any, Optional

OFFERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "offers.json")

class OfferMartService:
    def __init__(self):
        self.offers: List[Dict[str, Any]] = []
        self.load_offers()
    
    def load_offers(self):
        """Load offers from JSON file"""
        if os.path.exists(OFFERS_FILE):
            with open(OFFERS_FILE, 'r') as f:
                self.offers = json.load(f)
        else:
            self.offers = []
    
    def get_offers(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get offers for a specific customer"""
        customer_offers = [o for o in self.offers if o.get("customer_id") == customer_id]
        return customer_offers
    
    def get_offer_by_amount(self, customer_id: str, requested_amount: float) -> Optional[Dict[str, Any]]:
        """Get the best offer for a customer that respects the requested amount"""
        offers = self.get_offers(customer_id)
        if not offers:
            return None
        
        # Filter offers that are within the requested amount
        valid_offers = [o for o in offers if o.get("max_amount", 0) >= requested_amount]
        
        if not valid_offers:
            # If no offer matches, return the customer's max offer
            return offers[0] if offers else None
        
        # Return the offer with lowest interest rate
        return min(valid_offers, key=lambda x: x.get("base_interest", 100))

