"""
Thin wrapper around the Anthropic SDK pointed at Kimi Code.

One class, one method. No retries, no streaming, no tool-use protocol —
JSON-in-text is the worker's contract with the LLM.
"""

import os

from anthropic import Anthropic


class LLMClient:
    """One completion per worker step. Stateless."""

    def __init__(self) -> None:
        self._client = Anthropic(
            api_key=os.environ["KIMI_API_KEY"],
            base_url="https://api.kimi.com/coding/",
        )

    def complete(self, system: str, messages: list[dict]) -> str:
        """Send system + messages, return the assistant's text response."""
        response = self._client.messages.create(
            model="kimi-for-coding",
            system=system,
            messages=messages,
            max_tokens=2048,
        )
        return response.content[0].text
