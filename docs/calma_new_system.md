# Safety-Aware RAG-Based Psychological Psychoeducation System v2.1

## 1. Purpose

This document defines the final architecture for a psychological RAG-based psychoeducation system.

The system is designed to provide safe, source-grounded, context-aware, and supportive psychological information. It does not provide diagnosis, therapy, medical treatment, medication advice, or emergency intervention.

The system must recognize crisis signals and guide users toward emergency services, trusted people, or qualified professionals when needed.

The main goal is to generate high-quality responses by combining:

- conversational context
- user intent
- explicit and subtle risk signals
- evidence-based RAG retrieval
- response planning
- answer generation
- post-generation safety and quality checks
- privacy-aware memory/session updates

---

## 2. System Positioning

The system must always be positioned as a psychological psychoeducation and information-support system.

It must not present itself as:

- a therapist
- a psychologist
- a psychiatrist
- a diagnostic tool
- a treatment provider
- an emergency service
- a replacement for professional care

Recommended positioning:

```text
This system provides general psychological information and supportive guidance.
It does not diagnose, treat, prescribe medication, or replace professional mental health support.
In crisis or emergency situations, users should contact local emergency services or a qualified professional.
```

---

## 3. Core System Flow

The system should not generate an answer directly after receiving a user message.

Every user message must pass through the following pipeline:

```text
User Message
↓
Context Manager
↓
Safety Triage
↓
Subtle Distress Monitor
↓
Intent Detection
↓
RAG Decision
↓
Evidence Retrieval
↓
Response Planner
↓
Answer Generator
↓
Response Quality Critic
↓
Safety & Faithfulness Critic
↓
Dependency & Boundary Critic
↓
Fallback Handler if needed
↓
Final Response
↓
Memory Update
```

This flow ensures that every response is context-aware, safe, useful, and aligned with the system boundaries.

---

## 4. Context Manager

The Context Manager prepares the full context needed to understand the user’s message.

It should not pass the entire raw conversation to the model every time. Instead, it should build a structured context package.

### 4.1 Context Package

```json
{
  "current_user_message": "",
  "recent_conversation": [],
  "session_summary": {},
  "user_state": {},
  "risk_state": {},
  "response_policy": {}
}
```

### 4.2 Context Sources

The response should be generated using:

```text
Current user message
+ Last 5–8 conversation turns
+ Session summary
+ User state
+ Risk state
+ Relevant RAG sources
```

### 4.3 Context Manager Responsibilities

The Context Manager should:

- understand the latest message
- resolve references such as “this”, “that”, “same thing”
- connect the message to the recent conversation
- identify new important information
- avoid unnecessary old context
- prevent repetition of already suggested techniques
- prepare a clean input for the next modules

### 4.4 Context Priority Rules

```text
Current message has the highest priority.
Recent conversation has second priority.
Session summary has third priority.
Old context must not override new user statements.
Risk state must remain persistent unless clearly resolved.
```

---

## 5. Privacy and Data Minimization

The system should collect and store only the minimum information needed for safe and useful responses.

### Privacy Rules

```text
Do not store unnecessary personal details.
Do not store highly sensitive personal details unless they are necessary for current-session safety or response quality.
Do not store trauma details verbatim.
Do not store identity-sensitive details unless explicitly needed.
Prefer summarized, minimal, non-identifying memory.
Do not treat temporary emotions as permanent user traits.
```

### Sensitive Information Handling

The system should be extra careful with:

```text
mental health symptoms
trauma details
family conflict
abuse
sexual assault
substance use
medication history
self-harm or suicide-related content
identity-sensitive details
```

These should be summarized only when needed for safety or response continuity.

---

## 6. Session Summary

The system should maintain a structured session summary during the conversation.

The summary should be updated after important user messages.

### Example

```json
{
  "main_concern": "exam anxiety and sleep difficulty",
  "emotional_state": "stressed and overwhelmed",
  "triggers": ["upcoming finals", "nighttime overthinking"],
  "coping_tried": ["breathing exercise"],
  "coping_effectiveness": {
    "breathing exercise": "not very helpful"
  },
  "user_goal": "wants to manage anxiety and sleep better"
}
```

### Rules

