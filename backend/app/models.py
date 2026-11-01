"""Shared contract between the API, the workflow tasks and the frontend.

Mirror every change in frontend/lib/contracts.ts and data/samples/*.json in the same PR
(see architecture.md section 3). Both people must agree on changes.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

RunMode = Literal["generate", "check"]
RunStatus = Literal["queued", "running", "completed", "failed"]
Stage = Literal["queued", "variants", "filtering", "commenting", "ranking", "reality", "done"]
Action = Literal["like", "comment", "ignore", "report"]
ErrorCode = Literal["busy", "invalid_input", "render_unavailable", "not_found", "internal"]

GENERATE_MAX_CHARS = 280
CHECK_MAX_CHARS = 3000
PERSONA_TOTAL = 50


class RunRequest(BaseModel):
    mode: RunMode
    text: str = Field(min_length=1)
    demo_fail: bool = False

    @field_validator("text")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be empty")
        return v

    @model_validator(mode="after")
    def _length_by_mode(self) -> "RunRequest":
        limit = GENERATE_MAX_CHARS if self.mode == "generate" else CHECK_MAX_CHARS
        if len(self.text) > limit:
            raise ValueError(f"text must be at most {limit} characters in {self.mode} mode")
        return self


class Variant(BaseModel):
    post_id: str  # "v01".."v20"; "draft" in check mode
    voice_id: str  # from data/voices.json; "user" for the draft
    voice_label: str
    text: str


class CommentResult(BaseModel):
    event_id: str  # f"{run_id}:{post_id}:{persona_id}"
    post_id: str
    persona_id: str
    persona_name: str
    persona_label: str
    archetype: str
    action: Action
    comment: str | None = None  # only when action == "comment"
    appeal: Literal[1, 2, 3, 4, 5]
    cringe_flag: bool


class CringeFeature(BaseModel):
    id: str
    label: str
    count: int
    points: float


class CringeResult(BaseModel):
    post_id: str
    rule_score: float = Field(ge=0, le=100)
    llm_score: float | None = Field(default=None, ge=0, le=100)
    score: float = Field(ge=0, le=100)
    reasons: list[CringeFeature] = Field(default_factory=list, max_length=5)


class PostScore(BaseModel):
    post_id: str
    engagement_rate: float = Field(ge=0, le=1)
    appeal_mean: float = Field(ge=1, le=5)
    cringe: CringeResult
    base_score: float


class Reality(BaseModel):
    post_id: str
    original: str
    translation: str
    inflations: list[str] = Field(default_factory=list, max_length=3)


class Rewrite(BaseModel):
    post_id: str
    text: str
    cringe_before: float
    cringe_after: float


EventType = Literal[
    "run_started",
    "stage",
    "variants_ready",
    "finalists_selected",
    "comment",
    "cringe_scored",
    "ranking_ready",
    "reality_ready",
    "rewrite_ready",
    "demo_failure_triggered",
    "run_completed",
    "run_failed",
]


class RunEvent(BaseModel):
    """What a workflow task POSTs to the API. `seq` is assigned by the API, not the sender."""

    event_id: str
    seq: int | None = None
    type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)


# Payload shapes per event type (architecture.md section 3.3).
class RunStartedPayload(BaseModel):
    mode: RunMode
    input_text: str


class StagePayload(BaseModel):
    stage: Stage


class VariantsReadyPayload(BaseModel):
    variants: list[Variant]


class FinalistsSelectedPayload(BaseModel):
    finalist_ids: list[str]


class RankingReadyPayload(BaseModel):
    ranking: list[str]


class DemoFailurePayload(BaseModel):
    batch_id: str


class RunFailedPayload(BaseModel):
    error: str


class EmptyPayload(BaseModel):
    pass


EVENT_PAYLOADS: dict[str, type[BaseModel]] = {
    "run_started": RunStartedPayload,
    "stage": StagePayload,
    "variants_ready": VariantsReadyPayload,
    "finalists_selected": FinalistsSelectedPayload,
    "comment": CommentResult,
    "cringe_scored": PostScore,
    "ranking_ready": RankingReadyPayload,
    "reality_ready": Reality,
    "rewrite_ready": Rewrite,
    "demo_failure_triggered": DemoFailurePayload,
    "run_completed": EmptyPayload,
    "run_failed": RunFailedPayload,
}


def validate_payload(event_type: str, payload: dict[str, Any]) -> BaseModel:
    """Parse an event payload with the model for its type. Raises on an unknown type or bad shape."""
    return EVENT_PAYLOADS[event_type].model_validate(payload)


class RunState(BaseModel):
    run_id: str
    mode: RunMode
    status: RunStatus
    stage: Stage
    input_text: str
    demo_fail: bool = False
    task_run_id: str | None = None
    variants: list[Variant] = Field(default_factory=list)
    finalist_ids: list[str] = Field(default_factory=list)
    comments: list[CommentResult] = Field(default_factory=list)
    persona_total: int = PERSONA_TOTAL
    scores: list[PostScore] = Field(default_factory=list)
    ranking: list[str] = Field(default_factory=list)
    reality: Reality | None = None
    rewrite: Rewrite | None = None
    retries_seen: int = 0
    error: str | None = None
    started_at: str
    updated_at: str
    last_seq: int = 0


class ApiError(BaseModel):
    error: str
    code: ErrorCode
