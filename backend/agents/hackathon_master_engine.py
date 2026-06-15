from typing import Tuple, Dict, Any
from agents.chatbot_agent import ChatbotAgent
from agents.preapproved_instant_agent import PreApprovedInstantAgent
from agents.detailed_evaluation_agent import DetailedEvaluationAgent

class HackathonMasterEngine:
    """
    Master engine for hackathon chatbot flow
    Routes between:
    1. Initial conversation (collect name, mobile, city, amount)
    2. Pre-approved instant approval path
    3. Detailed evaluation path
    """
    
    def __init__(self, chatbot_agent: ChatbotAgent,
                 preapproved_agent: PreApprovedInstantAgent,
                 detailed_eval_agent: DetailedEvaluationAgent):
        self.chatbot_agent = chatbot_agent
        self.preapproved_agent = preapproved_agent
        self.detailed_eval_agent = detailed_eval_agent
    
    def handle(self, user_msg: str, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Orchestrate the hackathon loan journey workflow"""
        # Initialize context if needed
        if not ctx:
            ctx = {}
        
        # Set default stage if not present
        stage = ctx.get("stage", "INITIAL")
        
        reply = ""
        
        # Route to appropriate agent based on stage
        if stage == "INITIAL":
            # Collect basic information (name, mobile, city, loan amount)
            reply, ctx = self.chatbot_agent.handle(user_msg, ctx)
            
            # After collecting all info, chatbot agent sets stage to PREAPPROVED_CHECK or DETAILED_EVALUATION
        
        elif stage == "PREAPPROVED_CHECK":
            # Pre-approved path - instant approval
            reply, ctx = self.preapproved_agent.handle(user_msg, ctx)
        
        elif stage == "DETAILED_EVALUATION" or stage == "SUGGEST_AMOUNT":
            # Detailed evaluation path - collect more info, upload docs, evaluate
            reply, ctx = self.detailed_eval_agent.handle(user_msg, ctx)
        
        elif stage == "END":
            if not reply:
                reply = "Thank you for using our loan application service! If you need any assistance, feel free to reach out. 😊"
        
        else:
            # Unknown stage - default to initial
            ctx["stage"] = "INITIAL"
            reply, ctx = self.chatbot_agent.handle(user_msg, ctx)
        
        return reply, ctx