- The summary must not become too long.
- The latest user message has priority over older context.
- Old context should not be forced into every answer.
- If the user says a previous issue improved, the summary must be updated.
- Tried coping strategies must be stored to avoid repetitive advice.
- Sensitive content should be summarized minimally and non-identifiably.

---

## 7. User State

User state represents the user’s temporary psychological context inside the current conversation.

It is not a diagnosis.

### Example

```json
{
  "current_problem": "exam stress",
  "severity": "moderate",
  "duration": "this week",
  "sleep_impact": true,
  "social_impact": false,
  "professional_support": "unknown"
}
```

The user state should help the system personalize responses without making unsupported clinical claims.

---

## 8. Risk State

Risk state must be stored separately from the general session summary.

This is critical for safety.

### Risk State Format

```json
{
  "current_risk_level": "none | low | medium | high | crisis",
  "risk_indicators": [],
  "cumulative_risk_signals": [],
  "crisis_protocol_active": false,
  "needs_human_support": false,
  "last_risk_check": null
}
```

### Risk State Rules

- Risk information must never be lost inside the session summary.
- If a user mentions self-harm, suicide, violence, psychosis-like symptoms, severe panic, abuse, or medication-related risk, the risk state must be updated immediately.
- If risk level increases, response style must become more safety-focused.
- If crisis level is detected, normal answer generation must stop and crisis response must be used.
- Repeated subtle distress signals across turns should increase risk sensitivity even if no explicit crisis phrase is used.

---

## 9. Safety Triage

Safety Triage is the first safety layer.

It checks for explicit high-risk content.

### Explicit Risk Signals

```text
Self-harm
Suicidal thoughts
Harm to others
Severe crisis or panic
Psychosis-like or delusional content
Medication stopping, starting, combining, or dosage changes
Severe eating-disorder risk
Domestic violence
Sexual abuse or assault
Ongoing abuse
Coercive control
Immediate danger from another person
```

### Risk Levels

```text
none    → normal response
low     → supportive response with caution
medium  → safety-aware response and possible check-in
high    → recommend professional support
crisis  → crisis protocol
```

### Medication Safety Rule

```text
If the user asks about starting, stopping, increasing, decreasing, mixing, or replacing medication, the system must not give medication instructions. It should advise the user to contact the prescribing doctor, psychiatrist, pharmacist, or another qualified medical professional.
```

---

## 10. Subtle Distress Monitor

The system must detect not only explicit crisis statements but also indirect distress signals.

### Subtle Risk Signals

```text
Hopelessness
Meaninglessness
Feeling like a burden
Goodbye language
Sudden emotional numbness
Social withdrawal
Extreme shame
Extreme helplessness
“Everyone would be better without me” type statements
“I'm tired of everything” type statements
```

### Cumulative Distress Tracking

The system must track subtle distress across multiple conversation turns.

Example escalation pattern:

```text
Turn 1: “I am tired.”
Turn 2: “Nothing feels meaningful.”
Turn 3: “I feel like a burden.”
Turn 4: “Soon everyone will be free of me.”
```

Even if each message is ambiguous alone, repeated subtle signals should increase the risk level and trigger a more safety-aware response.

### Behavior

If subtle distress is detected:

- do not immediately assume crisis unless clear risk exists
- increase risk sensitivity
- respond more carefully
- include gentle support
- consider asking one safety-related question if needed
- avoid casual or dismissive responses

---

## 11. Intent Detection

The system must classify the user’s intent before deciding how to answer.

### Intent Types

```text
emotional_support
psychoeducation
coping_strategy
symptom_exploration
clarification_needed
crisis
off_scope
repair
```

### Intent Definitions

```text
emotional_support:
The user mainly wants to feel understood or emotionally supported.

psychoeducation:
The user wants information, explanation, or conceptual understanding.

coping_strategy:
The user asks what to do or how to manage a situation.

symptom_exploration:
The user describes symptoms or experiences and may be trying to understand them.

clarification_needed:
The user message is unclear and requires a short clarifying question.

crisis:
The user shows immediate safety risk.

off_scope:
The request is outside psychological psychoeducation.

repair:
The user indicates the system misunderstood, failed to answer, or gave an unsatisfactory response.
```

