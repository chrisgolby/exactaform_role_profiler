"""Behaviour pack templates for strengths and values."""
from __future__ import annotations

from typing import Dict, List

DEFAULT_STRENGTH_PACK = {
    "why": "This strength underpins reliable customer support delivery.",
    "risk": "If overplayed it may crowd out colleagues or stall decisions.",
    "mitigation": "Set clear guardrails and ask for a recent example using STAR to explore balance.",
    "do_well": [
        "Sets expectations clearly",
        "Shares context with peers",
        "Escalates before issues worsen",
    ],
    "anti_patterns": [
        "Takes over without alignment",
        "Ignores data points",
        "Lets workload bottleneck",
    ],
}

DEFAULT_VALUE_PACK = {
    "why": "This value shapes how the colleague shows up for service users.",
    "risk": "If unchecked it could tip into unhelpful extremes.",
    "mitigation": "Clarify boundaries and test with a STAR-style probe to confirm judgement.",
    "do_well": [
        "Aligns actions to policy",
        "Collaborates smoothly",
        "Stays open to feedback",
    ],
    "anti_patterns": [
        "Overpromises",
        "Applies personal lens only",
        "Dismisses different working styles",
    ],
}

STRENGTH_BEHAVIOUR_LIBRARY: Dict[str, Dict[str, List[str]]] = {
    "Empathy": {
        "why": "Empathy keeps contact calm and human, especially when callers are escalated or anxious.",
        "risk": "Too much empathy can lead to emotional drain or blurred boundaries.",
        "mitigation": "Rotate tricky caseloads, pair with clear handovers, and probe: 'Describe a situation where you had to stay empathetic yet resolve the issue swiftly.'",
        "do_well": [
            "Names emotions early",
            "Uses active listening cues",
            "Balances tone with policy",
        ],
        "anti_patterns": [
            "Absorbs issues without closure",
            "Agrees to scope creep",
            "Takes feedback personally",
        ],
    },
    "Communication": {
        "why": "Clear communication gives customers and colleagues confidence during triage and escalation.",
        "risk": "If overused it may drown others in updates or overlook nuance.",
        "mitigation": "Anchor updates to what the audience needs and probe: 'Talk me through a time you had to simplify technical language for a customer.'",
        "do_well": [
            "Frames status and next steps",
            "Uses plain UK English",
            "Checks understanding",
        ],
        "anti_patterns": [
            "Overexplains without action",
            "Broadcasts without listening",
            "Jumps channels mid-case",
        ],
    },
    "Adaptability": {
        "why": "Adaptability supports steady service when priorities or volumes shift without warning.",
        "risk": "Over-indexing on flexibility can erode needed routines.",
        "mitigation": "Pair agility with lightweight rituals and probe: 'Share a time you had to flex plans at the last minute.'",
        "do_well": [
            "Switches gears gracefully",
            "Stays calm with incomplete info",
            "Keeps customers updated",
        ],
        "anti_patterns": [
            "Drops agreed processes",
            "Chases novelty over closure",
            "Spreads focus too thin",
        ],
    },
    "Responsibility": {
        "why": "Responsibility ensures commitments are owned end-to-end, reinforcing trust in the support team.",
        "risk": "If unchecked it can lead to heroic overwork or reluctance to delegate.",
        "mitigation": "Clarify shared ownership, highlight team rota cover, and probe: 'Tell me about a ticket you owned from start to finish.'",
        "do_well": [
            "Sets clear next actions",
            "Follows through on escalations",
            "Flags risk early",
        ],
        "anti_patterns": [
            "Holds tasks too tightly",
            "Works unsustainable hours",
            "Struggles to say no",
        ],
    },
    "Restorative": {
        "why": "Restorative talent powers troubleshooting depth and gets services back online quickly.",
        "risk": "Overuse may mean diving into fixes without engaging stakeholders.",
        "mitigation": "Blend diagnostics with communication and probe: 'Describe the toughest fix you led and how you kept others updated.'",
        "do_well": [
            "Interprets error patterns",
            "Tests hypotheses quickly",
            "Records fixes clearly",
        ],
        "anti_patterns": [
            "Debugs in isolation",
            "Over-engineers solutions",
            "Neglects prevention",
        ],
    },
}

