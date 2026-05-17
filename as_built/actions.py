"""
Action vocabulary for the LLM worker.

Seven actions, each with a parameter model. The worker parses LLM responses
into ParsedAction, then execute() dispatches to the right platform call.
"""

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from as_built.platform import Platform


# ---- parameter models --------------------------------------------------------

class ThinkParams(BaseModel):
    note: str


class ListModelsParams(BaseModel):
    pass


class ReadModelParams(BaseModel):
    name: str


class ReadDashboardParams(BaseModel):
    pass


class RunBuildParams(BaseModel):
    pass


class WriteModelParams(BaseModel):
    name: str
    sql: str


class SubmitResolutionParams(BaseModel):
    diagnosis: str
    postmortem_note: str


_PARAM_MODELS: dict[str, type[BaseModel]] = {
    "think": ThinkParams,
    "list_models": ListModelsParams,
    "read_model": ReadModelParams,
    "read_dashboard": ReadDashboardParams,
    "run_build": RunBuildParams,
    "write_model": WriteModelParams,
    "submit_resolution": SubmitResolutionParams,
}


# ---- parsed action -----------------------------------------------------------

class ParsedAction(BaseModel):
    action: str
    parameters: dict[str, Any]

    def typed_params(self) -> BaseModel:
        model = _PARAM_MODELS.get(self.action)
        if model is None:
            raise ValueError(f"Unknown action: {self.action!r}")
        return model.model_validate(self.parameters)


def parse_action(text: str) -> ParsedAction:
    """Parse a raw LLM response into a ParsedAction. Raises on bad JSON."""
    stripped = text.strip()
    # Strip markdown code fences if the model ignored instructions.
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        end = -1 if lines[-1].strip() == "```" else len(lines)
        stripped = "\n".join(lines[1:end])
    return ParsedAction.model_validate_json(stripped)


# ---- executor ----------------------------------------------------------------

def execute(action: ParsedAction, platform: Platform) -> tuple[dict, str]:
    """Execute a parsed action against the platform.

    Returns (event_payload, result_text):
      event_payload — written to the event log (type-specific keys).
      result_text   — recorded in the working context for the LLM to read.
    """
    params = action.typed_params()

    if action.action == "think":
        # No platform call. Payload carries the reasoning note.
        return {"note": params.note}, "ok"  # type: ignore[union-attr]

    if action.action == "list_models":
        models = platform.list_models()
        return {"model_count": len(models)}, json.dumps(models)

    if action.action == "read_model":
        sql = platform.read_model(params.name)  # type: ignore[union-attr]
        content_hash = hashlib.sha1(sql.encode()).hexdigest()[:8]
        return {"name": params.name, "content_hash": content_hash}, sql  # type: ignore[union-attr]

    if action.action == "read_dashboard":
        rows = platform.read_dashboard()
        return {"row_count": len(rows)}, json.dumps(rows)

    if action.action == "run_build":
        result = platform.build()
        stderr_tail = result.stderr[-800:] if result.stderr else ""
        payload = {"returncode": result.returncode, "stderr_tail": stderr_tail}
        result_text = json.dumps({"returncode": result.returncode, "stderr": stderr_tail})
        return payload, result_text

    if action.action == "write_model":
        old_sql = platform.read_model(params.name)  # type: ignore[union-attr]
        old_lines = len(old_sql.splitlines())
        new_lines = len(params.sql.splitlines())  # type: ignore[union-attr]
        platform.write_model(params.name, params.sql)  # type: ignore[union-attr]
        payload = {"name": params.name, "lines_changed": abs(new_lines - old_lines)}  # type: ignore[union-attr]
        return payload, f"written ({new_lines} lines)"

    if action.action == "submit_resolution":
        # Terminal action. No platform call.
        payload = {  # type: ignore[union-attr]
            "diagnosis": params.diagnosis,  # type: ignore[union-attr]
            "postmortem_note": params.postmortem_note,  # type: ignore[union-attr]
        }
        return payload, "resolution submitted"

    raise ValueError(f"No executor for action: {action.action!r}")