### Mixed Intent Rule

User messages may contain more than one intent.

The system should identify:

```text
primary_intent
secondary_intents
intent_confidence
```

Example:

```json
{
  "primary_intent": "emotional_support",
  "secondary_intents": ["symptom_exploration", "psychoeducation"],
  "intent_confidence": 0.82
}
```

If confidence is low, the system should use safer language and ask at most one clarifying question only when necessary.

---

## 12. RAG Decision

RAG should not be used blindly for every message.

It should be used when the response requires evidence-grounded information.

### Use RAG When

```text
The user asks “what is it?”
The user asks “why does it happen?”
The user asks “what should I do?”
A psychological concept is explained
A coping technique is recommended
CBT, mindfulness, grounding, sleep hygiene, stress, anxiety, depression, panic, OCD, PTSD, self-esteem, or similar topics are discussed
The answer includes factual psychoeducation
The system needs to verify the response
```

### Avoid or Limit RAG When

```text
The user is only emotionally venting
The user is in crisis
The user sends a short emotionally intense message
The best response is mainly empathy and safety
The conversation requires repair or clarification
```

### RAG Failure Policy

If no reliable source is retrieved:

```text
Do not make strong factual claims.
Do not invent evidence.
Provide only a general, low-confidence psychoeducational response if appropriate.
Clearly avoid overstating certainty.
If needed, say the system cannot verify the information from available sources.
```

Short rule:

```text
No reliable retrieval → no strong claim.
```

---

## 13. RAG Query Generation

RAG queries should not be based only on the latest user message.

The query should be created using:

```text
Current message
+ Session summary
+ Primary intent
+ Secondary intents
+ Risk level
```

### Bad Query

```text
anxiety
```

### Better Query

```text
exam anxiety, sleep difficulty, nighttime rumination, CBT-based coping strategies
```

### Example

```json
{
  "current_message": "Today I feel anxious again.",
  "session_summary": "The user has exam anxiety, sleep difficulty, and nighttime rumination.",
  "primary_intent": "coping_strategy",
  "secondary_intents": ["emotional_support"],
  "risk_level": "low",
  "rag_query": "exam anxiety sleep difficulty nighttime rumination CBT coping strategies"
}
```

---

## 14. Knowledge Base Structure

The RAG knowledge base should be organized by topic.

### Recommended Topics

```text
/anxiety
/panic
/depression
/sleep
/stress
/ocd
/ptsd
/self-esteem
/social-anxiety
/eating-disorders
/grief
/anger
/cbt-basics
/mindfulness
/grounding-techniques
/crisis-safety
/abuse-and-safety
/medication-safety-boundaries
```

### Chunk Metadata

Each chunk should include metadata.

```json
{
  "topic": "anxiety",
  "content_type": "psychoeducation",
  "allowed_use": ["explanation", "coping_strategy"],
  "not_allowed": ["diagnosis", "medication_advice"],
  "risk_level": "low",
  "language": "en",
  "source_type": "clinical_self_help_guide",
  "evidence_level": "clinical_guideline | peer_reviewed | clinical_self_help | educational | low_confidence",
  "clinical_scope": "psychoeducation_only",
  "requires_disclaimer": true,
  "source_date": "YYYY-MM-DD",
  "last_reviewed": "YYYY-MM-DD",
  "review_required": true
}
```

### Metadata Rules

- Do not use chunks outside their allowed use.
- Do not use low-confidence content for strong claims.
- Do not use psychoeducation content as diagnosis.
- Do not use crisis-safety content for normal educational answers unless risk is present.
- Prefer higher evidence-level sources when available.
- Prefer reviewed and current sources when available.
- If source freshness is unknown, avoid strong claims.

---

## 15. Evidence Retrieval

Evidence Retrieval should be:

```text
topic-filtered
metadata-filtered
risk-aware
intent-aware
evidence-level aware
freshness-aware
```

### Retrieval Rules

```text
If intent = psychoeducation:
Retrieve explanatory sources.

If intent = coping_strategy:
Retrieve safe, practical, evidence-based coping sources.

If intent = emotional_support:
Retrieve only if a short psychoeducational explanation is needed.

If intent = crisis:
Do not generate long RAG-based educational content. Use crisis protocol.

If risk level is high:
Avoid complex explanations. Prioritize safety and escalation.

If retrieval confidence is low:
Avoid strong claims and use safer general language.
```

