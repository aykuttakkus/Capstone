# Project Overview

## Project Title
**Psychology-Oriented Mental Health RAG Assistant**

---

## 1. Introduction

The **Psychology-Oriented Mental Health RAG Assistant** is a domain-specific AI application designed to provide **safe, structured, and evidence-grounded psychoeducational support** in the mental health domain. The system is built on a **Retrieval-Augmented Generation (RAG)** architecture, meaning it retrieves relevant information from trusted mental health resources before generating a response. This approach reduces unsupported generation and helps ensure that answers remain transparent, bounded, and grounded in reliable sources.

The project is designed as an **educational and guidance-oriented assistant**, not as a therapist, doctor, diagnostic tool, or treatment system. Its purpose is to help users better understand mental health topics such as stress, anxiety, low mood, burnout, sleep-related difficulties, and emotional overwhelm through reliable information and structured interaction.

This project goes beyond a simple chatbot. It combines:
- trusted-source retrieval
- safety-aware interaction
- intake-guided conversation
- structured psychoeducation flows
- refusal mechanisms for unsafe requests
- crisis-sensitive routing
- citation-based answer generation

As a result, the application is positioned as a **safe psychoeducational platform built on top of a RAG system**, rather than a generic conversational AI tool.

---

## 2. Problem Statement

Access to clear and reliable mental health information remains difficult for many users. Existing systems often fall into one of two categories:

1. **Static information platforms**  
   These provide pre-written articles or FAQ-style content, but they are often inflexible and do not adapt well to user-specific questions.

2. **Generic AI chatbots**  
   These feel more natural and conversational, but they may generate unsupported, misleading, overly confident, or unsafe answers, especially in high-sensitivity domains such as mental health.

This creates an important gap. Users may want:
- a more flexible system than a static website
- a safer and more transparent system than a general chatbot
- a first-step support tool that helps them understand what they are experiencing
- information that is grounded in trusted mental health sources
- clear boundaries around what the system can and cannot do

Mental health is a domain where trust, transparency, and safety matter more than conversational creativity. A system in this area should not improvise freely, blur clinical boundaries, or behave as if it can replace human professionals. Therefore, the core challenge of this project is to design an assistant that is **helpful, flexible, grounded, and safe at the same time**.

---

## 3. Project Goal

The main goal of this project is to develop a **safe, evidence-grounded mental health psychoeducation assistant** that helps users better understand emotional difficulties and mental health topics while maintaining strict safety boundaries.

The assistant is intended to:
- retrieve relevant information from curated mental health sources
- generate grounded answers using retrieved evidence
- provide transparent and understandable source references
- avoid unsupported answers when evidence is weak
- refuse unsafe requests such as diagnosis or medication advice
- detect crisis-related or self-harm-related language
- guide the user through structured and topic-aware interaction flows
- offer a calmer and more reliable experience than unrestricted AI chatbots

The final system should feel like a **guided, source-grounded, safety-aware information assistant**, not like an unrestricted therapist-like chatbot.

---

## 4. Core Positioning

This project should be positioned as:

**A psychology-oriented, safety-aware, source-grounded RAG assistant for psychoeducational mental health support.**

It is **not**:
- a therapist
- a psychiatrist
- a diagnostic engine
- a treatment recommendation system
- a medical device
- a suicide prediction tool

It **is**:
- an educational assistant
- a trusted mental health information interface
- a guided first-step support tool
- a safety-bounded conversational application
- a structured RAG-based psychoeducation system

This positioning is one of the most important aspects of the project. The strength of the application does not come from pretending to be a clinician. It comes from being **clear, responsible, explainable, and bounded**.

---

## 5. Scope

### In Scope
The project includes:
- psychoeducational question answering in the mental health domain
- trusted-source retrieval from curated documents
- structured onboarding and intake
- topic-guided interaction flows
- evidence-based response generation
- citation or source transparency
- insufficient evidence handling
- refusal behavior for diagnosis and medication requests
- self-harm and crisis-sensitive routing
- frontend-based interaction through an MVP application

### Out of Scope
The project does not include:
- diagnosing any mental health condition
- confirming whether a user has a disorder
- prescribing medication
- recommending treatment plans
- replacing therapy or psychiatry
- acting as an emergency response service
- delivering clinical judgment
- functioning as a clinically approved healthcare product

The system is intentionally limited in order to remain safe, realistic, and ethically responsible.

---

## 6. Proposed Solution

The proposed solution is a **mental health RAG assistant with guided interaction and safety-aware routing**.

At a high level, the application works in the following way:

