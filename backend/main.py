"""FastAPI application for the Exactaform Role Profiler."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .behaviour_packs import get_behaviour_pack
from .mapping import (
    STRENGTHS_DEFINITIONS,
    VALUE_DEFINITIONS,
    calculate_profiles,
    compute_attribute_map,
    generate_interview_questions,
    score_attributes,
)

app = FastAPI(title="Exactaform Role Profiler", version="1.0.0")

FRONTEND_DIST = Path(__file__).resolve().parent / "static"


class ContextToggles(BaseModel):
    customer_volume: float = Field(0.0, ge=-1.0, le=1.5)
    technical_complexity: float = Field(0.0, ge=-1.0, le=1.5)
    strict_sla: float = Field(0.0, ge=-1.0, le=1.5)
    shift_work: float = Field(0.0, ge=-1.0, le=1.5)

    def as_dict(self) -> Dict[str, float]:
        return self.model_dump()


class ProfileRequest(BaseModel):
    job_summary: str
    key_responsibilities: str
    other_skills: str
    context: Optional[ContextToggles] = None


class AttributeBehaviour(BaseModel):
    why_it_matters: str
    risk_if_overused: str
    mitigation_and_probe: str
    do_well_indicators: List[str]
    anti_patterns: List[str]


class AttributeResponse(BaseModel):
    name: str
    domain: str
    score: float
    score_breakdown: Dict[str, float]
    evidence: List[str]
    best_exemplar: Optional[str]
    rules_fired: List[str]
    behaviour_pack: AttributeBehaviour


class InterviewQuestion(BaseModel):
    question: str
    probe: str


class ProfileResponse(BaseModel):
    strengths: List[AttributeResponse]
    values: List[AttributeResponse]
    interview_questions: List[InterviewQuestion]
    explainability: Dict[str, Any]


class AskRequest(BaseModel):
    question: str
    job_summary: str
    key_responsibilities: str
    other_skills: str
    context: Optional[ContextToggles] = None
    current_profile: Optional[Dict[str, Any]] = None


class AskResponse(BaseModel):
    answer: str
    attributes: List[Dict[str, Any]]
    changes: Optional[List[Dict[str, Any]]] = None
    profile: Optional[ProfileResponse] = None


def _with_behaviour(items: List[Dict], attribute_type: str) -> List[Dict]:
    for item in items:
        pack = get_behaviour_pack(item["name"], attribute_type, item.get("evidence", []))
        item["behaviour_pack"] = pack
    return items


def build_profile(
    job_summary: str,
    key_responsibilities: str,
    other_skills: str,
    context: Optional[ContextToggles] = None,
) -> ProfileResponse:
    toggles = context.as_dict() if context else {}
    strengths, values, explainability = calculate_profiles(
        job_summary,
        key_responsibilities,
        other_skills,
        toggles,
    )
    strengths = _with_behaviour(strengths, "strength")
    values = _with_behaviour(values, "value")
    explainability["strengths"] = {item["name"]: item for item in strengths}
    explainability["values"] = {item["name"]: item for item in values}
    interview_questions = generate_interview_questions(strengths, values)
    return ProfileResponse(
        strengths=[AttributeResponse(**item) for item in strengths],
        values=[AttributeResponse(**item) for item in values],
        interview_questions=[InterviewQuestion(**q) for q in interview_questions],
        explainability=explainability,
    )


@app.post("/profile/generate", response_model=ProfileResponse)
def generate_profile(request: ProfileRequest) -> ProfileResponse:
    return build_profile(
        request.job_summary,
        request.key_responsibilities,
        request.other_skills,
        request.context,
    )


def _find_attribute_name(text: str, names: List[str]) -> Optional[str]:
    text_lower = text.lower()
    for name in names:
        if name.lower() in text_lower:
            return name
    return None


def _rank_map(items: List[Dict[str, Any]]) -> Dict[str, int]:
    return {item["name"]: idx for idx, item in enumerate(items, start=1)}


def _prepare_changes(
    original: ProfileResponse,
    updated: ProfileResponse,
) -> List[Dict[str, Any]]:
    changes: List[Dict[str, Any]] = []
    original_strengths = _rank_map([item.model_dump() for item in original.strengths])
    updated_strengths = _rank_map([item.model_dump() for item in updated.strengths])
    for name, new_rank in updated_strengths.items():
        old_rank = original_strengths.get(name)
        if old_rank is None:
            changes.append({"attribute": name, "type": "strength", "change": "added", "new_rank": new_rank})
        elif new_rank != old_rank:
            diff = old_rank - new_rank
            direction = "up" if diff > 0 else "down"
            changes.append({
                "attribute": name,
                "type": "strength",
                "change": direction,
                "positions": abs(diff),
                "new_rank": new_rank,
            })
    original_values = _rank_map([item.model_dump() for item in original.values])
    updated_values = _rank_map([item.model_dump() for item in updated.values])
    for name, new_rank in updated_values.items():
        old_rank = original_values.get(name)
        if old_rank is None:
            changes.append({"attribute": name, "type": "value", "change": "added", "new_rank": new_rank})
        elif new_rank != old_rank:
            diff = old_rank - new_rank
            direction = "up" if diff > 0 else "down"
            changes.append({
                "attribute": name,
                "type": "value",
                "change": direction,
                "positions": abs(diff),
                "new_rank": new_rank,
            })
    return changes


@app.post("/codex/ask", response_model=AskResponse)
def ask_codex(request: AskRequest) -> AskResponse:
    toggles = request.context.as_dict() if request.context else {}
    strength_results, _ = score_attributes(
        STRENGTHS_DEFINITIONS,
        request.job_summary,
        request.key_responsibilities,
        request.other_skills,
        toggles,
    )
    value_results, _ = score_attributes(
        VALUE_DEFINITIONS,
        request.job_summary,
        request.key_responsibilities,
        request.other_skills,
        toggles,
    )
    strength_map = compute_attribute_map(
        [
            {
                "name": item["name"],
                "domain": item["domain"],
                "score": item["total_score"],
                "score_breakdown": {
                    "keyword_match": item["keyword_score_norm"],
                    "semantic_sim": item["semantic_score_norm"],
                    "role_priors": item["role_prior"],
                    "context_mods": item["context_score_norm"],
                },
                "evidence": item["evidence"],
                "best_exemplar": item["best_exemplar"],
                "rules_fired": item.get("context_rules", []),
            }
            for item in strength_results
        ]
    )
    value_map = compute_attribute_map(
        [
            {
                "name": item["name"],
                "domain": item["domain"],
                "score": item["total_score"],
                "score_breakdown": {
                    "keyword_match": item["keyword_score_norm"],
                    "semantic_sim": item["semantic_score_norm"],
                    "role_priors": item["role_prior"],
                    "context_mods": item["context_score_norm"],
                },
                "evidence": item["evidence"],
                "best_exemplar": item["best_exemplar"],
                "rules_fired": item.get("context_rules", []),
            }
            for item in value_results
        ]
    )

    all_names = list(strength_map.keys()) + list(value_map.keys())
    question = request.question.strip()
    lower_question = question.lower()
    attributes: List[Dict[str, Any]] = []

    if lower_question.startswith("why did you pick"):
        target = _find_attribute_name(lower_question, all_names)
        if target:
            source_map = strength_map if target in strength_map else value_map
            data = source_map[target]
            rules = [rule for rule in data.get("rules_fired", []) if rule]
            answer = (
                f"{target} was prioritised because the job copy referenced {', '.join(data['evidence']) or 'service cues'} "
                "and aligned with the frontline support priors."
            )
            attributes.append({"name": target, "score_breakdown": data["score_breakdown"], "evidence": data["evidence"], "rules": rules})
        else:
            answer = "I could not find that attribute in the current library."
        return AskResponse(answer=answer, attributes=attributes)

    if lower_question.startswith("why not"):
        target = _find_attribute_name(lower_question, all_names)
        if target:
            source_map = strength_map if target in strength_map else value_map
            data = source_map[target]
            answer = (
                f"{target} sat lower because its combined score was {data['score']:.2f}. "
                f"Keyword signal {data['score_breakdown']['keyword_match']:.2f} and context adjustments {data['score_breakdown']['context_mods']:.2f} were lighter than the selected top picks."
            )
            attributes.append({"name": target, "score_breakdown": data["score_breakdown"], "evidence": data["evidence"], "rules": data.get("rules_fired", [])})
        else:
            answer = "That attribute is not currently mapped."
        return AskResponse(answer=answer, attributes=attributes)

    adjustments_made = False
    updated_context = dict(toggles)
    if "increase" in lower_question or "add" in lower_question or "+" in lower_question:
        if "technical" in lower_question or "troubleshooting" in lower_question:
            updated_context["technical_complexity"] = min(1.0, toggles.get("technical_complexity", 0.0) + 0.4)
            adjustments_made = True
        if "customer" in lower_question or "volume" in lower_question:
            updated_context["customer_volume"] = min(1.0, toggles.get("customer_volume", 0.0) + 0.4)
            adjustments_made = True
        if "sla" in lower_question:
            updated_context["strict_sla"] = min(1.0, toggles.get("strict_sla", 0.0) + 0.4)
            adjustments_made = True
    if "reduce" in lower_question or "-" in lower_question:
        if "frontline" in lower_question or "contact" in lower_question or "customer" in lower_question:
            updated_context["customer_volume"] = max(-0.5, toggles.get("customer_volume", 0.0) - 0.3)
            adjustments_made = True
        if "technical" in lower_question:
            updated_context["technical_complexity"] = max(-0.5, toggles.get("technical_complexity", 0.0) - 0.3)
            adjustments_made = True
    if adjustments_made:
        context_model = ContextToggles(**updated_context)
        updated_profile = build_profile(
            request.job_summary,
            request.key_responsibilities,
            request.other_skills,
            context_model,
        )
        base_profile = request.current_profile
        if base_profile:
            original_profile = ProfileResponse(**base_profile)
        else:
            original_profile = build_profile(
                request.job_summary,
                request.key_responsibilities,
                request.other_skills,
                request.context,
            )
        changes = _prepare_changes(original_profile, updated_profile)
        answer = "Adjusted context toggles and refreshed the ranked profile."
        return AskResponse(
            answer=answer,
            attributes=[{"name": change["attribute"], "change": change["change"]} for change in changes],
            changes=changes,
            profile=updated_profile,
        )

    answer = "I noted the request. Ask about a specific attribute or suggest a what-if adjustment for more detail."
    return AskResponse(answer=answer, attributes=[])


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:

    @app.get("/", include_in_schema=False)
    def frontend_placeholder() -> Dict[str, str]:
        return {
            "detail": "Frontend build not found. Run 'npm install' and 'npm run build' from the frontend directory to serve the UI.",
        }