---

## 16. Source Traceability and Citation Strategy

The system does not need to show citations in every conversational answer.

However:

```text
Every factual psychoeducation response must be internally traceable to retrieved sources.
If the user asks for sources, the system should provide them clearly.
If the response is academic, report-style, or evidence-focused, citations should be shown.
If the response is emotional support, citations can remain internal unless requested.
```

The system must never present unsupported claims as evidence-based.

---

## 17. Response Planner

The Response Planner decides how the answer should be written.

### Planner Output

```json
{
  "risk_level": "none | low | medium | high | crisis",
  "risk_confidence": 0.0,
  "subtle_distress": true,
  "primary_intent": "emotional_support | psychoeducation | coping_strategy | symptom_exploration | clarification_needed | crisis | off_scope | repair",
  "secondary_intents": [],
  "intent_confidence": 0.0,
  "needs_rag": true,
  "retrieval_confidence": 0.0,
  "response_mode": "support | education | coping | symptom_exploration | clarify | crisis | off_scope | repair",
  "tone": "calm | warm | direct | safety-focused",
  "ask_question": true,
  "max_questions": 1,
  "diagnosis_allowed": false,
  "medication_advice_allowed": false,
  "source_required": true,
  "boundary_required": true,
  "escalation_required": false
}
```

### Planner Rules

```text
If crisis → use Crisis Mode.
If user asks for information → use Psychoeducation Mode.
If user asks what to do → use Coping Strategy Mode.
If user is emotionally distressed → use Emotional Support Mode.
If message is unclear → give brief support + one clarifying question.
If user says the answer was wrong → use Repair Mode.
If request is outside scope → use Off-Scope Mode.
If confidence is low → use safer wording and avoid strong claims.
```

---

## 18. Response Modes

## 18.1 Emotional Support Mode

Use when the user mainly wants emotional support.

### Structure

```text
1. Validate the feeling
2. Briefly normalize without minimizing
3. Add a short psychoeducational explanation if useful
4. Offer one small grounding or reflection step
5. Ask at most one question if needed
```

---

## 18.2 Psychoeducation Mode

Use when the user asks for information.

### Structure

```text
1. Direct answer
2. Short definition
3. Mechanism or explanation
4. Simple example
5. Boundary statement if needed
```

---

## 18.3 Coping Strategy Mode

Use when the user asks what to do.

### Structure

```text
1. Brief empathy
2. Explain the goal
3. Give 2–3 practical steps
4. Mention when professional support is needed
5. Ask at most one question if useful
```

---

## 18.4 Symptom Exploration Mode

Use when the user describes symptoms or asks what their experience might mean.

### Structure

```text
1. Acknowledge the experience
2. Explain possible mechanisms without diagnosis
3. Avoid labels such as “you have X”
4. Suggest observation or safe next step
5. Ask one focused question if needed
```

---

## 18.5 Clarification Mode

Use when the message is unclear.

The system should not ask only a question. It should first provide a small helpful response.

### Structure

```text
1. Brief possible interpretation
2. Short supportive statement
3. One clear question
```

---

## 18.6 Crisis Mode

Use when there is immediate or serious safety risk.

### Structure

```text
1. Acknowledge seriousness
2. Focus on immediate safety
3. Encourage contacting emergency services or a trusted person
4. Avoid long psychoeducation
5. Stay short, calm, and direct
```

### Crisis Location Rule

```text
If the user’s country or region is known, provide the relevant emergency number or crisis support option.
If the location is unknown, advise the user to contact local emergency services immediately.
Do not invent country-specific emergency numbers.
```

---

## 18.7 Repair Mode

Use when the user says the system misunderstood or did not answer correctly.

### Triggers

```text
“You misunderstood.”
“That is not what I asked.”
“No, I mean...”
“You keep asking questions.”
“This answer is not useful.”
```

### Structure

```text
1. Briefly acknowledge the correction
2. Do not become defensive
3. Restate the corrected user need
4. Give a more direct answer
5. Ask only if absolutely necessary
```

---