1. the user enters the application
2. the system presents a short onboarding or intake process
3. the user’s purpose, emotional theme, and preferred help type are identified
4. the safety layer checks for crisis or unsafe request patterns
5. the system selects the most appropriate conversation route
6. a retrieval query is built using the user’s message and session context
7. relevant document chunks are retrieved from a curated knowledge base
8. an evidence gate checks whether the support is strong enough
9. the language model generates a response grounded in the retrieved evidence
10. the output is checked again for safety
11. the final answer is returned in a structured format with source transparency

This design keeps RAG at the center of the project, while extending it with:
- intake-aware context
- guided flows
- risk clarification
- safety routing
- structured session behavior

So the project is not moving away from RAG. It is **expanding RAG into a more mature application layer**.

---

## 7. Why RAG Is the Core of the System

RAG is the central technical foundation of this project because mental health is a high-sensitivity domain where trustworthiness matters more than open-ended fluency.

A purely generative chatbot may:
- invent facts
- overstate certainty
- generate unsupported advice
- blur the line between information and diagnosis
- provide answers without making their origin visible

RAG improves this by:
- retrieving relevant information before generation
- grounding the answer in trusted source material
- making source-based answering possible
- enabling transparent citations or references
- reducing hallucination risk
- allowing the system to abstain when evidence is insufficient

For this project, RAG is essential because it supports the assistant’s most important qualities:
- reliability
- transparency
- controllability
- safer response behavior

The final system can be understood as:

**RAG + Intake + Routing + Safety + Guided Psychoeducation**

---

## 8. Knowledge Base Strategy

The application is built on a **curated knowledge base of trusted mental health resources**. The goal is not to search the entire internet, but to work with a controlled and auditable corpus.

The knowledge base should include reliable public materials related to topics such as:
- stress
- anxiety
- depression
- burnout
- sleep and mental health
- OCD
- PTSD
- psychosis
- eating disorders
- emotional wellbeing
- help-seeking behavior

The reason for this curated approach is simple:
- unrestricted web information is inconsistent in quality
- mental health information requires careful source selection
- users need responses that are easier to trust and verify
- bounded retrieval helps preserve system safety

This knowledge base should be treated as the **authoritative information layer** of the assistant.

---

## 9. Safety Philosophy

Safety is one of the defining pillars of the project.

The assistant should not treat every user message as a normal information request. In mental health contexts, some inputs require a different response strategy. For this reason, safety should be built into the system both **before** and **after** answer generation.

The assistant must be able to recognize and respond appropriately to:
- diagnosis-seeking prompts
- medication or treatment-seeking prompts
- crisis-related language
- self-harm-related statements
- highly distressed or ambiguous emotional language
- attempts to override system boundaries

The project should follow a clear principle:

**The assistant must remain helpful without crossing clinical, medical, or ethical boundaries.**

This means:
- no diagnosis
- no medication advice
- no treatment plans
- no minimizing self-harm language
- no pretending to act as a professional clinician

Instead, the assistant should:
- clarify
- guide
- explain
- redirect
- refuse when necessary
- escalate to crisis-oriented language when appropriate

---

## 10. Intake-Guided Interaction Design

A key advancement in this project is the addition of an **intake-guided interaction layer**.

Instead of directly answering the first user message in a flat chatbot style, the system first tries to understand:
- why the user is here
- what emotional theme is most relevant
- how long the issue has been present
- how much it affects daily functioning
- what kind of help the user wants
- whether there is any safety concern

This intake layer is not diagnostic. It does not try to label or evaluate the user clinically. Its purpose is to make the interaction:
- more relevant
- more structured
- safer
- more personalized
- more useful for retrieval

This allows the system to route the user into guided psychoeducation flows such as:
- stress and anxiety
- low mood
- burnout and fatigue
- sleep-related struggles
- social or relationship pressure
- help-seeking guidance

As a result, the assistant becomes more than a reactive chatbot. It becomes a **guided psychoeducational system**.

---

## 11. Crisis and Risk Clarification Logic

One of the most sensitive responsibilities of the application is how it handles self-harm-related or suicide-related language.

The assistant should never:
- ignore such language
- dismiss it as unimportant
- continue with normal psychoeducation without checking
- generate casual or careless responses

At the same time, the system should not pretend to perform deep clinical evaluation. Instead, it should follow a **risk clarification approach**.

This means:
1. detect serious or ambiguous distress language
2. pause normal psychoeducation flow
3. ask short, direct clarification questions when appropriate
4. determine whether the situation reflects:
   - emotional distress
   - elevated concern
   - immediate crisis
5. route the user to the correct mode

The system should support at least three safety levels:

### Level 1 – Distress / unclear risk
The user sounds overwhelmed, hopeless, or emotionally unsafe, but the intent is not yet clear.

### Level 2 – Elevated concern
The user expresses possible self-harm intention or stronger warning signs.

