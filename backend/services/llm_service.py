import os
from typing import Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime
    OpenAI = None  # type: ignore


class LLMService:
    """
    Thin wrapper around OpenAI chat completions.

    This is OPTIONAL – if OPENAI_API_KEY is not set or openai isn't installed,
    the service will be disabled and the system will fall back to rule-based replies.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = bool(api_key and OpenAI is not None)
        self.model = model
        self._client: Optional["OpenAI"] = None

        if self.enabled:
            self._client = OpenAI(api_key=api_key)

    def is_enabled(self) -> bool:
        return self.enabled and self._client is not None

    def rewrite_reply(self, user_message: str, system_reply: str, context: dict) -> str:
        """
        Use the LLM to rewrite the rule-based reply in a more natural, conversational way
        WITHOUT changing the actual steps, decisions, or numbers.
        """
        if not self.is_enabled():
            return system_reply

        # Safety net: never send extremely large payloads
        ctx_excerpt = str(context)[:2000]

        prompt_system = (
            "You are a loan-journey assistant. You receive:\n"
            "1) The user's latest message.\n"
            "2) A rule-based backend reply that encodes the exact business logic and stages.\n"
            "3) A compact context dictionary.\n\n"
            "Your job:\n"
            "- Rewrite the reply to be friendly and natural.\n"
            "- Keep ALL stages, decisions (APPROVED/REFERRED/REJECTED), "
            "amounts, tenures, interest rates, FOIR, and explanations EXACTLY the same.\n"
            "- You may rephrase sentences and add brief clarifications, "
            "but you MUST NOT change any numbers, decisions, or required next actions.\n"
            "- If the backend reply already asks the user to type specific keywords "
            "(like 'confirm' or 'uploaded'), keep those exact instructions.\n"
        )

        messages = [
            {"role": "system", "content": prompt_system},
            {
                "role": "user",
                "content": (
                    f"User message: {user_message}\n\n"
                    f"Backend reply:\n{system_reply}\n\n"
                    f"Context (truncated):\n{ctx_excerpt}"
                ),
            },
        ]

        try:
            resp = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=400,
            )
            content = resp.choices[0].message.content
            return content or system_reply
        except Exception:
            # Fail open – if LLM call fails, fall back to original reply
            return system_reply


