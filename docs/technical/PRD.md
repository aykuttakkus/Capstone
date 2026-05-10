# PRD

## Product Requirements Document

### Product Name
**Psychology-Oriented Mental Health RAG Assistant**

---

## 1. Product Summary

The **Psychology-Oriented Mental Health RAG Assistant** is a safety-aware, psychoeducational AI application designed to help users better understand mental health topics through **trusted-source retrieval**, **structured guidance**, and **bounded conversational support**.

The product is built around a **Retrieval-Augmented Generation (RAG)** architecture. Instead of generating responses freely from model memory, the system first retrieves relevant information from a curated mental health knowledge base and then generates responses grounded in that evidence.

The application is not designed to diagnose, prescribe, or replace professional mental health care. Its purpose is to provide:
- clear psychoeducational information
- safer first-step support
- guided interaction
- transparent source-based answering
- controlled behavior in high-sensitivity situations

The assistant should feel like a **guided mental health information system**, not like an unrestricted chatbot or therapist simulation.

---

## 2. Product Vision

To create a **trustworthy, structured, and safe mental health psychoeducation assistant** that helps users understand emotional difficulties through reliable information, guided interaction, and clear safety boundaries.

The product should bridge the gap between:
- static information websites that are not interactive enough
- generic AI chatbots that are not grounded or safe enough

The vision is to build a system that is:
- easier to trust
- more transparent
- more structured
- more bounded
- more suitable for mental health psychoeducation

---

## 3. Product Goals

The product should achieve the following goals:

1. **Provide trusted-source psychoeducation**
   - retrieve reliable information from curated mental health documents
   - generate source-grounded answers

2. **Improve safety in mental health AI interaction**
   - refuse unsafe diagnosis and medication requests
   - detect distress and crisis-related language
   - route users safely when needed

3. **Guide users more effectively than a flat chatbot**
   - use onboarding and intake
   - identify user intent
   - route users into topic-specific guidance flows

4. **Increase answer transparency**
   - show source references
   - avoid unsupported claims
   - return insufficient evidence when needed

5. **Create a structured and usable MVP application**
   - clean interface
   - session-aware interaction
   - summary-based conversation flow

---

## 4. Non-Goals

The product is not intended to:
- diagnose any mental health condition
- determine whether the user has a disorder
- prescribe medication
- suggest treatment plans
- replace therapy or psychiatry
- function as a crisis intervention service
- act as a clinical decision support system
- provide emergency medical advice

These boundaries are central to the product design and must remain visible throughout the user experience.

---

## 5. Target Users

### Primary Users
Users who:
- want to understand stress, anxiety, low mood, burnout, sleep difficulties, or emotional pressure
- want psychoeducational information in a more interactive format
- prefer a structured first-step support experience
- want reliable sources instead of unsupported chatbot answers

### Secondary Users
Users who:
- want to understand when professional support may be useful
- want a guided mental health information experience
- want a calmer and safer alternative to general AI chatbots

### Excluded Use Cases
The product is not intended for:
- users seeking diagnosis confirmation
- users seeking medication recommendations
- users expecting therapy sessions
- users in immediate crisis who need emergency intervention instead of an informational tool

---

## 6. Core User Problems

The product is designed to solve the following user problems:

### Problem 1
Users often do not know where to begin when trying to understand what they are feeling.

### Problem 2
Mental health websites provide useful information, but they are often static and difficult to navigate based on personal context.

### Problem 3
Generic chatbots may sound confident but can provide unsupported or unsafe responses.

### Problem 4
Users may ask emotionally loaded or risky questions that require more careful handling than a normal information request.

### Problem 5
Users often want a structured path:
- what is happening
- what this may generally mean
- what kind of information is relevant
- when support might be worth considering

---

## 7. Product Principles

The product should follow these principles:

### 7.1 Safety Before Fluency
The system should prioritize safe and bounded behavior over conversational smoothness.

### 7.2 Grounded Before Generative
The assistant should rely on trusted-source retrieval before generating answers.

### 7.3 Guidance Before Overload
The product should guide the user step by step instead of presenting large, unstructured responses.

### 7.4 Supportive Without Pretending to Be Clinical
The tone should be calm and supportive, but the assistant must not imitate therapy or clinical authority.

### 7.5 Structured Interaction Over Random Chat
The application should use flows, routing, and summaries to create a more useful experience.

### 7.6 Transparency Over False Confidence
The system should indicate source-backed information clearly and abstain when evidence is weak.

---

## 8. User Journey Overview

A typical user journey should look like this:

1. user opens the application
2. user sees a short disclaimer and system boundaries
3. user completes a short onboarding or intake
4. system identifies the user’s topic and intended help type
5. system checks for unsafe or crisis-related content
6. system selects the appropriate guided flow
7. system retrieves trusted source material
8. system provides a structured answer
9. user can continue within the same flow or choose another topic
10. system ends with a short summary or safe next-step suggestion

---

## 9. Main Features

## 9.1 Welcome and Boundary Screen
A short opening screen that clearly states:
- the assistant provides psychoeducational information
- it does not diagnose
- it does not prescribe medication
- it does not replace professional support
- crisis-related situations require more urgent support

### Purpose
To set user expectations and reduce misuse.

---

## 9.2 Intake and Onboarding
A short guided intake that helps the system understand:
- why the user is here
- which emotional topic is most relevant
- how long the issue has been present
- how much it affects daily life
- what kind of help the user wants

### Example goals of intake
- identify main theme
- improve relevance
- improve safety
- improve flow selection
- improve retrieval context

### Requirements
- should be short and low-friction
- should not feel like a diagnostic form
- should support skipping some optional questions
- should store answers in session state

---

## 9.3 Intent Classification
The system should classify the user’s request into high-level categories such as:
- psychoeducation
- coping information
- help-seeking guidance
- diagnosis-seeking
- medication-seeking
- crisis-related
- off-domain

### Purpose
To determine the correct behavioral mode of the assistant.

---

## 9.4 Guided Psychoeducation Flows
The system should support structured topic flows rather than only generic free chat.

### Initial flow groups
- Stress / Anxiety
- Low Mood
- Burnout / Fatigue / Sleep
- Social / Relationship Pressure
- Help-Seeking Guidance

### Flow behavior
Each flow may include:
- one or more short follow-up questions
- topic-aware retrieval
- structured answers
- optional continuation within the same theme

### Purpose
To make the conversation feel more useful and less random.

---

## 9.5 RAG-Based Source Retrieval
The application must retrieve relevant chunks from a curated mental health knowledge base before generating answers.

### Requirements
- use curated trusted documents
- generate context-grounded responses
- support source references
- support insufficient evidence behavior
- avoid unsupported free generation

### Purpose
To improve trustworthiness and reduce hallucination risk.

---

## 9.6 Evidence Gate
The system should check whether retrieved evidence is strong enough before answering.

### If evidence is strong enough
Proceed with grounded answer generation.

### If evidence is weak
Return a bounded response such as:
- insufficient evidence
- topic not sufficiently covered
- suggest a related supported topic if appropriate

### Purpose
To prevent low-confidence hallucinated answers.

---

## 9.7 Structured Response Format
The assistant should not return only one large block of text.

### Recommended answer structure
- short summary of what the user shared
- psychoeducational explanation
- source-grounded information
- helpful next step
- when professional support may be worth considering
- source references

### Purpose
To make answers easier to read and more trustworthy.

---

## 9.8 Diagnosis Refusal Mode
If the user asks:
- “Do I have depression?”
- “Am I bipolar?”
- “Can you diagnose me?”
- similar diagnosis-seeking prompts

The system must:
- refuse to diagnose
- explain its boundary
- redirect toward general educational information
- optionally explain when professional support may be worth considering

### Purpose
To prevent unsafe clinical overreach.

---

## 9.9 Medication Refusal Mode
If the user asks:
- “Should I take antidepressants?”
- “What medication should I use?”
- “Would this drug help me?”

The system must:
- refuse medication guidance
- explain its limitation
- avoid any dosage or treatment suggestion
- redirect toward professional support

### Purpose
To avoid unsafe medical advice.

---

## 9.10 Distress and Crisis Routing
The system should distinguish between:
- emotional distress
- elevated concern
- immediate crisis

### If the user expresses ambiguous distress
Pause normal psychoeducation and ask brief clarification questions.

### If the user expresses stronger self-harm concern
Enter safety-oriented routing mode.

### If the user appears to be in immediate danger
Stop normal conversation and move to crisis-oriented language.

### Purpose
To avoid careless handling of serious emotional language.

---

## 9.11 Risk Clarification
If the user says something like:
- “I don’t want to live”
- “I might hurt myself”
- “I’m not safe”

the assistant should not immediately continue with normal information delivery.

### The system should:
- ask short direct safety clarification questions
- identify whether the issue is distress, elevated concern, or immediate danger
- route the user accordingly

### Requirements
- keep questions short
- avoid acting like a clinician
- prioritize safety over conversational continuity

---

