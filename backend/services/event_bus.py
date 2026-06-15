import json
import os
from datetime import datetime
from typing import Dict, List, Any

EVENTS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "events.json")

class EventBus:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.load_events()
    
    def load_events(self):
        """Load events from file if it exists"""
        if os.path.exists(EVENTS_FILE):
            try:
                with open(EVENTS_FILE, 'r') as f:
                    self.events = json.load(f)
            except:
                self.events = []
    
    def save_events(self):
        """Save events to file"""
        os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
        with open(EVENTS_FILE, 'w') as f:
            json.dump(self.events, f, indent=2)
    
    def publish_event(self, event_type: str, payload: Dict[str, Any], customer_id: str):
        """Publish an event to the event bus"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "customer_id": customer_id,
            "event_type": event_type,
            "payload": payload
        }
        self.events.append(event)
        self.save_events()
        print(f"[EventBus] Published {event_type} for customer {customer_id}")
        return event
    
    def get_events_by_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific customer"""
        return [e for e in self.events if e.get("customer_id") == customer_id]
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get all events of a specific type"""
        return [e for e in self.events if e.get("event_type") == event_type]

