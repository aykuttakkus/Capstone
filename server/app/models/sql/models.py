from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.sql import func
from server.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Clinical Profile Fragment
    last_phq9_score = Column(Integer, nullable=True)
    last_screening_date = Column(DateTime, nullable=True)


class UserClinicalState(Base):
    __tablename__ = "user_clinical_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    screening_completed = Column(Boolean, nullable=False, default=False)
    last_phq9_score = Column(Integer, nullable=True)
    last_gad7_score = Column(Integer, nullable=True)
    last_screening_date = Column(DateTime, nullable=True)
    screening_completed_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    summary_nuggets = Column(Text, nullable=True)  # Summarized clinical insights
    sentiment_trend = Column(String, nullable=True) # e.g. "improving", "unstable"
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    preferred_name = Column(String, nullable=True)
    age_group = Column(String, nullable=True)
    therapy_status = Column(String, nullable=True)
    primary_concerns = Column(Text, nullable=True)
    main_triggers = Column(Text, nullable=True)
    support_system = Column(Text, nullable=True)
    coping_strategies_helpful = Column(Text, nullable=True)
    coping_strategies_unhelpful = Column(Text, nullable=True)
    communication_style = Column(String, nullable=True)
    response_length_preference = Column(String, nullable=True)
    sleep_context = Column(Text, nullable=True)
    stress_context = Column(Text, nullable=True)
    goals_for_support = Column(Text, nullable=True)
    personalization_consent = Column(Boolean, nullable=False, default=True)
    use_mood_context = Column(Boolean, nullable=False, default=False)
    use_journal_context = Column(Boolean, nullable=False, default=False)
    use_memory_context = Column(Boolean, nullable=False, default=True)
    life_narrative = Column(Text, nullable=True)
    intake_completed = Column(Boolean, nullable=False, default=False)
    last_profile_refresh_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ChatSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False, default="New session")
    topic = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    summary = Column(Text, nullable=True)
    last_safety_mode = Column(String, nullable=True)
    intake_json = Column(Text, nullable=True)
    consent_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)


class MemorySegment(Base):
    __tablename__ = "memory_segments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)
    segment_type = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    topic = Column(String, nullable=True, index=True)
    confidence = Column(Float, nullable=False, default=0.5)
    source_turn_range = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)


class MemoryReflection(Base):
    __tablename__ = "memory_reflections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    insight_type = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    evidence_refs = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.5)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String, nullable=True)
    route = Column(String, nullable=True)
    safety_mode = Column(String, nullable=True)
    sources_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    route = Column(String, nullable=True)
    helpful = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    safety_mode = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MoodEntry(Base):
    __tablename__ = "mood_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mood_score = Column(Integer, nullable=False)
    energy_score = Column(Integer, nullable=True)
    anxiety_score = Column(Integer, nullable=True)
    sleep_quality = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    sentiment_label = Column(String, nullable=True)
    topics_json = Column(Text, nullable=True)
    risk_flag = Column(Boolean, nullable=False, default=False)
    consent_for_chat = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
