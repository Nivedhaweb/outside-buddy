"""Strict schema for what the AI is allowed to return."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Mission(BaseModel):
    title: str = Field(min_length=3, max_length=60)
    goal: str = Field(min_length=10, max_length=240)
    steps: list[str] = Field(min_length=2, max_length=5)
    observe: list[str] = Field(min_length=2, max_length=4,
                               description="Observation prompts while outside")
    duration_min: int = Field(ge=5, le=90)
    where: str = Field(max_length=120, description="Suggested place (a real nearby one if given)")
    safety: str = Field(min_length=5, max_length=200)
    rainy_plan: str = Field(default="", max_length=200)
    source: str = "gemma"          # "gemma" or "offline" — shown in the UI

    @field_validator("steps", "observe")
    @classmethod
    def _trim_items(cls, v: list[str]) -> list[str]:
        out = [s.strip()[:160] for s in v if s and s.strip()]
        if len(out) < 2:
            raise ValueError("need at least 2 non-empty items")
        return out
