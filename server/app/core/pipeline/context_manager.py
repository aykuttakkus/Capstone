from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from server.app.core.pipeline.risk_state import RiskState


@dataclass(slots=True)
class ConversationContext:
    """P3: Superseded by ContextPackage. Retained only for backward compatibility."""

    user_id: int
    session_id: str
    current_message: str
    topic: str
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    mood_trend: str | None = None
    distress_level: int = 0
    previous_topics: list[str] = field(default_factory=list)
    engagement_level: int = 1
    user_preferences: dict[str, Any] = field(default_factory=dict)
    screening_state: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ContextPackage:
    current_user_message: str
    recent_conversation: list[dict[str, Any]] = field(default_factory=list)
    session_summary: dict[str, Any] = field(default_factory=dict)
    user_state: dict[str, Any] = field(default_factory=dict)
    risk_state: RiskState = field(default_factory=lambda: RiskState(current_risk_level="none"))
    response_policy: dict[str, Any] = field(default_factory=dict)
    resolved_references: list[str] = field(default_factory=list)
    new_context_signals: list[str] = field(default_factory=list)
    possible_contradictions: list[str] = field(default_factory=list)
    previously_suggested_strategies: list[str] = field(default_factory=list)


class ContextManager:
    def __init__(self, max_history: int = 10) -> None:
        self.max_history = max_history
        self.conversation_cache: dict[str, ConversationContext] = {}

    def build_context(
        self,
        user_id: int,
        session_id: str,
        current_message: str,
        topic: str,
        conversation_history: list[dict[str, str]] | None = None,
        user_profile: dict[str, Any] | None = None,
        screening_state: dict[str, Any] | None = None,
    ) -> ConversationContext:
        """Build comprehensive conversation context from available data."""

        # Extract recent turns (keep last N)
        recent_turns = []
        if conversation_history:
            recent_turns = conversation_history[-self.max_history :]

        # Analyze mood trend from history
        mood_trend = self._analyze_mood_trend(recent_turns)

        # Calculate distress level from history
        distress_level = self._calculate_distress_level(recent_turns, current_message)

        # Extract topic history
        previous_topics = self._extract_topics(recent_turns)

        # Get user preferences
        user_preferences = user_profile or {}

        # Build context
        context = ConversationContext(
            user_id=user_id,
            session_id=session_id,
            current_message=current_message,
            topic=topic,
            recent_turns=recent_turns,
            mood_trend=mood_trend,
            distress_level=distress_level,
            previous_topics=previous_topics,
            engagement_level=self._calculate_engagement(recent_turns),
            user_preferences=user_preferences,
            screening_state=screening_state or {},
        )

        # Cache for quick access
        self.conversation_cache[session_id] = context

        return context

    def build_context_package(
        self,
        *,
        current_user_message: str,
        recent_conversation: list[dict[str, Any]] | None = None,
        session_summary: dict[str, Any] | str | None = None,
        user_state: dict[str, Any] | None = None,
        risk_state: RiskState | None = None,
        response_policy: dict[str, Any] | None = None,
        max_turns: int = 8,
        include_summaries: bool = True,
        include_key_entities: bool = True,
        include_risk_evolution: bool = True,
        previous_responses: list[str] | None = None,
    ) -> ContextPackage:
        """Build the structured context package required by the v2.1 system.
        
        Enhanced with:
        - Conversation summaries
        - Key entities extraction
        - Risk evolution tracking
        - Previous responses for coherence
        """
        bounded_turns = self._normalize_recent_turns(recent_conversation or [], max_turns=max_turns)
        summary = self._normalize_session_summary(session_summary)
        effective_risk_state = risk_state or RiskState(current_risk_level="none")
        strategies = self._extract_suggested_strategies(bounded_turns, summary)
        
        # Enhanced features
        if include_summaries:
            summary = self._generate_conversation_summary(bounded_turns, summary)
        
        key_entities = []
        if include_key_entities:
            key_entities = self._extract_key_entities(bounded_turns)
            summary["key_entities"] = key_entities
        
        if include_risk_evolution:
            risk_evolution = self._track_risk_evolution(bounded_turns, effective_risk_state)
            summary["risk_evolution"] = risk_evolution
        
        # Add previous responses for coherence
        if previous_responses:
            summary["previous_responses"] = previous_responses[-3:]  # Son 3 yanıt

        return ContextPackage(
            current_user_message=current_user_message,
            recent_conversation=bounded_turns,
            session_summary=summary,
            user_state=user_state or {},
            risk_state=effective_risk_state,
            response_policy=response_policy or self._default_response_policy(effective_risk_state),
            resolved_references=self._resolve_references(current_user_message, bounded_turns),
            new_context_signals=self._extract_new_context_signals(current_user_message),
            possible_contradictions=self._detect_possible_contradictions(current_user_message, summary),
            previously_suggested_strategies=strategies,
        )

    def get_cached_context(self, session_id: str) -> ConversationContext | None:
        return self.conversation_cache.get(session_id)

    def update_context(
        self,
        session_id: str,
        current_message: str,
        distress_level: int | None = None,
    ) -> ConversationContext | None:
        """Update existing context with new information."""

        context = self.conversation_cache.get(session_id)
        if not context:
            return None

        context.current_message = current_message

        if distress_level is not None:
            context.distress_level = distress_level

        return context

    def clear_cache(self, session_id: str) -> None:
        """Clear cached context for a session."""
        self.conversation_cache.pop(session_id, None)

    def _analyze_mood_trend(self, recent_turns: list[dict[str, str]]) -> str | None:
        """Analyze mood trend from recent conversation."""

        if not recent_turns:
            return None

        mood_keywords = {
            "improving": ["better", "good", "hopeful", "optimistic", "encouraged"],
            "declining": ["worse", "hopeless", "struggling", "difficult", "tired"],
            "stable": ["same", "managing", "okay", "fine"],
        }

        recent_text = " ".join([turn.get("user", "").lower() for turn in recent_turns[-3:]])

        for trend, keywords in mood_keywords.items():
            if any(kw in recent_text for kw in keywords):
                return trend

        return "neutral"

    def _calculate_distress_level(
        self, recent_turns: list[dict[str, str]], current_message: str
    ) -> int:
        """Calculate distress level (0-5) from conversation."""

        distress_keywords = {
            "crisis": ["suicide", "kill myself", "goodbye", "hopeless"],
            "high": ["overwhelming", "panic", "unbearable", "can't cope"],
            "moderate": ["struggling", "difficult", "worried", "anxious"],
            "low": ["manageable", "okay", "better", "improving"],
        }

        all_text = (
            " ".join([turn.get("user", "").lower() for turn in recent_turns])
            + " "
            + current_message.lower()
        )

        for level, keywords in distress_keywords.items():
            if any(kw in all_text for kw in keywords):
                return {"crisis": 5, "high": 4, "moderate": 2, "low": 1}.get(level, 1)

        return 1

    def _extract_topics(self, recent_turns: list[dict[str, str]]) -> list[str]:
        """Extract topic history from recent turns."""

        topics = []
        for turn in recent_turns:
            topic_hint = turn.get("metadata", {}).get("topic")
            if topic_hint:
                topics.append(topic_hint)

        return list(set(topics))  # Remove duplicates

    def _calculate_engagement(self, recent_turns: list[dict[str, str]]) -> int:
        """Calculate engagement level (1-5)."""

        if not recent_turns:
            return 1

        # More turns = higher engagement
        engagement = min(len(recent_turns) // 2, 5)
        return max(engagement, 1)

    def _normalize_recent_turns(
        self,
        turns: list[dict[str, Any]],
        *,
        max_turns: int,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for turn in turns[-max_turns:]:
            role = str(turn.get("role") or turn.get("speaker") or "user")
            content = str(turn.get("content") or turn.get("user") or turn.get("assistant") or "")
            if content:
                normalized.append(
                    {
                        "role": role,
                        "content": content,
                        "intent": turn.get("intent"),
                        "route": turn.get("route"),
                        "safety_mode": turn.get("safety_mode"),
                    }
                )
        return normalized

    def _normalize_session_summary(self, summary: dict[str, Any] | str | None) -> dict[str, Any]:
        if isinstance(summary, dict):
            return dict(summary)
        if not summary:
            return {}
        return {"recap": str(summary)}

    def _default_response_policy(self, risk_state: RiskState) -> dict[str, Any]:
        return {
            "max_questions": 1,
            "diagnosis_allowed": False,
            "medication_advice_allowed": False,
            "boundary_required": True,
            "escalation_required": risk_state.is_high_risk(),
        }

    def _resolve_references(self, message: str, recent_turns: list[dict[str, Any]]) -> list[str]:
        lowered = message.lower()
        reference_markers = ["this", "that", "same thing", "it", "bunu", "şunu", "aynı şey"]
        if not any(marker in lowered for marker in reference_markers):
            return []

        for turn in reversed(recent_turns):
            if turn.get("role") == "user":
                content = str(turn.get("content", "")).strip()
                if content:
                    return [content[:180]]
        return []

    def _extract_new_context_signals(self, message: str) -> list[str]:
        lowered = message.lower()
        signal_map = {
            "sleep_impact": ["sleep", "slept", "insomnia", "uyku", "uyuyam"],
            "panic": ["panic", "panik"],
            "exam_stress": ["exam", "final", "sınav"],
            "family_stress": ["family", "parent", "aile", "anne", "baba"],
            "work_stress": ["work", "job", "iş", "çalış"],
            "social_withdrawal": ["alone", "isolate", "yalnız", "uzaklaş"],
        }
        return [name for name, keywords in signal_map.items() if any(keyword in lowered for keyword in keywords)]

    def _detect_possible_contradictions(
        self,
        message: str,
        session_summary: dict[str, Any],
    ) -> list[str]:
        lowered = message.lower()
        recap = str(session_summary.get("recap", "")).lower()
        contradictions: list[str] = []
        improvement_markers = ["better", "improved", "passed", "fine now", "daha iyi", "geçti", "şimdi iyi"]
        distress_markers = ["anxious", "stress", "panic", "hopeless", "stressed", "kaygı", "stres", "panik"]
        if any(marker in lowered for marker in improvement_markers) and any(marker in recap for marker in distress_markers):
            contradictions.append("latest_message_may_update_or_resolve_prior_distress")
        if "not that" in lowered or "that's not" in lowered or "öyle değil" in lowered:
            contradictions.append("user_corrected_previous_interpretation")
        return contradictions

    def _extract_suggested_strategies(
        self,
        recent_turns: list[dict[str, Any]],
        session_summary: dict[str, Any],
    ) -> list[str]:
        strategies: set[str] = set()
        known = {
            "breathing": ["breath", "breathing", "nefes"],
            "grounding": ["grounding", "5-4-3-2-1", "topraklan"],
            "journaling": ["journal", "write down", "günlük", "yaz"],
            "sleep_routine": ["sleep routine", "bedtime", "uyku rutini"],
            "trusted_person": ["trusted person", "someone you trust", "güvendiğin"],
        }

        text_blocks = [str(session_summary.get("recap", ""))]
        text_blocks.extend(str(turn.get("content", "")) for turn in recent_turns if turn.get("role") == "assistant")
        combined = " ".join(text_blocks).lower()
        for strategy, keywords in known.items():
            if any(keyword in combined for keyword in keywords):
                strategies.add(strategy)

        explicit = session_summary.get("coping_tried")
        if isinstance(explicit, list):
            strategies.update(str(item) for item in explicit)

        return sorted(strategies)

    def _generate_conversation_summary(
        self,
        recent_turns: list[dict[str, Any]],
        existing_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate comprehensive conversation summary."""
        summary = dict(existing_summary)
        
        if not recent_turns:
            return summary
        
        # Extract main topics
        all_content = " ".join([str(turn.get("content", "")) for turn in recent_turns])
        summary["main_topics"] = self._extract_main_topics(all_content)
        
        # Track conversation flow
        summary["conversation_flow"] = self._analyze_conversation_flow(recent_turns)
        
        # Key concerns
        summary["key_concerns"] = self._extract_key_concerns(all_content)
        
        # Suggested strategies that were mentioned
        summary["strategies_discussed"] = self._extract_suggested_strategies(recent_turns, {})
        
        return summary
    
    def _extract_key_entities(self, recent_turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract key entities (people, places, concepts) from conversation."""
        entities = []
        
        # Entity patterns
        entity_patterns = {
            "work": ["iş", "work", "job", "meslek", "calisma", "ofis", "patron", "işyeri"],
            "family": ["aile", "family", "anne", "baba", "ebeveyn", "parent", "kardeş", "sibling"],
            "relationship": ["ilişki", "relationship", "partner", "eş", "sevgili", "boyfriend", "girlfriend"],
            "health": ["sağlık", "health", "doktor", "doctor", "hastane", "hospital", "ilaç", "medication"],
            "sleep": ["uyku", "sleep", "uyumak", "yatmak", "bed", "yatak"],
            "anxiety": ["anksiyete", "anxiety", "kaygı", "worry", "endişe", "concern"],
            "depression": ["depresyon", "depression", "mutsuz", "unhappy", "üzgün", "sad"],
            "social": ["sosyal", "social", "arkadaş", "friend", "topluluk", "community"],
        }
        
        all_content = " ".join([str(turn.get("content", "")).lower() for turn in recent_turns])
        
        for entity_type, keywords in entity_patterns.items():
            if any(kw in all_content for kw in keywords):
                # Find context around the entity
                for keyword in keywords:
                    if keyword in all_content:
                        idx = all_content.find(keyword)
                        start = max(0, idx - 50)
                        end = min(len(all_content), idx + 50)
                        context = all_content[start:end]
                        
                        entities.append({
                            "type": entity_type,
                            "keyword": keyword,
                            "context": context,
                            "frequency": all_content.count(keyword),
                        })
                        break
        
        return entities
    
    def _track_risk_evolution(
        self,
        recent_turns: list[dict[str, Any]],
        current_risk_state: RiskState,
    ) -> dict[str, Any]:
        """Track how risk level has evolved throughout conversation."""
        # Convert string risk level to int
        risk_level_map = {"none": 0, "low": 1, "medium": 2, "high": 3, "crisis": 4}
        current_level_int = risk_level_map.get(current_risk_state.current_risk_level, 0)
        
        evolution = {
            "current_level": current_risk_state.current_risk_level,
            "current_level_int": current_level_int,
            "highest_level": current_level_int,
            "trend": "stable",
            "risk_points": [],
        }
        
        # Analyze each turn for risk signals
        for i, turn in enumerate(recent_turns):
            content = str(turn.get("content", "")).lower()
            turn_risk = 0
            
            # Risk indicators
            if any(kw in content for kw in ["suicide", "kill myself", "intihar", "öldürmek"]):
                turn_risk = 5
            elif any(kw in content for kw in ["self-harm", "hurt myself", "zarar", "kesmek"]):
                turn_risk = 4
            elif any(kw in content for kw in ["hopeless", "umutsuz", "çaresiz", "değersiz"]):
                turn_risk = 3
            elif any(kw in content for kw in ["anxious", "worried", "kaygılı", "stressed"]):
                turn_risk = 2
            
            if turn_risk > 0:
                evolution["risk_points"].append({
                    "turn": i,
                    "risk_level": turn_risk,
                    "snippet": content[:100],
                })
                evolution["highest_level"] = max(evolution["highest_level"], turn_risk)
        
        # Determine trend
        if len(evolution["risk_points"]) >= 2:
            first = evolution["risk_points"][0]["risk_level"]
            last = evolution["risk_points"][-1]["risk_level"]
            if last > first:
                evolution["trend"] = "increasing"
            elif last < first:
                evolution["trend"] = "decreasing"
            else:
                evolution["trend"] = "stable"
        
        return evolution
    
    def _extract_main_topics(self, content: str) -> list[str]:
        """Extract main topics from conversation content."""
        topics = []
        topic_keywords = {
            "work_stress": ["iş", "work", "meslek", "patron", "işyeri", "ofis"],
            "family_issues": ["aile", "family", "ebeveyn", "anne", "baba"],
            "relationship": ["ilişki", "relationship", "partner", "eş", "sevgili"],
            "mental_health": ["mental", "psikoloji", "ruh sağlığı", "therapy", "terapi"],
            "anxiety": ["anksiyete", "anxiety", "kaygı", "endişe"],
            "depression": ["depresyon", "depression", "mutsuzluk"],
            "sleep": ["uyku", "sleep", "uykusuzluk", "insomnia"],
            "social": ["sosyal", "social", "yalnızlık", "loneliness"],
        }
        
        content_lower = content.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def _analyze_conversation_flow(self, recent_turns: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze the flow and progression of conversation."""
        flow = {
            "total_turns": len(recent_turns),
            "user_turns": sum(1 for turn in recent_turns if turn.get("role") == "user"),
            "assistant_turns": sum(1 for turn in recent_turns if turn.get("role") == "assistant"),
            "progression": [],
        }
        
        # Track conversation progression
        intents = [turn.get("intent") for turn in recent_turns if turn.get("intent")]
        if intents:
            flow["progression"] = intents
            flow["most_common_intent"] = max(set(intents), key=intents.count) if intents else None
        
        return flow
    
    def _extract_key_concerns(self, content: str) -> list[str]:
        """Extract key concerns or problems mentioned."""
        concerns = []
        concern_patterns = [
            (r"(zorlanıyorum|struggling with|having trouble with) ([^,.]+)", "struggling"),
            (r"(endişeliyim|worried about|concerned about) ([^,.]+)", "worried"),
            (r"(korkuyorum|afraid of|scared of) ([^,.]+)", "afraid"),
            (r"(yorgunum|tired of|exhausted from) ([^,.]+)", "tired"),
        ]
        
        content_lower = content.lower()
        for pattern, concern_type in concern_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                if isinstance(match, tuple):
                    concerns.append(f"{concern_type}: {match[1]}")
                else:
                    concerns.append(f"{concern_type}: {match}")
        
        return concerns[:5]  # Max 5 concerns

    def get_summary(self, context: ConversationContext) -> str:
        """Generate a summary of the conversation context."""

        summary = f"""
Conversation Context Summary:
- User ID: {context.user_id}
- Topic: {context.topic}
- Distress Level: {context.distress_level}/5
- Mood Trend: {context.mood_trend}
- Engagement: {context.engagement_level}/5
- Recent Turns: {len(context.recent_turns)}
- Previous Topics: {', '.join(context.previous_topics) if context.previous_topics else 'None'}
"""
        return summary.strip()
