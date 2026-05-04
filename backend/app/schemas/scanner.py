from typing import Any

from pydantic import BaseModel, Field, model_validator


class ScannerDecisionRule(BaseModel):
    key: str
    score: float | None = None
    max_score: float | None = None
    threshold: float | None = None
    passed: bool | None = None


class ScannerDecision(BaseModel):
    version: str = "oneil_core_us_etf_v2"
    strategy: str = "oneil_core_us_etf"
    decision: str
    score: float | None = None
    total_score: float | None = None
    setup_type: str | None = None
    setup_grade: str | None = None
    validation_status: str | None = "shadow_only"
    trigger_price: float | None = None
    initial_stop: float | None = None
    passed_rules: list[ScannerDecisionRule] = Field(default_factory=list)
    failed_rules: list[ScannerDecisionRule] = Field(default_factory=list)
    watch_reasons: list[str] = Field(default_factory=list)
    upgrade_conditions: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _drop_unknown_null_lists(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        payload = dict(data)
        for key in ("passed_rules", "failed_rules", "watch_reasons", "upgrade_conditions", "risk_notes"):
            if payload.get(key) is None:
                payload[key] = []
        return payload

    @model_validator(mode="after")
    def _mirror_score_fields(self) -> "ScannerDecision":
        if self.score is None and self.total_score is not None:
            self.score = self.total_score
        if self.total_score is None and self.score is not None:
            self.total_score = self.score
        return self

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ScannerDecision":
        return cls.model_validate(payload)