VALUE_BEHAVIOUR_LIBRARY: Dict[str, Dict[str, List[str]]] = {
    "Caring": {
        "why": "Caring signals a service mindset that reassures customers at stressful moments.",
        "risk": "Over-caring can erode healthy boundaries and extend calls unnecessarily.",
        "mitigation": "Agree realistic limits and probe: 'When have you balanced care with time pressures?'",
        "do_well": [
            "Shows attentive tone",
            "Checks welfare signs",
            "Connects to follow-up support",
        ],
        "anti_patterns": [
            "Takes ownership of personal issues",
            "Avoids tough messages",
            "Lets calls overrun",
        ],
    },
    "Calm": {
        "why": "Calm keeps the operation grounded when SLAs and emotions spike.",
        "risk": "If overused it may look detached from urgency.",
        "mitigation": "Match calm with clear priorities and probe: 'Share an example of staying calm under intense pressure.'",
        "do_well": [
            "Breathes before responding",
            "Uses stabilising language",
            "Signals next steps",
        ],
        "anti_patterns": [
            "Appears disengaged",
            "Delays necessary escalation",
            "Ignores energy in the room",
        ],
    },
    "Trustworthy": {
        "why": "Trustworthiness underpins confidence that commitments will be met.",
        "risk": "It can become rigid if transparency slips.",
        "mitigation": "Keep audit trails visible and probe: 'How do you show stakeholders they can rely on you?'",
        "do_well": [
            "Sets honest expectations",
            "Protects data and privacy",
            "Shares progress openly",
        ],
        "anti_patterns": [
            "Shields information",
            "Breaks promises",
            "Deflects accountability",
        ],
    },
    "Friendly": {
        "why": "Friendliness keeps conversations open even when dealing with complex issues.",
        "risk": "Being too friendly may blur professional boundaries.",
        "mitigation": "Signpost next steps confidently and probe: 'Tell me about a time friendliness helped diffuse a situation.'",
        "do_well": [
            "Greets warmly",
            "Uses names appropriately",
            "Finds shared ground",
        ],
        "anti_patterns": [
            "Over-shares personal details",
            "Loses focus on resolution",
            "Fills silence unnecessarily",
        ],
    },
    "Patient": {
        "why": "Patience gives customers the space to explain while keeping solutions on track.",
        "risk": "If overdone it can slow decisions or let calls drift.",
        "mitigation": "Set gentle checkpoints and probe: 'Describe a time patience helped you unpick a complex problem.'",
        "do_well": [
            "Lets callers finish",
            "Checks understanding",
            "Summarises to close",
        ],
        "anti_patterns": [
            "Avoids drawing conversations to a close",
            "Allows repetition without progress",
            "Sidesteps direct answers",
        ],
    },
}


def _format_evidence(evidence: List[str]) -> str:
    if not evidence:
        return ""
    joined = ", ".join(dict.fromkeys(evidence))
    return f" Signals including {joined} make this clear."


def get_behaviour_pack(name: str, attribute_type: str, evidence: List[str]) -> Dict:
    library = STRENGTH_BEHAVIOUR_LIBRARY if attribute_type == "strength" else VALUE_BEHAVIOUR_LIBRARY
    pack = library.get(name, DEFAULT_STRENGTH_PACK if attribute_type == "strength" else DEFAULT_VALUE_PACK)
    why = pack["why"] + _format_evidence(evidence)
    return {
        "why_it_matters": why,
        "risk_if_overused": pack["risk"],
        "mitigation_and_probe": pack["mitigation"],
        "do_well_indicators": pack["do_well"],
        "anti_patterns": pack["anti_patterns"],
    }
