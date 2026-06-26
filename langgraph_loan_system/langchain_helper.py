from typing import Any, Dict


def build_decision_summary(state: Dict[str, Any]) -> str:
    """Use LangChain prompt formatting when available; otherwise use a plain string."""
    profile = state.get("profile", {})
    data = {
        "name": profile.get("name", "Customer"),
        "decision": state.get("decision", "PENDING"),
        "credit_score": profile.get("credit_score", 0),
        "foir": state.get("foir_percent", 0),
        "reason": state.get("reason", "Pipeline completed."),
    }

    try:
        from langchain.prompts import PromptTemplate

        template = PromptTemplate.from_template(
            "{name}: {decision}. Credit score {credit_score}, FOIR {foir}%. {reason}"
        )
        return template.format(**data)
    except Exception:
        return (
            f"{data['name']}: {data['decision']}. "
            f"Credit score {data['credit_score']}, FOIR {data['foir']}%. {data['reason']}"
        )