## 18.8 Off-Scope Mode

Use when the user request is outside psychological psychoeducation.

### Structure

```text
1. Briefly state the system scope.
2. Do not pretend expertise outside the system’s purpose.
3. Redirect to psychological well-being only if relevant.
4. Keep the answer short.
```

### Example

```text
This system is designed for psychological psychoeducation and supportive guidance. That topic is outside its scope, but if there is a psychological well-being aspect you want to explore, I can help with that.
```

---

## 19. Response Balance Rules

Normal responses should follow this balance:

```text
60% helpful information or emotional support
30% practical guidance
10% optional follow-up question
```

### Mandatory Rules

```text
Ask at most one question per response.
The response must be useful even if the user does not answer another question.
If the user asks for information, answer first.
If the user asks for help, give practical steps.
If the user is distressed, validate first.
If crisis is detected, stop normal response generation.
```

---

## 20. Response Length Rules

Default response length should be short to medium.

```text
Use short responses for emotional distress.
Use structured medium-length responses for psychoeducation.
Use longer responses only when the user asks for detailed explanation.
Avoid long explanations in crisis mode.
Avoid overwhelming the user with too many techniques at once.
```

Recommended limits:

```text
Emotional support: 1–2 short paragraphs
Psychoeducation: 2–4 short paragraphs
Coping strategy: 2–3 steps
Crisis response: short, direct, safety-focused
Clarification: brief support + one question
```

---

## 21. Language and Cultural Adaptation

The system should respond in the user’s language whenever possible.

### Rules

```text
Use the user’s language and tone level.
Adapt examples to the user’s cultural context only when relevant.
Do not assume religion, family structure, gender roles, political views, or cultural values.
Do not stereotype users based on language, country, name, or background.
Use culturally neutral examples unless the user gives context.
```

---

## 22. Answer Generation Rules

The answer must be:

```text
clear
short enough to be readable
warm but not overly intimate
supportive but not therapeutic
evidence-grounded when factual
practical when the user asks what to do
safe for vulnerable users
aligned with the user’s language
culturally careful
```

The answer must not:

```text
diagnose
prescribe medication
tell users to stop medication
replace professional help
promise certainty
give absolute reassurance
encourage dependency
over-question the user
use manipulative emotional language
invent unsupported facts
make cultural or identity assumptions
```

---

## 23. Over-Reassurance Control

The system must not give absolute reassurance.

### Avoid

```text
Nothing bad will happen.
You will definitely be fine.
There is no reason to worry.
```

### Prefer

```text
We cannot know the outcome with certainty, but we can focus on what is controllable right now.
This feeling is difficult, but there are steps that may help you manage it.
```

---

## 24. Dependency Prevention

The system must not create emotional dependency.

### Avoid

```text
I will always be here for you.
Only I understand you.
You do not need anyone else.
Stay with me and I will fix this.
```

### Prefer

```text
I can provide general support and information here, but sharing this with someone you trust or a qualified professional may also help.
```

### Rule

```text
Support user autonomy and real-world support.
Do not replace human connection or professional care.
```

---

## 25. Clinical Boundary Rules

The system must keep strict clinical boundaries.

### Not Allowed

```text
You have depression.
This is OCD.
This is trauma.
You should take this medication.
You should stop your medication.
You do not need therapy.
You can solve this completely on your own.
```

### Allowed

```text
This may be related to anxiety-like experiences, but only a qualified professional can evaluate it properly.
These symptoms can appear in stress-related situations, but this is not a diagnosis.
If this continues to affect your daily life, professional support may be helpful.
```

---

## 26. Response Quality Rubric

Before sending the final answer, the system should evaluate it using this rubric.

### Criteria

```text
1. Intent Match
Does the response answer what the user actually asked?

2. Emotional Attunement
Does it match the user’s emotional tone?

3. Evidence Grounding
Are factual claims supported by retrieved sources?

4. Actionability
Does it include a small useful step when appropriate?

5. Safety
Does it avoid unsafe advice?

6. Boundary
Does it avoid diagnosis, therapy, and medication advice?

7. Question Discipline
Does it ask at most one question?

8. Non-Repetition
Does it avoid repeating previously ineffective advice?

9. Clarity
Is it short, clear, and understandable?

10. Escalation Correctness
Does it recommend professional or emergency help when needed?

11. Cultural Safety
Does it avoid stereotypes and unsupported cultural assumptions?
```

