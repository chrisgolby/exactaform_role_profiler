"""Scoring and mapping utilities for Exactaform Role Profiler."""
from __future__ import annotations

import math
import os
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import requests

LLM_DISABLED = os.getenv("LLM_DISABLED", "true").lower() != "false"
OPENAI_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ROLE_TYPE = "Frontline Support"

ToggleMap = Dict[str, float]


def _load_openai_embedding(text: str) -> Optional[List[float]]:
    """Return an OpenAI embedding vector when enabled."""
    if LLM_DISABLED or not OPENAI_API_KEY:
        return None
    try:
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"input": text, "model": OPENAI_MODEL},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception:
        return None


@dataclass
class AttributeDefinition:
    name: str
    domain: str
    keywords: Dict[str, float]
    exemplars: List[str]
    role_prior: float
    context_weights: Dict[str, float] = field(default_factory=dict)
    dependency_hints: Dict[str, Dict[str, float]] = field(default_factory=dict)


def _default_keywords(base_terms: Iterable[str], weight: float = 1.0) -> Dict[str, float]:
    return {term: weight for term in base_terms}


STRENGTHS_DEFINITIONS: List[AttributeDefinition] = [
    AttributeDefinition(
        name="Achiever",
        domain="Executing",
        keywords={"deliverables": 1.2, "productivity": 1.1, "high output": 1.0},
        exemplars=[
            "Keeps delivering outcomes against demanding workloads",
            "Tracks performance metrics and personal targets",
        ],
        role_prior=0.3,
        context_weights={"shift_work": 0.05, "strict_sla": 0.05},
    ),
    AttributeDefinition(
        name="Activator",
        domain="Influencing",
        keywords={"kick-off": 1.2, "launch": 1.0, "start quickly": 1.1},
        exemplars=["Turns ideas into immediate action", "Gets initiatives moving fast"],
        role_prior=0.25,
        context_weights={"customer_volume": 0.05},
    ),
    AttributeDefinition(
        name="Adaptability",
        domain="Relationship Building",
        keywords={
            "adaptable": 1.4,
            "flexible": 1.3,
            "calm under pressure": 2.0,
            "change": 1.0,
            "first point of contact": 1.4,
        },
        exemplars=[
            "Handles unpredictable requests without fuss",
            "Thrives when priorities shift across service queues",
        ],
        role_prior=0.85,
        context_weights={"customer_volume": 0.2, "shift_work": 0.15},
        dependency_hints={
            "switch": {"channel": 1.0, "priority": 1.0},
            "juggle": {"queue": 1.0, "ticket": 0.9},
            "handle": {"escalation": 0.9},
        },
    ),
    AttributeDefinition(
        name="Analytical",
        domain="Strategic Thinking",
        keywords={"root cause": 1.5, "analysis": 1.3, "metrics": 1.1, "diagnose": 1.4},
        exemplars=[
            "Diagnoses issues using data and structured thinking",
            "Asks for evidence before committing to fixes",
        ],
        role_prior=0.4,
        context_weights={"technical_complexity": 0.2},
    ),
    AttributeDefinition(
        name="Arranger",
        domain="Executing",
        keywords={
            "schedule": 1.0,
            "coordinate": 1.2,
            "handover": 1.5,
            "workflow": 1.2,
            "backlog": 1.3,
        },
        exemplars=[
            "Coordinates moving parts across shifts",
            "Optimises who handles what in the queue",
        ],
        role_prior=0.4,
        context_weights={"shift_work": 0.2, "customer_volume": 0.1},
        dependency_hints={
            "coordinate": {"handover": 1.3, "backlog": 1.0},
            "manage": {"handover": 1.1, "queue": 1.0},
        },
    ),
    AttributeDefinition(
        name="Belief",
        domain="Executing",
        keywords={"values": 1.0, "purpose": 1.0, "ethos": 1.1},
        exemplars=["Acts from a strong service ethos", "Makes decisions guided by principles"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Command",
        domain="Influencing",
        keywords={"take charge": 1.4, "lead": 1.1, "assertive": 1.2},
        exemplars=["Steps in decisively during escalations"],
        role_prior=0.25,
        context_weights={"strict_sla": 0.1},
    ),
    AttributeDefinition(
        name="Communication",
        domain="Influencing",
        keywords={
            "communicate": 1.5,
            "explain": 1.2,
            "clear updates": 1.4,
            "knowledge base": 1.2,
            "escalate": 1.3,
        },
        exemplars=[
            "Keeps stakeholders informed of issue status",
            "Translates technical issues into plain UK English",
        ],
        role_prior=0.9,
        context_weights={"customer_volume": 0.2, "strict_sla": 0.15},
        dependency_hints={
            "update": {"stakeholder": 1.1, "customer": 1.0},
            "escalate": {"issue": 1.0, "ticket": 0.9},
            "share": {"handover": 1.0, "status": 0.9},
        },
    ),
    AttributeDefinition(
        name="Competition",
        domain="Influencing",
        keywords={"targets": 1.0, "win": 1.0, "top performer": 1.1},
        exemplars=["Enjoys outperforming service level targets"],
        role_prior=0.2,
        context_weights={"strict_sla": 0.05},
    ),
    AttributeDefinition(
        name="Connectedness",
        domain="Relationship Building",
        keywords={"community": 1.0, "link": 0.9, "together": 0.9},
        exemplars=["Sees patterns across customer feedback"],
        role_prior=0.25,
        context_weights={},
    ),
    AttributeDefinition(
        name="Consistency",
        domain="Executing",
        keywords={"process": 1.4, "policy": 1.2, "standard": 1.2},
        exemplars=["Applies policies evenly across tickets"],
        role_prior=0.45,
        context_weights={"strict_sla": 0.2},
    ),
    AttributeDefinition(
        name="Context",
        domain="Strategic Thinking",
        keywords={"history": 0.9, "precedent": 1.0, "background": 1.0},
        exemplars=["Pulls previous resolutions to inform next steps"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Deliberative",
        domain="Executing",
        keywords={"risk": 1.2, "careful": 1.1, "consider": 1.0},
        exemplars=["Weighs risk before committing to changes"],
        role_prior=0.3,
        context_weights={"technical_complexity": 0.1},
    ),
    AttributeDefinition(
        name="Developer",
        domain="Relationship Building",
        keywords={"coach": 1.0, "mentor": 1.0, "support colleagues": 1.3},
        exemplars=["Helps teammates grow through feedback"],
        role_prior=0.35,
        context_weights={},
    ),
    AttributeDefinition(
        name="Discipline",
        domain="Executing",
        keywords={
            "structure": 1.0,
            "routine": 1.0,
            "checklist": 1.1,
            "backlog": 1.2,
            "sla": 1.1,
        },
        exemplars=["Relies on disciplined routines to manage volume"],
        role_prior=0.4,
        context_weights={"strict_sla": 0.1},
        dependency_hints={
            "maintain": {"sla": 1.1, "backlog": 1.0},
            "monitor": {"queue": 0.9},
        },
    ),
    AttributeDefinition(
        name="Empathy",
        domain="Relationship Building",
        keywords={
            "empathy": 2.2,
            "empathic": 2.0,
            "support": 1.3,
            "calm under pressure": 2.2,
            "first point of contact": 2.0,
            "de-escalate": 2.3,
            "reassure": 1.8,
        },
        exemplars=[
            "Tunes into customer mood and adapts tone",
            "Diffuses emotional escalations kindly",
        ],
        role_prior=0.95,
        context_weights={"customer_volume": 0.25, "shift_work": 0.15},
        dependency_hints={
            "calm": {"customer": 1.1, "caller": 1.1},
            "reassure": {"customer": 1.0, "caller": 1.0},
            "support": {"upset": 0.9, "escalation": 0.8},
        },
    ),
    AttributeDefinition(
        name="Focus",
        domain="Executing",
        keywords={"focus": 1.0, "prioritise": 1.2, "concentrate": 1.0},
        exemplars=["Cuts through noise to prioritise urgent cases"],
        role_prior=0.35,
        context_weights={"strict_sla": 0.1},
    ),
    AttributeDefinition(
        name="Futuristic",
        domain="Strategic Thinking",
        keywords={"future": 0.9, "vision": 0.9, "long term": 0.9},
        exemplars=["Paints a compelling picture of future services"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Harmony",
        domain="Relationship Building",
        keywords={"harmony": 0.9, "conflict": 1.0, "resolve": 1.1},
        exemplars=["Keeps the team settled during hectic spikes"],
        role_prior=0.4,
        context_weights={"customer_volume": 0.1},
    ),
    AttributeDefinition(
        name="Ideation",
        domain="Strategic Thinking",
        keywords={"ideas": 1.0, "creative": 1.0, "innovation": 1.0},
        exemplars=["Generates new solutions for recurring issues"],
        role_prior=0.25,
        context_weights={},
    ),
    AttributeDefinition(
        name="Includer",
        domain="Relationship Building",
        keywords={"inclusive": 1.0, "welcome": 1.0, "diverse": 1.0},
        exemplars=["Ensures every caller feels heard"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Individualization",
        domain="Relationship Building",
        keywords={"tailor": 1.2, "personal": 1.2, "bespoke": 1.1},
        exemplars=["Adjusts support to each customer's context"],
        role_prior=0.45,
        context_weights={"customer_volume": 0.1},
    ),
    AttributeDefinition(
        name="Input",
        domain="Strategic Thinking",
        keywords={"knowledge": 1.1, "catalogue": 1.0, "document": 1.2},
        exemplars=["Collects tips and scripts for the team"],
        role_prior=0.3,
        context_weights={"technical_complexity": 0.1},
    ),
    AttributeDefinition(
        name="Intellection",
        domain="Strategic Thinking",
        keywords={"reflect": 1.0, "deep thinking": 1.0, "conceptual": 0.9},
        exemplars=["Reflects before advising others"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Learner",
        domain="Strategic Thinking",
        keywords={"learn": 1.2, "upskill": 1.2, "training": 1.3},
        exemplars=["Absorbs new troubleshooting steps quickly"],
        role_prior=0.55,
        context_weights={"technical_complexity": 0.15},
    ),
    AttributeDefinition(
        name="Maximizer",
        domain="Influencing",
        keywords={"refine": 1.0, "optimise": 1.0, "best": 1.1},
        exemplars=["Turns good service into great experiences"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Positivity",
        domain="Relationship Building",
        keywords={"positive": 1.0, "uplift": 1.0, "cheer": 1.0},
        exemplars=["Brings lightness to tense interactions"],
        role_prior=0.35,
        context_weights={"customer_volume": 0.05},
    ),
    AttributeDefinition(
        name="Relator",
        domain="Relationship Building",
        keywords={"relationship": 1.0, "rapport": 1.2, "trust": 1.1},
        exemplars=["Builds rapport quickly with repeat callers"],
        role_prior=0.4,
        context_weights={"customer_volume": 0.1},
    ),
    AttributeDefinition(
        name="Responsibility",
        domain="Executing",
        keywords={
            "ownership": 1.7,
            "accountable": 1.6,
            "follow through": 1.5,
            "escalate": 1.2,
            "service level": 1.1,
            "backlog": 1.2,
        },
        exemplars=[
            "Takes ownership of tickets until closure",
            "Keeps promises to customers and colleagues",
        ],
        role_prior=0.92,
        context_weights={"strict_sla": 0.2, "customer_volume": 0.15},
        dependency_hints={
            "own": {"ticket": 1.1, "backlog": 1.0, "resolution": 1.0},
            "manage": {"sla": 1.0, "obligation": 0.9},
        },
    ),
    AttributeDefinition(
        name="Restorative",
        domain="Executing",
        keywords={
            "troubleshoot": 2.2,
            "fix": 1.6,
            "diagnose": 1.5,
            "resolve": 1.4,
            "triage": 1.7,
            "backlog": 1.2,
        },
        exemplars=[
            "Quickly diagnoses faults and restores service",
            "Enjoys solving complex customer issues",
        ],
        role_prior=0.9,
        context_weights={"technical_complexity": 0.25, "strict_sla": 0.15},
        dependency_hints={
            "troubleshoot": {"incident": 1.1, "issue": 1.0, "integration": 1.0},
            "diagnose": {"root cause": 1.2, "problem": 1.0},
            "clear": {"backlog": 0.9},
        },
    ),
    AttributeDefinition(
        name="Self-Assurance",
        domain="Influencing",
        keywords={"confidence": 1.1, "self assured": 1.0, "decisive": 1.0},
        exemplars=["Acts confidently in uncertain situations"],
        role_prior=0.25,
        context_weights={"technical_complexity": 0.05},
    ),
    AttributeDefinition(
        name="Significance",
        domain="Influencing",
        keywords={"impact": 1.0, "recognition": 1.0, "profile": 1.0},
        exemplars=["Wants their work to be seen and valued"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Strategic",
        domain="Strategic Thinking",
        keywords={"strategy": 1.0, "plan": 1.0, "pattern": 1.0},
        exemplars=["Spots patterns and plans ahead"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Woo",
        domain="Influencing",
        keywords={"win over": 1.0, "influence": 1.0, "engage": 1.0},
        exemplars=["Enjoys winning people round quickly"],
        role_prior=0.25,
        context_weights={"customer_volume": 0.05},
    ),
]


VALUE_DEFINITIONS: List[AttributeDefinition] = [
    AttributeDefinition(
        name="Able",
        domain="Values",
        keywords={"skilled": 1.0, "capable": 1.0, "competent": 1.1},
        exemplars=["Shows competence across varied tasks"],
        role_prior=0.4,
        context_weights={"technical_complexity": 0.1},
    ),
    AttributeDefinition(
        name="Accepting",
        domain="Values",
        keywords={"inclusive": 1.0, "open": 1.0, "accepting": 1.1},
        exemplars=["Welcomes diverse customers and colleagues"],
        role_prior=0.35,
        context_weights={},
    ),
    AttributeDefinition(
        name="Adaptable",
        domain="Values",
        keywords={"adaptable": 1.4, "flexible": 1.3, "resilient": 1.2},
        exemplars=["Adjusts style in fast-moving environments"],
        role_prior=0.9,
        context_weights={"customer_volume": 0.15, "shift_work": 0.1},
    ),
    AttributeDefinition(
        name="Bold",
        domain="Values",
        keywords={"bold": 1.0, "courage": 1.0},
        exemplars=["Takes decisive action"],
        role_prior=0.25,
        context_weights={},
    ),
    AttributeDefinition(
        name="Brave",
        domain="Values",
        keywords={"brave": 1.0, "courage": 1.0},
        exemplars=["Steps into tough conversations"],
        role_prior=0.25,
        context_weights={},
    ),
    AttributeDefinition(
        name="Calm",
        domain="Values",
        keywords={
            "calm": 2.0,
            "steady": 1.5,
            "compose": 1.4,
            "calm under pressure": 2.1,
        },
        exemplars=["Keeps composure under pressure"],
        role_prior=0.95,
        context_weights={"customer_volume": 0.2, "strict_sla": 0.1},
        dependency_hints={
            "remain": {"calm": 1.2, "composed": 1.0},
            "stay": {"calm": 1.0, "steady": 0.9},
            "keep": {"composure": 1.0},
        },
    ),
    AttributeDefinition(
        name="Caring",
        domain="Values",
        keywords={"care": 1.8, "caring": 2.0, "support": 1.3, "help": 1.1, "wellbeing": 1.2},
        exemplars=["Looks after customers thoughtfully"],
        role_prior=0.92,
        context_weights={"customer_volume": 0.2},
        dependency_hints={
            "check": {"wellbeing": 1.1, "welfare": 1.0},
            "support": {"caller": 1.0, "customer": 1.0},
            "offer": {"follow up": 0.9},
        },
    ),
    AttributeDefinition(
        name="Cheerful",
        domain="Values",
        keywords={"cheerful": 1.0, "positive": 1.0, "uplift": 1.0},
        exemplars=["Brings lightness to customer calls"],
        role_prior=0.35,
        context_weights={},
    ),
    AttributeDefinition(
        name="Clever",
        domain="Values",
        keywords={"clever": 1.0, "smart": 1.0, "bright": 1.0},
        exemplars=["Picks up complex issues swiftly"],
        role_prior=0.45,
        context_weights={"technical_complexity": 0.1},
    ),
    AttributeDefinition(
        name="Complex",
        domain="Values",
        keywords={"complex": 1.0, "multi-faceted": 1.0},
        exemplars=["Navigates nuanced environments"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Confident",
        domain="Values",
        keywords={"confident": 1.1, "assured": 1.0},
        exemplars=["Speaks up with confidence"],
        role_prior=0.35,
        context_weights={},
    ),
    AttributeDefinition(
        name="Defensive",
        domain="Values",
        keywords={"defensive": 1.0},
        exemplars=["Protective of standards"],
        role_prior=0.1,
        context_weights={},
    ),
    AttributeDefinition(
        name="Dependable",
        domain="Values",
        keywords={"dependable": 1.3, "reliable": 1.4, "trust": 1.1},
        exemplars=["Can be counted on to deliver"],
        role_prior=0.88,
        context_weights={"strict_sla": 0.15},
    ),
    AttributeDefinition(
        name="Dignified",
        domain="Values",
        keywords={"dignity": 1.0, "respect": 1.0},
        exemplars=["Treats people respectfully"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Driver",
        domain="Values",
        keywords={"drive": 1.0, "push": 1.0},
        exemplars=["Pushes for progress"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Empathetic",
        domain="Values",
        keywords={"empathy": 2.0, "empathetic": 2.0, "understand": 1.3},
        exemplars=["Understands emotional context"],
        role_prior=0.94,
        context_weights={"customer_volume": 0.2},
    ),
    AttributeDefinition(
        name="Energetic",
        domain="Values",
        keywords={"energetic": 1.0, "energetic": 1.0, "lively": 1.0},
        exemplars=["Brings energy to interactions"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Expressive",
        domain="Values",
        keywords={"expressive": 1.0, "communicative": 1.0},
        exemplars=["Uses expressive language"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Friendly",
        domain="Values",
        keywords={"friendly": 1.5, "approachable": 1.4, "warm": 1.2, "first point of contact": 1.6},
        exemplars=["Puts customers at ease"],
        role_prior=0.9,
        context_weights={"customer_volume": 0.15},
        dependency_hints={
            "welcome": {"caller": 1.1, "customer": 1.1},
            "first": {"point of contact": 1.3},
            "build": {"rapport": 1.0},
        },
    ),
    AttributeDefinition(
        name="Gregarious",
        domain="Values",
        keywords={"gregarious": 1.0, "sociable": 1.0},
        exemplars=["Enjoys social contact"],
        role_prior=0.3,
        context_weights={"customer_volume": 0.1},
    ),
    AttributeDefinition(
        name="Giving",
        domain="Values",
        keywords={"giving": 1.0, "generous": 1.0},
        exemplars=["Goes the extra mile"],
        role_prior=0.4,
        context_weights={},
    ),
    AttributeDefinition(
        name="Happy",
        domain="Values",
        keywords={"happy": 1.0, "cheer": 1.0},
        exemplars=["Brings happiness"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Helpful",
        domain="Values",
        keywords={"help": 1.4, "assist": 1.2, "support": 1.1},
        exemplars=["Proactively helps others"],
        role_prior=0.88,
        context_weights={"customer_volume": 0.1},
    ),
    AttributeDefinition(
        name="Idealistic",
        domain="Values",
        keywords={"ideal": 1.0, "aspire": 1.0},
        exemplars=["Seeks better ways"],
        role_prior=0.25,
        context_weights={},
    ),
    AttributeDefinition(
        name="Independent",
        domain="Values",
        keywords={"independent": 1.2, "autonomous": 1.1},
        exemplars=["Works well with minimal supervision"],
        role_prior=0.35,
        context_weights={"shift_work": 0.05},
    ),
    AttributeDefinition(
        name="Ingenious",
        domain="Values",
        keywords={"ingenious": 1.0, "creative": 1.0},
        exemplars=["Finds clever fixes"],
        role_prior=0.3,
        context_weights={"technical_complexity": 0.1},
    ),
    AttributeDefinition(
        name="Intelligent",
        domain="Values",
        keywords={"intelligent": 1.0, "smart": 1.0},
        exemplars=["Understands complex situations"],
        role_prior=0.4,
        context_weights={"technical_complexity": 0.1},
    ),
    AttributeDefinition(
        name="Introverted",
        domain="Values",
        keywords={"introverted": 1.0, "reflective": 1.0},
        exemplars=["Prefers quieter focus time"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Kind",
        domain="Values",
        keywords={"kind": 1.6, "kindness": 1.4, "compassion": 1.4},
        exemplars=["Treats others with kindness"],
        role_prior=0.72,
        context_weights={"customer_volume": 0.1},
    ),
    AttributeDefinition(
        name="Knowledgeable",
        domain="Values",
        keywords={"knowledgeable": 1.3, "subject matter": 1.2, "expert": 1.2},
        exemplars=["Draws on deep knowledge"],
        role_prior=0.5,
        context_weights={"technical_complexity": 0.2},
    ),
    AttributeDefinition(
        name="Logical",
        domain="Values",
        keywords={"logical": 1.2, "structured": 1.0, "analytical": 1.0},
        exemplars=["Applies logic to troubleshoot"],
        role_prior=0.45,
        context_weights={"technical_complexity": 0.15},
    ),
    AttributeDefinition(
        name="Loud",
        domain="Values",
        keywords={"loud": 1.0},
        exemplars=["High-energy presence"],
        role_prior=0.1,
        context_weights={},
    ),
    AttributeDefinition(
        name="Loving",
        domain="Values",
        keywords={"loving": 1.0, "care": 1.0},
        exemplars=["Shows care"],
        role_prior=0.35,
        context_weights={},
    ),
    AttributeDefinition(
        name="Mature",
        domain="Values",
        keywords={"mature": 1.0, "composed": 1.0},
        exemplars=["Responds with maturity"],
        role_prior=0.4,
        context_weights={"customer_volume": 0.05},
    ),
    AttributeDefinition(
        name="Modest",
        domain="Values",
        keywords={"modest": 1.0, "humble": 1.0},
        exemplars=["Keeps praise quiet"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Nervous",
        domain="Values",
        keywords={"nervous": 1.0, "anxious": 1.0},
        exemplars=["Sensitive to risk"],
        role_prior=0.1,
        context_weights={},
    ),
    AttributeDefinition(
        name="Observant",
        domain="Values",
        keywords={"observe": 1.2, "noticing": 1.2, "spot": 1.1},
        exemplars=["Spots subtle cues"],
        role_prior=0.55,
        context_weights={"strict_sla": 0.05},
    ),
    AttributeDefinition(
        name="Organised",
        domain="Values",
        keywords={
            "organised": 1.5,
            "structured": 1.3,
            "methodical": 1.3,
            "backlog": 1.3,
            "queue": 1.2,
        },
        exemplars=["Keeps workload organised"],
        role_prior=0.86,
        context_weights={"strict_sla": 0.2},
        dependency_hints={
            "manage": {"backlog": 1.2, "rota": 1.0},
            "plan": {"handover": 1.0},
        },
    ),
    AttributeDefinition(
        name="Patient",
        domain="Values",
        keywords={"patient": 1.9, "patience": 1.7, "steady": 1.3, "calm under pressure": 1.8},
        exemplars=["Gives callers time to explain"],
        role_prior=0.93,
        context_weights={"customer_volume": 0.18},
        dependency_hints={
            "listen": {"carefully": 1.1, "fully": 1.0},
            "allow": {"customer": 1.0, "caller": 1.0},
            "stay": {"calm": 1.0},
        },
    ),
    AttributeDefinition(
        name="Powerful",
        domain="Values",
        keywords={"powerful": 1.0, "influential": 1.0},
        exemplars=["Drives outcomes"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Proud",
        domain="Values",
        keywords={"proud": 1.0, "pride": 1.0},
        exemplars=["Takes pride in quality"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Quiet",
        domain="Values",
        keywords={"quiet": 1.0, "low-key": 1.0},
        exemplars=["Reserved presence"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Reflective",
        domain="Values",
        keywords={"reflective": 1.1, "thoughtful": 1.1},
        exemplars=["Considers impact thoughtfully"],
        role_prior=0.35,
        context_weights={},
    ),
    AttributeDefinition(
        name="Relaxed",
        domain="Values",
        keywords={"relaxed": 1.3, "unflappable": 1.3},
        exemplars=["Stays relaxed in busy periods"],
        role_prior=0.76,
        context_weights={"customer_volume": 0.15},
    ),
    AttributeDefinition(
        name="Religious",
        domain="Values",
        keywords={"religious": 1.0, "faith": 1.0},
        exemplars=["Guided by faith"],
        role_prior=0.1,
        context_weights={},
    ),
    AttributeDefinition(
        name="Responsive",
        domain="Values",
        keywords={"responsive": 1.5, "prompt": 1.4, "timely": 1.3},
        exemplars=["Responds quickly to need"],
        role_prior=0.68,
        context_weights={"strict_sla": 0.15},
    ),
    AttributeDefinition(
        name="Searching",
        domain="Values",
        keywords={"search": 1.0, "explore": 1.0},
        exemplars=["Keeps digging for answers"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Self-assertive",
        domain="Values",
        keywords={"assertive": 1.1, "self-assertive": 1.0},
        exemplars=["Speaks up when needed"],
        role_prior=0.3,
        context_weights={},
    ),
    AttributeDefinition(
        name="Self-conscious",
        domain="Values",
        keywords={"self-conscious": 1.0, "aware": 1.0},
        exemplars=["Aware of perception"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Sensible",
        domain="Values",
        keywords={"sensible": 1.3, "practical": 1.2, "sound judgement": 1.2},
        exemplars=["Brings sensible judgement"],
        role_prior=0.6,
        context_weights={"technical_complexity": 0.1},
    ),
    AttributeDefinition(
        name="Sentimental",
        domain="Values",
        keywords={"sentimental": 1.0, "emotional": 1.0},
        exemplars=["Values emotional connection"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Shy",
        domain="Values",
        keywords={"shy": 1.0, "reserved": 1.0},
        exemplars=["More reserved style"],
        role_prior=0.15,
        context_weights={},
    ),
    AttributeDefinition(
        name="Silly",
        domain="Values",
        keywords={"silly": 1.0, "playful": 1.0},
        exemplars=["Injects humour"],
        role_prior=0.15,
        context_weights={},
    ),
    AttributeDefinition(
        name="Spontaneous",
        domain="Values",
        keywords={"spontaneous": 1.0, "improvise": 1.0},
        exemplars=["Acts quickly without much planning"],
        role_prior=0.2,
        context_weights={},
    ),
    AttributeDefinition(
        name="Tense",
        domain="Values",
        keywords={"tense": 1.0, "high pressure": 1.0},
        exemplars=["Feels pressure acutely"],
        role_prior=0.1,
        context_weights={},
    ),
    AttributeDefinition(
        name="Trustworthy",
        domain="Values",
        keywords={
            "trustworthy": 1.8,
            "integrity": 1.5,
            "dependable": 1.4,
            "first point of contact": 1.6,
            "escalate": 1.2,
        },
        exemplars=["Trusted with sensitive information"],
        role_prior=0.96,
        context_weights={"strict_sla": 0.2, "customer_volume": 0.12},
        dependency_hints={
            "maintain": {"sla": 1.1, "promise": 1.0},
            "handover": {"detail": 1.0, "log": 0.9},
            "keep": {"promise": 1.1, "commitment": 1.0},
        },
    ),
    AttributeDefinition(
        name="Warm",
        domain="Values",
        keywords={"warm": 1.5, "welcoming": 1.4, "open": 1.1},
        exemplars=["Creates a warm welcome"],
        role_prior=0.74,
        context_weights={"customer_volume": 0.1},
    ),
    AttributeDefinition(
        name="Wise",
        domain="Values",
        keywords={"wise": 1.0, "experienced": 1.0},
        exemplars=["Offers wise counsel"],
        role_prior=0.4,
        context_weights={"technical_complexity": 0.1},
    ),
    AttributeDefinition(
        name="Witty",
        domain="Values",
        keywords={"witty": 1.0, "humour": 1.0},
        exemplars=["Uses wit to lighten interactions"],
        role_prior=0.25,
        context_weights={"customer_volume": 0.05},
    ),
]


def clean_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def tokenize(text: str) -> List[str]:
    return [token for token in clean_text(text).replace("/", " ").replace("-", " ").split(" ") if token]


def build_ngrams(tokens: List[str], max_n: int = 3) -> List[str]:
    phrases: List[str] = []
    for n in range(1, max_n + 1):
        for i in range(len(tokens) - n + 1):
            phrases.append(" ".join(tokens[i : i + n]))
    return phrases


def cosine_similarity(counter_a: Counter, counter_b: Counter) -> float:
    if not counter_a or not counter_b:
        return 0.0
    intersection = set(counter_a.keys()) & set(counter_b.keys())
    numerator = sum(counter_a[x] * counter_b[x] for x in intersection)
    sum1 = sum(v ** 2 for v in counter_a.values())
    sum2 = sum(v ** 2 for v in counter_b.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _semantic_score(definition: AttributeDefinition, text: str, tokens: List[str]) -> Tuple[float, Optional[str]]:
    if not definition.exemplars:
        return 0.0, None
    text_counter = Counter(tokens)
    best = 0.0
    best_phrase = None
    if not LLM_DISABLED and OPENAI_API_KEY:
        text_embedding = _load_openai_embedding(text)
        if text_embedding is not None:
            text_vector = np.array(text_embedding)
            for exemplar in definition.exemplars:
                ex_vector_raw = _load_openai_embedding(exemplar)
                if ex_vector_raw is None:
                    continue
                exemplar_vector = np.array(ex_vector_raw)
                denom = np.linalg.norm(text_vector) * np.linalg.norm(exemplar_vector)
                if denom == 0:
                    continue
                score = float(np.dot(text_vector, exemplar_vector) / denom)
                if score > best:
                    best = score
                    best_phrase = exemplar
            return best, best_phrase
    for exemplar in definition.exemplars:
        exemplar_tokens = tokenize(exemplar)
        score = cosine_similarity(text_counter, Counter(exemplar_tokens))
        if score > best:
            best = score
            best_phrase = exemplar
    return best, best_phrase


def _dependency_score(definition: AttributeDefinition, tokens: List[str]) -> Tuple[float, List[str]]:
    if not definition.dependency_hints or not tokens:
        return 0.0, []
    score = 0.0
    evidence: List[str] = []
    token_count = len(tokens)
    seen: set[str] = set()
    for head, tails in definition.dependency_hints.items():
        head_clean = clean_text(head)
        head_tokens = head_clean.split()
        head_len = len(head_tokens)
        if head_len == 0:
            continue
        for index in range(token_count - head_len + 1):
            window_slice = tokens[index : index + head_len]
            if window_slice != head_tokens:
                continue
            window_start = max(0, index - 3)
            window_end = min(token_count, index + head_len + 4)
            window_tokens = tokens[window_start:window_end]
            window_text = " ".join(window_tokens)
            for tail, weight in tails.items():
                tail_clean = clean_text(tail)
                if tail_clean and tail_clean in window_text:
                    key = f"{head_clean}->{tail_clean}"
                    if key in seen:
                        continue
                    seen.add(key)
                    score += weight
                    evidence.append(f"dependency: {head}->{tail}")
    return score, evidence


def _keyword_score(
    definition: AttributeDefinition,
    text: str,
    ngrams: List[str],
    tokens: List[str],
) -> Tuple[float, List[str]]:
    score = 0.0
    evidence: List[str] = []
    for phrase, weight in definition.keywords.items():
        phrase_clean = clean_text(phrase)
        if phrase_clean in text or phrase_clean in ngrams:
            score += weight
            evidence.append(phrase)
    dep_score, dep_evidence = _dependency_score(definition, tokens)
    score += dep_score
    evidence.extend(dep_evidence)
    return score, evidence


def _context_adjustment(definition: AttributeDefinition, toggles: ToggleMap) -> Tuple[float, List[str]]:
    adjustments = []
    score = 0.0
    for toggle, weight in definition.context_weights.items():
        value = toggles.get(toggle, 0.0)
        if value:
            delta = weight * value
            score += delta
            adjustments.append(f"{toggle}:{value:+.2f} → {delta:+.2f}")
    return score, adjustments


def _normalise_component(results: List[Dict], key: str) -> None:
    max_value = max((item[key] for item in results), default=0.0)
    if max_value <= 0:
        for item in results:
            item[f"{key}_norm"] = 0.0
        return
    for item in results:
        item[f"{key}_norm"] = item[key] / max_value


def score_attributes(
    definitions: List[AttributeDefinition],
    job_summary: str,
    key_responsibilities: str,
    other_skills: str,
    toggles: Optional[ToggleMap] = None,
) -> Tuple[List[Dict], List[str]]:
    toggles = toggles or {}
    combined_text = " ".join([
        job_summary or "",
        key_responsibilities or "",
        other_skills or "",
    ])
    cleaned_text = clean_text(combined_text)
    tokens = tokenize(combined_text)
    ngrams = build_ngrams(tokens)
    results: List[Dict] = []
    all_evidence: List[str] = []
    for definition in definitions:
        keyword_score, evidence = _keyword_score(definition, cleaned_text, ngrams, tokens)
        semantic_score, exemplar = _semantic_score(definition, cleaned_text, tokens)
        context_score, context_rules = _context_adjustment(definition, toggles)
        results.append(
            {
                "name": definition.name,
                "domain": definition.domain,
                "keyword_score": keyword_score,
                "semantic_score": semantic_score,
                "role_prior": definition.role_prior,
                "context_score": context_score,
                "evidence": evidence,
                "best_exemplar": exemplar,
                "context_rules": context_rules,
            }
        )
        all_evidence.extend(evidence)
    _normalise_component(results, "keyword_score")
    _normalise_component(results, "semantic_score")
    _normalise_component(results, "context_score")
    for item in results:
        item["total_score"] = (
            0.35 * item["keyword_score_norm"]
            + 0.25 * item["semantic_score_norm"]
            + 0.25 * item["role_prior"]
            + 0.15 * item["context_score_norm"]
        )
    return results, all_evidence


DOMAIN_CAP = {
    "Executing": 2,
    "Influencing": 2,
    "Relationship Building": 2,
    "Strategic Thinking": 2,
}


def select_top_strengths(results: List[Dict], top_n: int = 5) -> List[Dict]:
    sorted_results = sorted(results, key=lambda item: item["total_score"], reverse=True)
    domain_counts: Dict[str, int] = {domain: 0 for domain in DOMAIN_CAP}
    selection: List[Dict] = []
    for item in sorted_results:
        domain = item["domain"]
        allowed = DOMAIN_CAP.get(domain, top_n)
        if domain_counts.get(domain, 0) >= allowed:
            continue
        selection.append(item)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if len(selection) >= top_n:
            break
    if len(selection) < top_n:
        for item in sorted_results:
            if item in selection:
                continue
            selection.append(item)
            if len(selection) >= top_n:
                break
    return selection


def select_top_values(results: List[Dict], top_n: int = 5) -> List[Dict]:
    return sorted(results, key=lambda item: item["total_score"], reverse=True)[:top_n]


def summarise_rules(item: Dict) -> List[str]:
    rules: List[str] = []
    if item["evidence"]:
        rules.append(f"keywords: {', '.join(item['evidence'])}")
    if item["best_exemplar"]:
        rules.append(f"semantic exemplar: {item['best_exemplar']}")
    if item["context_rules"]:
        rules.extend(item["context_rules"])
    if item["role_prior"] > 0.6:
        rules.append(f"role_prior boost for {ROLE_TYPE}")
    return rules


def generate_interview_questions(strengths: List[Dict], values: List[Dict]) -> List[Dict[str, str]]:
    questions: List[Dict[str, str]] = []
    for item in strengths[:2]:
        probe = (
            f"Walk me through a time you used {item['name']} to settle a complex customer issue. "
            "What was the situation, what action did you take, and what changed?"
        )
        questions.append(
            {
                "question": (
                    f"How have you demonstrated {item['name']} when handling high-volume support?"
                ),
                "probe": probe,
            }
        )
    if values:
        value = values[0]
        questions.append(
            {
                "question": (
                    f"Tell me about a time your {value['name']} value was challenged during service delivery."
                ),
                "probe": "Describe the situation, the tension, actions you took, and the result.",
            }
        )
    while len(questions) < 3:
        questions.append(
            {
                "question": "Describe a moment you balanced customer care with policy adherence.",
                "probe": "Outline the context, your judgement, and the outcome.",
            }
        )
    return questions[:3]


def build_attribute_payload(item: Dict) -> Dict:
    return {
        "name": item["name"],
        "domain": item["domain"],
        "score": round(item["total_score"], 4),
        "score_breakdown": {
            "keyword_match": round(item["keyword_score_norm"], 4),
            "semantic_sim": round(item["semantic_score_norm"], 4),
            "role_priors": round(item["role_prior"], 4),
            "context_mods": round(item["context_score_norm"], 4),
        },
        "evidence": item["evidence"],
        "best_exemplar": item["best_exemplar"],
        "rules_fired": summarise_rules(item),
    }


def calculate_profiles(
    job_summary: str,
    key_responsibilities: str,
    other_skills: str,
    toggles: Optional[ToggleMap] = None,
) -> Tuple[List[Dict], List[Dict], Dict[str, Dict]]:
    strength_results, strength_evidence = score_attributes(
        STRENGTHS_DEFINITIONS,
        job_summary,
        key_responsibilities,
        other_skills,
        toggles,
    )
    value_results, value_evidence = score_attributes(
        VALUE_DEFINITIONS,
        job_summary,
        key_responsibilities,
        other_skills,
        toggles,
    )
    top_strengths = [build_attribute_payload(item) for item in select_top_strengths(strength_results)]
    top_values = [build_attribute_payload(item) for item in select_top_values(value_results)]
    explainability = {
        "strengths": {item["name"]: item for item in top_strengths},
        "values": {item["name"]: item for item in top_values},
        "all_evidence": list(dict.fromkeys(strength_evidence + value_evidence)),
    }
    return top_strengths, top_values, explainability


def compute_attribute_map(results: List[Dict]) -> Dict[str, Dict]:
    return {item["name"]: item for item in results}
