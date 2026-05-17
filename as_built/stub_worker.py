"""
v0 stub worker. Picks up a ticket and "works" it for a fixed number of ticks,
emitting one think-style action per tick, then submits a fake resolution.

This is what the real LLM-driven worker replaces. The interface
(`step`) is the same — one step per tick — so swapping in the real
worker doesn't change the orchestrator at all.

Worker state machine:
  idle -> working -> idle
"""

from uuid import UUID

from as_built.tickets import Ticket


# Things the stub "does" per step. The real worker will produce these from an
# LLM action vocabulary; here they're a fixed script so we can see the rhythm.
_SCRIPT = [
    ("think", "reading the ticket"),
    ("think", "forming a hypothesis"),
    ("propose_diff", "submitting a placeholder fix"),
]


class StubWorker:
    """One-ticket-at-a-time, scripted action sequence."""

    def __init__(self, worker_id: str = "w1") -> None:
        self.id = worker_id
        self._current: UUID | None = None
        self._step_idx: int = 0

    @property
    def idle(self) -> bool:
        return self._current is None

    def assign(self, ticket: Ticket) -> None:
        assert self.idle, "worker is already busy"
        self._current = ticket.id
        self._step_idx = 0

    def step(self) -> tuple[str, str, UUID, bool]:
        """Take one action. Returns (action_type, note, ticket_id, done).

        `done` is True on the step that resolves the ticket.
        """
        assert self._current is not None, "worker is idle"
        action_type, note = _SCRIPT[self._step_idx]
        ticket_id = self._current
        self._step_idx += 1
        done = self._step_idx >= len(_SCRIPT)
        if done:
            self._current = None
        return action_type, note, ticket_id, done