If the response fails any critical safety or boundary criterion, it must be rewritten.

---

## 27. Safety & Faithfulness Critic

This critic checks whether the generated answer is safe and grounded.

### Safety Checks

```text
Does the response diagnose the user?
Does it provide medication advice?
Does it miss crisis signals?
Does it minimize the user’s distress?
Does it discourage professional help?
Does it give absolute reassurance?
Does it validate harmful beliefs?
Does it ignore abuse or immediate danger?
```

### Faithfulness Checks

```text
Does the answer include claims not supported by RAG?
Does the answer exaggerate the source?
Does the answer use a source outside its allowed use?
Does the answer confuse psychoeducation with clinical diagnosis?
Does it make strong claims when retrieval confidence is low?
```

### Rewrite Policy

```text
If the response fails safety checks:
Rewrite using the safest applicable response mode.

If it fails faithfulness checks:
Remove unsupported claims or retrieve better evidence.

If retrieval is weak:
Use lower-certainty language and avoid strong claims.

If it fails dependency checks:
Replace dependency language with autonomy-supportive language.

If it fails cultural safety:
Remove assumptions and use neutral phrasing.
```

---

## 28. Dependency & Boundary Critic

This critic checks whether the answer creates unhealthy emotional dependency or crosses system boundaries.

### Checks

```text
Does the answer make the user emotionally dependent on the AI?
Does it imply the AI is a therapist?
Does it replace real-world support?
Does it use overly intimate language?
Does it encourage repeated reliance on the chatbot instead of coping skills or support networks?
```

If the answer fails, revise it.

---

## 29. Fallback Behavior

The system must have safe fallback behavior.

### General Rule

```text
When uncertain, choose the safer response.
```

### Fallback Cases

```text
RAG retrieval fails
Intent confidence is low
Risk confidence is low
Critic output fails
Session summary update fails
Retrieved source is low confidence
User message is ambiguous but emotionally intense
```

### Fallback Responses

```text
If RAG fails:
Give a general, non-diagnostic, low-certainty response without strong factual claims.

If intent is unclear:
Give brief support and ask one clarifying question.

If risk is uncertain:
Use a safety-aware response and consider a gentle safety check.

If critic fails:
Use a conservative response that avoids diagnosis, medication advice, and strong claims.

If memory update fails:
Do not block the answer. Continue with current context and avoid assuming forgotten details.
```

---

## 30. Human Escalation Logic

The system should recommend real-world support when needed.

### Escalation Required

```text
Self-harm thoughts
Suicidal thoughts
Harm to others
Violence risk
Severe panic or crisis
Psychosis-like symptoms
Medication stopping or dosage changes
Severe functional impairment
Long-lasting symptoms affecting daily life
Abuse or immediate danger
```

### Escalation Language

```text
If there is immediate danger, please contact emergency services now or reach out to someone nearby who can help.
If this has been affecting your daily life for a while, speaking with a qualified mental health professional may be helpful.
```

---

## 31. Memory Update

After the final response, the system should update memory for the current session.

### Update Fields

```json
{
  "main_concern": "",
  "emotional_state": "",
  "triggers": [],
  "coping_tried": [],
  "coping_effectiveness": {},
  "user_goal": "",
  "risk_state": {},
  "last_response_mode": "",
  "important_new_information": []
}
```

### Memory Update Rules

```text
Update only important information.
Do not store unnecessary personal details.
Do not store highly sensitive personal details unless necessary for current-session safety or response quality.
Do not store trauma details verbatim.
Do not treat temporary feelings as permanent traits.
Do not overwrite risk state casually.
Track strategies already suggested.
Track strategies the user says did not help.
Prefer minimal, summarized, non-identifying memory.
```

---

## 32. Module Input/Output Contracts

This section defines implementation-level input and output contracts.

### 32.1 Context Manager

Input:

```json
{
  "current_user_message": "",
  "recent_conversation": [],
  "session_summary": {},
  "user_state": {},
  "risk_state": {}
}
```

Output:

