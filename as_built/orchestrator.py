"""
The orchestrator is the heartbeat. Each tick it executes five steps in a fixed
order:

  1. Advance the clock
  2. Solicit new work from generators
  3. Dispatch tickets to idle workers
  4. Step any active workers (one action per tick per worker)
  5. Handle completions (verification + status updates)

The order matters. Work arrives at the start of a tick, work finishes at the
end. Reversing those collapses two narrative beats into one timestamp and the
replay loses its rhythm.

For v0 with one worker and stub everything, this is ~100 lines. The shape will
stay the same as components get replaced; only the implementations of
generators, workers, and the verification step change.
"""

from as_built.backlog import Backlog
from as_built.event_store import append
from as_built.events import Event
from as_built.stub_generator import StubGenerator
from as_built.stub_worker import StubWorker


class Orchestrator:
    def __init__(self) -> None:
        self.tick: int = 0
        self.backlog = Backlog()
        self.generator = StubGenerator(interval=5)
        self.worker = StubWorker()

    # ---- the tick loop ---------------------------------------------------

    def run(self, ticks: int) -> None:
        """Run the campaign for `ticks` ticks."""
        for _ in range(ticks):
            self._advance_clock()
            self._solicit_work()
            self._dispatch()
            self._step_workers()
            # NB: in this stub the worker emits its own "resolved" event on
            # the same tick as its final action, so there's nothing extra to
            # do in step 5. When the real worker arrives, verification and
            # resolution_check happen here.

    # ---- the five steps --------------------------------------------------

    def _advance_clock(self) -> None:
        self.tick += 1
        append(Event(
            tick=self.tick,
            type="tick",
            actor="orchestrator",
        ))

    def _solicit_work(self) -> None:
        emitted = self.generator.maybe_emit(self.tick)
        for ticket, sealed in emitted:
            self.backlog.add(ticket, sealed)
            append(Event(
                tick=self.tick,
                type="ticket_opened",
                actor=f"generator:{sealed.origin}",
                subject=str(ticket.id),
                payload={
                    "severity": ticket.severity,
                    "surface": ticket.surface,
                    "body": ticket.body,
                },
            ))

    def _dispatch(self) -> None:
        if not self.worker.idle:
            return
        ticket = self.backlog.next_open()
        if ticket is None:
            return
        self.backlog.set_status(ticket.id, "pulled")
        self.worker.assign(ticket)
        append(Event(
            tick=self.tick,
            type="ticket_pulled",
            actor=f"worker:{self.worker.id}",
            subject=str(ticket.id),
        ))

    def _step_workers(self) -> None:
        if self.worker.idle:
            return
        action_type, note, ticket_id, done = self.worker.step()
        append(Event(
            tick=self.tick,
            type=f"worker_action:{action_type}",
            actor=f"worker:{self.worker.id}",
            subject=str(ticket_id),
            payload={"note": note},
        ))
        if done:
            self.backlog.set_status(ticket_id, "resolved")
            append(Event(
                tick=self.tick,
                type="ticket_resolved",
                actor=f"worker:{self.worker.id}",
                subject=str(ticket_id),
                payload={"verification": "stub-pass"},
            ))
