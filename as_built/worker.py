"""
LLM-driven worker. Operates on the dbt+DuckDB platform via a JSON-in-text
action protocol. One step per tick; one action per step.

State machine: idle → working → idle (same contract as the stub it replaces).

The working context is an alternating user/assistant message list that grows
with each action. The full history is sent to the LLM on every step, giving
the model a complete view of what it has done and what each action returned.
"""

import json
from pathlib import Path
from uuid import UUID

from as_built.actions import ParsedAction, execute, parse_action
from as_built.llm_client import LLMClient
from as_built.platform import Platform
from as_built.tickets import Ticket

_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "worker.md"

_LAYER_DESCRIPTION = (
    "Models are organized in three layers:\n"
    "- staging (stg_*): light cleanup of raw sources, materialized as views\n"
    "- intermediate (int_*): joined and enriched, materialized as views\n"
    "- mart (mart_*): final tables consumed by the dashboard, materialized as tables\n"
    "The dashboard CSV is exported from mart_revenue_summary after each successful build."
)


def _load_system_prompt() -> str:
    """Read worker.md, returning only the prompt body after '## Prompt'."""
    text = _SYSTEM_PROMPT_PATH.read_text()
    marker = "## Prompt\n"
    idx = text.find(marker)
    if idx != -1:
        text = text[idx + len(marker):].strip()
    return text


def _format_work_order(ticket: Ticket, models: list[str]) -> str:
    """Build the initial user message handed to the worker at ticket start."""
    return (
        f"# Ticket\n\n"
        f"**severity:** {ticket.severity}\n"
        f"**surface:** {ticket.surface}\n\n"
        f"{ticket.body}\n\n"
        f"# Platform briefing\n\n"
        f"Available models: {', '.join(models)}\n\n"
        f"{_LAYER_DESCRIPTION}\n\n"
        f"# Memory\n\n"
        f"No lessons attached.\n"
    )


class Worker:
    """One-ticket-at-a-time LLM worker."""

    def __init__(self, worker_id: str = "w1") -> None:
        self.id = worker_id
        self._platform = Platform()
        self._llm = LLMClient()
        self._system = _load_system_prompt()
        self._current: UUID | None = None
        self._messages: list[dict] = []

    @property
    def idle(self) -> bool:
        return self._current is None

    def assign(self, ticket: Ticket, models: list[str]) -> None:
        assert self.idle, "worker is already busy"
        self._current = ticket.id
        self._messages = [
            {"role": "user", "content": _format_work_order(ticket, models)}
        ]

    def step(self) -> tuple[str, dict, UUID, bool]:
        """Take one action. Returns (action_type, event_payload, ticket_id, done).

        Calls the LLM, parses the action, executes it against the platform,
        appends both halves to the conversation, then returns for the
        orchestrator to write the event.
        """
        assert self._current is not None, "worker is idle"
        ticket_id = self._current

        raw = self._llm.complete(system=self._system, messages=self._messages)

        action: ParsedAction = parse_action(raw)
        payload, result_text = execute(action, self._platform)

        # Extend conversation: assistant's action, then the result as a user turn.
        self._messages.append({"role": "assistant", "content": raw.strip()})
        self._messages.append(
            {"role": "user", "content": json.dumps({"result": result_text})}
        )

        done = action.action == "submit_resolution"
        if done:
            self._current = None
            self._messages = []

        return action.action, payload, ticket_id, done