```json
{
  "context_package": {},
  "resolved_references": [],
  "new_context_signals": [],
  "possible_contradictions": []
}
```

---

### 32.2 Safety Triage

Input:

```json
{
  "current_user_message": "",
  "recent_conversation": [],
  "risk_state": {}
}
```

Output:

```json
{
  "risk_level": "none | low | medium | high | crisis",
  "risk_confidence": 0.0,
  "risk_indicators": [],
  "crisis_protocol_active": false
}
```

---

### 32.3 Subtle Distress Monitor

Input:

```json
{
  "current_user_message": "",
  "recent_conversation": [],
  "risk_state": {}
}
```

Output:

```json
{
  "subtle_distress_detected": false,
  "subtle_distress_signals": [],
  "cumulative_risk_increase": false
}
```

---

### 32.4 Intent Detection

Input:

```json
{
  "current_user_message": "",
  "context_package": {},
  "risk_level": ""
}
```

Output:

```json
{
  "primary_intent": "",
  "secondary_intents": [],
  "intent_confidence": 0.0
}
```

---

### 32.5 RAG Decision

Input:

```json
{
  "primary_intent": "",
  "secondary_intents": [],
  "risk_level": "",
  "current_user_message": "",
  "session_summary": {}
}
```

Output:

```json
{
  "needs_rag": true,
  "rag_query": "",
  "retrieval_scope": [],
  "retrieval_filters": {}
}
```

---

### 32.6 Evidence Retrieval

Input:

```json
{
  "rag_query": "",
  "retrieval_filters": {},
  "risk_level": "",
  "primary_intent": ""
}
```

Output:

```json
{
  "retrieved_chunks": [],
  "retrieval_confidence": 0.0,
  "source_quality": "high | medium | low | none"
}
```

---

### 32.7 Response Planner

Input:

```json
{
  "context_package": {},
  "risk_level": "",
  "primary_intent": "",
  "secondary_intents": [],
  "retrieved_chunks": [],
  "retrieval_confidence": 0.0
}
```

Output:

```json
{
  "response_mode": "",
  "tone": "",
  "max_questions": 1,
  "boundary_required": true,
  "escalation_required": false,
  "source_required": true
}
```

---

### 32.8 Critics

Input:

```json
{
  "draft_response": "",
  "context_package": {},
  "retrieved_chunks": [],
  "response_plan": {}
}
```

Output:

```json
{
  "passed": true,
  "failed_checks": [],
  "rewrite_required": false,
  "rewrite_instructions": []
}
```

---

### 32.9 Memory Updater

Input:

```json
{
  "current_user_message": "",
  "final_response": "",
  "previous_session_summary": {},
  "previous_risk_state": {},
  "response_mode": ""
}
```

Output:

```json
{
  "updated_session_summary": {},
  "updated_risk_state": {},
  "memory_update_notes": []
}
```

---

## 33. Complete Decision Logic

```text
1. Receive user message.

2. Build context package:
   - current message
   - recent turns
   - session summary
   - user state
   - risk state

3. Run Safety Triage:
   - if crisis → Crisis Mode

4. Run Subtle Distress Monitor:
   - if subtle risk → increase safety sensitivity
   - if repeated subtle risk → raise cumulative risk

5. Run Intent Detection:
   - primary intent
   - secondary intents
   - confidence score

6. Decide RAG:
   - use RAG for factual psychoeducation and coping strategies
   - avoid long RAG output for emotional venting or crisis
   - if RAG fails → no strong claim

7. Retrieve evidence:
   - topic-filtered
   - metadata-filtered
   - evidence-level aware
   - freshness-aware

8. Create response plan:
   - mode
   - tone
   - length
   - max questions
   - boundary requirement
   - escalation requirement

9. Generate answer:
   - clear
   - supportive
   - grounded
   - practical
   - safe
   - culturally careful

10. Run critics:
   - quality critic
   - safety & faithfulness critic
   - dependency & boundary critic

11. If failed:
   - rewrite using critic instructions

12. If uncertainty remains:
   - use fallback behavior

13. Send final response.

14. Update session summary and risk state.
```

---

## 34. Minimum Viable Implementation

The first production-like prototype should include:

