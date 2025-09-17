import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.main import ContextToggles, build_profile


def _profile(job_copy: str, context: ContextToggles | None = None):
    return build_profile(job_copy, job_copy, job_copy, context)


def test_frontline_support_keywords_surface_expected_attributes():
    text = (
        "We need a first point of contact who can troubleshoot, escalate when required, "
        "and remain calm under pressure while providing caring updates."
    )
    profile = _profile(text)
    strength_names = [item.name for item in profile.strengths]
    value_names = [item.name for item in profile.values]
    expected_strengths = {"Empathy", "Communication", "Adaptability", "Responsibility", "Restorative"}
    expected_values = {"Caring", "Calm", "Trustworthy", "Friendly", "Patient"}
    assert expected_strengths.issubset(set(strength_names))
    assert expected_values.issubset(set(value_names))


def test_domain_diversification_caps_strengths():
    text = (
        "Own outcomes, take accountability, resolve escalations, ensure strict SLA discipline, "
        "and deliver process excellence with consistent handovers."
    )
    profile = _profile(text)
    domain_counts: dict[str, int] = {}
    for item in profile.strengths:
        domain_counts[item.domain] = domain_counts.get(item.domain, 0) + 1
    for domain, count in domain_counts.items():
        if domain in {"Executing", "Influencing", "Relationship Building", "Strategic Thinking"}:
            assert count <= 2


def test_context_toggles_shift_scores():
    text = "Diagnose incidents, troubleshoot integrations, document fixes, and manage technical escalations."
    baseline = _profile(text)
    toggled = _profile(text, ContextToggles(technical_complexity=1.0))
    baseline_strength_scores = {item.name: item.score for item in baseline.strengths}
    toggled_strength_scores = {item.name: item.score for item in toggled.strengths}
    assert toggled_strength_scores.get("Restorative", 0) >= baseline_strength_scores.get("Restorative", 0)