### Level 3 – Immediate crisis
The user appears to be in urgent danger or communicates immediate intent.

The purpose of this logic is not to give the user a risk score. The purpose is to ensure that the application reacts responsibly and safely.

---

## 12. Main Functional Components

The application is expected to include the following major components:

### IntakeManager
Handles onboarding questions and creates a structured session profile.

### IntentClassifier
Determines what kind of help the user is requesting, such as psychoeducation, diagnosis-seeking, coping information, medication-seeking, crisis-related support, or off-domain requests.

### RiskRouter
Detects crisis-related and self-harm-related language and routes the user into the correct safety path.

### FlowSelector
Chooses the most appropriate psychoeducation flow based on the user’s main issue and intake context.

### RetrievalOrchestrator
Builds the final retrieval query using user input, topic context, and session state.

### EvidenceGate
Checks whether retrieved evidence is strong enough to support an answer. If not, the system returns an insufficient evidence response instead of improvising.

### PromptBuilder
Constructs a prompt that combines:
- system rules
- user context
- flow context
- retrieved evidence
- response structure rules

### SafetyPolicyEngine
Applies pre-check and post-check safety rules around diagnosis, medication, crisis language, and unsafe content.

### ResponseFormatter
Returns the final answer in a readable and structured way.

### SessionSummaryBuilder
Creates a short session summary after the interaction.

---

## 13. Expected User Experience

The application should feel:
- calm
- clear
- bounded
- supportive
- trustworthy
- structured

A typical user experience may look like this:

1. the user opens the app
2. the app shows a short disclaimer and purpose statement
3. the user answers a few onboarding questions
4. the system identifies the main emotional topic
5. the system asks one or two focused follow-up questions if needed
6. the RAG system retrieves source-grounded information
7. the assistant provides a structured answer
8. the user sees what the assistant can explain and what it cannot do
9. the session ends with a short summary or safe next step

This creates a more responsible and user-friendly flow than an unrestricted chatbot experience.

---

## 14. Technical Direction

The project is intended to be implemented as a modular application with the following broad layers:

- **User Interface Layer**  
  Handles onboarding, chat interaction, flow navigation, and answer presentation.

- **Application Logic Layer**  
  Handles intake, intent detection, risk routing, flow selection, and session state.

- **RAG Layer**  
  Handles chunk retrieval, evidence filtering, prompt construction, and grounded answer generation.

- **Safety Layer**  
  Applies pre-response and post-response safety control.

- **Data Layer**  
  Stores the curated document corpus, embeddings, metadata, and retrieval structures.

This layered design keeps the application clean, scalable, and understandable.

---

## 15. Evaluation Perspective

A strong capstone project should not only build a working application, but also evaluate it in a structured way.

This project should therefore be assessed across multiple dimensions, including:
- retrieval relevance
- groundedness of answers
- source transparency
- insufficient evidence behavior
- refusal correctness
- crisis detection behavior
- flow appropriateness
- session quality

The goal is to show that the system is not only functional, but also:
- safer than a generic chatbot
- more transparent than a basic conversational model
- more structured than a flat question-answer bot

This evaluation perspective is essential for making the project academically strong and globally competitive.

---

## 16. Project Value

This project creates value at several levels.

### Educational Value
It helps users access mental health information in a simpler, more understandable, and more guided way.

### Technical Value
It demonstrates how RAG can be used responsibly in a high-sensitivity domain.

### Safety Value
It shows how AI systems can be constrained to avoid diagnosis claims, medication advice, and careless handling of self-harm-related language.

### Product Value
It transforms a basic chatbot into a more complete application with onboarding, guided flows, and session-aware interaction.

### Research Value
It provides a strong capstone case study in trustworthy AI design for mental health psychoeducation.

---

## 17. Current Limitations

The project should openly acknowledge its limitations.

These include:
- the system is only as strong as its source coverage
- it does not replace professional mental health care
- it cannot diagnose or treat
- it may not cover every mental health topic equally well
- it remains an application-level assistant, not a clinically validated healthcare product
- response quality depends on retrieval quality and source quality
- the assistant is bounded intentionally, which means it may refuse or abstain more often than a general chatbot

These limitations are not weaknesses to hide. They are part of the project’s responsible design.

---

## 18. Final Summary

The **Psychology-Oriented Mental Health RAG Assistant** is a domain-specific, safety-aware, psychoeducational AI application built around a trusted-source RAG architecture. It is designed to help users better understand mental health topics through grounded retrieval, structured interaction, and clear safety boundaries. The system does not attempt to diagnose, prescribe, or replace professional care. Instead, it provides a safer, more transparent, and more guided alternative to unrestricted AI chatbots by combining retrieval, intake, routing, flow-based interaction, and safety-aware response generation in a single platform.