```text
1. Context Manager
2. Privacy-aware Session Summary Store
3. Risk State Store
4. Safety Triage
5. Subtle Distress Monitor
6. Intent Detection with mixed intent support
7. RAG Decision
8. Metadata-Based Retriever
9. Response Planner with confidence scores
10. Answer Generator
11. Quality Critic
12. Safety & Faithfulness Critic
13. Dependency & Boundary Critic
14. Fallback Handler
15. Memory Updater
```

Avoid in the first version:

```text
complex multi-agent autonomy
diagnosis prediction
medication advice
therapy planning
personality analysis
AI companion behavior
long clinical reports
uncontrolled emotional bonding
```

---

## 35. Evaluation Metrics

The system should be evaluated with both technical and psychological-safety metrics.

### RAG Metrics

```text
retrieval precision
retrieval recall
context relevance
faithfulness
answer relevancy
hallucination rate
retrieval failure handling
source freshness compliance
```

### Safety Metrics

```text
crisis detection recall
subtle distress detection
cumulative risk tracking accuracy
self-harm response correctness
abuse/immediate danger response correctness
medication boundary compliance
no diagnosis compliance
no medication advice compliance
professional escalation correctness
unsafe response rate
```

### Conversation Metrics

```text
intent match
mixed intent handling
empathy score
clarity score
helpfulness score
question overload score
repetition rate
repair success rate
off-scope handling correctness
```

### Context Metrics

```text
session summary accuracy
context carryover accuracy
contradiction handling
coping strategy repetition rate
risk state persistence
privacy-aware memory compliance
```

---

## 36. Test Dataset Requirements

The evaluation dataset should include at least the following categories:

```text
normal psychoeducation questions
emotional support messages
coping strategy requests
symptom exploration messages
ambiguous messages
mixed intent messages
repair requests
explicit crisis messages
subtle distress messages
cumulative subtle risk conversations
medication-related messages
abuse or immediate danger messages
hallucination traps
low-retrieval / no-retrieval cases
off-scope messages
cultural sensitivity cases
over-reassurance traps
dependency-inducing scenarios
```

Each test case should include:

```json
{
  "user_message": "",
  "conversation_context": [],
  "expected_primary_intent": "",
  "expected_secondary_intents": [],
  "expected_risk_level": "",
  "expected_response_mode": "",
  "must_include": [],
  "must_not_include": []
}
```

---

## 37. Final System Claim

### English

```text
This project proposes a safety-aware, context-aware, evidence-grounded psychoeducation response system for psychological information support. The system does not provide diagnosis, therapy, or medication advice. It analyzes conversational context, mixed user intent, explicit and subtle risk signals, retrieved evidence, source quality, and confidence levels to generate safe, useful, and supportive responses. The architecture includes context management, privacy-aware memory, safety triage, subtle distress monitoring, intent detection, RAG-based evidence retrieval, response planning, answer generation, quality validation, safety validation, dependency prevention, fallback handling, and memory updates.
```

### Turkish

```text
Bu proje, psikolojik bilgilendirme amacıyla tasarlanmış güvenlik odaklı, bağlama duyarlı ve kaynak temelli bir cevap sistemi önerir. Sistem tanı koymaz, terapi yapmaz ve ilaç önermez. Kullanıcının konuşma bağlamını, karma niyetlerini, açık ve dolaylı risk sinyallerini, RAG ile getirilen kaynakları, kaynak kalitesini ve güven skorlarını analiz ederek güvenli, faydalı ve destekleyici cevaplar üretir. Mimari; bağlam yönetimi, gizlilik duyarlı memory, güvenlik taraması, ince distress takibi, niyet tespiti, RAG tabanlı kaynak getirme, cevap planlama, cevap üretimi, kalite doğrulama, güvenlik doğrulama, bağımlılık önleme, fallback yönetimi ve memory update katmanlarından oluşur.
```

---

## 38. Final Rule

The most important response rule:

```text
The answer must be helpful enough even if the user does not answer another question.
```

Turkish:

```text
Cevap, kullanıcı yeni bir soruya cevap vermese bile yeterince yardımcı olmalıdır.
```

This prevents the system from becoming a chatbot that only asks questions. The system should help first, then ask at most one useful question when needed.