## 9.12 Session Summary
At the end of a session, the system should provide a short structured summary.

### Summary content
- main topic discussed
- what the assistant explained
- safe next-step suggestion
- reminder of system boundaries if relevant

### Purpose
To improve clarity and make the interaction feel complete.

---

## 10. Functional Requirements

## 10.1 Onboarding
- The system must show a short product disclaimer before use.
- The system must support a short onboarding flow.
- The system must store onboarding answers in session state.
- The onboarding should include at least:
  - purpose of visit
  - main issue
  - duration
  - level of daily impact
  - preferred help type
- Optional questions may include:
  - prior professional support
  - current support availability

## 10.2 Classification and Routing
- The system must classify user intent.
- The system must select an appropriate interaction flow.
- The system must support special routing for diagnosis, medication, distress, and crisis language.

## 10.3 Retrieval and Generation
- The system must use RAG-based retrieval before answering domain questions.
- The system must generate answers from retrieved evidence.
- The system must support insufficient evidence handling.
- The system must support source display or references.

## 10.4 Safety
- The system must block diagnosis outputs.
- The system must block medication advice outputs.
- The system must detect self-harm-related statements.
- The system must support crisis escalation language.
- The system must not continue normal psychoeducation in immediate crisis mode.

## 10.5 Output Format
- The system must use a structured response layout.
- The system must return readable, non-clinical, bounded answers.
- The system must support a session summary at the end of the interaction.

---

## 11. Non-Functional Requirements

### 11.1 Clarity
The product should use simple, understandable, and calm language.

### 11.2 Safety
The product should prioritize safe behavior over complete answer coverage.

### 11.3 Transparency
The system should make source-grounded reasoning visible where possible.

### 11.4 Modularity
The system should be designed with separate modules for:
- intake
- routing
- retrieval
- safety
- formatting

### 11.5 Scalability
The MVP should be simple, but the architecture should allow future upgrades such as:
- multilingual support
- reranking
- evaluation dashboards
- richer benchmarks

### 11.6 Responsiveness
The app should respond quickly enough to maintain a smooth user experience.

---

## 12. Initial Screens

The first version of the product should include these main screens:

### 12.1 Welcome Screen
Contains:
- product purpose
- system boundary statement
- start button

### 12.2 Intake Screen
Contains:
- onboarding questions
- progress indicator
- continue button

### 12.3 Main Chat Screen
Contains:
- conversation view
- structured answer display
- follow-up flow questions
- input area

### 12.4 Sources Panel
Contains:
- source references
- retrieved document visibility if available
- source transparency section

### 12.5 Crisis Support State
A special interaction state for crisis-related routing.

### 12.6 Session Summary Screen
Contains:
- short recap
- safe next step
- option to restart or continue

---

## 13. MVP Scope

The MVP should include:

- welcome/disclaimer screen
- onboarding flow
- 4 to 5 guided topic flows
- intent classification
- risk routing
- RAG-based answering
- evidence gate
- diagnosis refusal
- medication refusal
- structured output format
- session summary

The MVP does not need to include:
- advanced analytics dashboards
- multi-user support
- production deployment infrastructure
- clinician review tools
- mobile app version
- multilingual expansion in the first release

---

## 14. Success Metrics

The product should be judged successful if it can demonstrate:

### Product Success
- users can complete onboarding easily
- users can reach the right topic flow
- answers feel more structured than a basic chatbot
- the interaction feels guided and understandable

### Technical Success
- retrieval returns relevant source material
- the evidence gate prevents weak unsupported answers
- outputs remain grounded in retrieved content

### Safety Success
- diagnosis requests are refused correctly
- medication requests are refused correctly
- self-harm-related language triggers the correct safety mode
- immediate crisis situations do not continue in normal information mode

### Capstone Success
- the product clearly demonstrates RAG in a high-sensitivity domain
- the system shows boundaries, explainability, and evaluation thinking
- the project feels like a serious application, not only a simple demo chatbot

---

## 15. Future Enhancements

Potential future directions include:
- bilingual support
- improved retrieval strategies
- hybrid search
- reranking
- explainability improvements
- safety benchmark suite
- richer session memory
- clinician-informed flow refinements
- reflective tracking features
- more advanced evaluation dashboards

These are future opportunities, not requirements for the first version.

---

## 16. Final Product Definition

The final product should be defined as:

**A psychology-oriented, safety-aware, source-grounded mental health RAG assistant that provides guided psychoeducation, structured interaction, and bounded support without crossing into diagnosis, treatment, or clinical decision-making.**
