# Calma Psychology RAG System Test Analysis Report

## 1. Report Purpose

This report analyzes a test conversation conducted with the **Calma Psychology RAG System**. The purpose of the analysis is to identify the strengths, weaknesses, missing components, and improvement areas of the system based on the quality of its responses, emotional continuity, RAG source usage, and user guidance behavior.

The tested scenario focuses on a user who reports feeling lonely despite being around people and later reveals anxiety about not having a romantic relationship and possibly never getting married. This makes the test particularly useful for evaluating the system’s ability to handle emotional disclosure, relationship-related anxiety, clarification requests, and psychoeducational support.

---

## 2. Test Conversation Summary

### 2.1 User’s Main Emotional Theme

The user’s core concern develops gradually throughout the conversation:

- The user feels lonely even when surrounded by people.
- The user knows many people but still feels emotionally alone.
- The user does not know how to build meaningful relationships.
- The user explicitly says they came to the system to talk and learn.
- The user reveals a deeper concern: they have not had a girlfriend for a long time.
- The user expected to be married around this age.
- The user fears that if they cannot find someone soon, they may never get married.

### 2.2 Core Psychological Themes

The conversation contains the following psychological themes:

- Loneliness
- Lack of emotional connection
- Relationship anxiety
- Fear of future uncertainty
- Negative comparison with past expectations
- Possible self-worth concerns
- Need for guidance rather than only questioning
- Need for emotional validation and practical psychoeducation

The system partially recognizes the user’s loneliness and anxiety, but it does not consistently maintain the emotional context across the conversation.

---

## 3. General Evaluation

Overall, Calma demonstrates some useful baseline qualities, especially in emotional validation and avoiding direct diagnosis. However, the system shows important weaknesses in context tracking, source relevance, clarification handling, and practical guidance.

The most important issue is that Calma often responds in a generic way instead of deeply following the user’s actual emotional narrative. When the user asks for clarification or says they do not know what to do, the system continues asking broad questions rather than providing simple explanations, concrete guidance, or small actionable steps.

In a psychology-oriented RAG system, the assistant should not only retrieve related content. It should also understand the user’s emotional context, explain concepts in a simple way, and guide the user safely through psychoeducational reflection.

---

## 4. Strengths Observed in the System

### 4.1 Empathetic Opening

Calma usually begins with an emotionally validating sentence, such as:

> “I understand how that can feel isolating.”

This is a positive behavior because it helps the user feel heard and acknowledged. Emotional validation is important in a mental health support context because users often need to feel understood before they can reflect on their thoughts or behaviors.

### 4.2 Avoidance of Direct Diagnosis

The system does not directly diagnose the user with a disorder such as depression, social anxiety disorder, or attachment issues. This is appropriate for a psychoeducational RAG system.

The system should continue avoiding statements such as:

- “You have depression.”
- “You have social anxiety.”
- “This means you have attachment trauma.”

Instead, it should use safer language such as:

- “This may be related to...”
- “Some people experience this when...”
- “One possible explanation is...”

### 4.3 Use of Open-Ended Questions

Calma asks open-ended questions to keep the conversation going. For example:

> “How might you start building more meaningful relationships?”

Open-ended questions can be helpful, especially when encouraging reflection. However, in this test, the system overuses questions and does not always provide enough explanation before asking them.

---

## 5. Main Problems Identified

## 5.1 Problem 1: Weak Handling of “I Don’t Know” Responses

### Observed Issue

When the user says:

> “I don't know, I am coming for learn for you”

The user is clearly expressing that they need guidance. However, Calma responds with another broad question instead of providing a clear explanation or direction.

### Why This Is a Problem

When a user says they do not know what to do, the system should not immediately return the responsibility back to the user. In this case, the user is asking the assistant to help them understand their experience.

A better approach would be:

1. Validate the uncertainty.
2. Explain the concept simply.
3. Offer a small first step.
4. Ask one gentle follow-up question only after providing guidance.

### Recommended Rule

```text
If the user says “I don’t know”, “I came here to learn”, “I don’t understand”, or similar phrases, the system should first provide a simple explanation and one practical micro-step before asking another question.
```

### Improved Example

```text
That makes sense. You do not have to know the answer right now. We can explore it step by step. Feeling lonely around people can sometimes mean that you have social contact, but not enough emotional closeness. A small first step could be noticing one person around whom you feel even slightly safe or comfortable.
```

---

## 5.2 Problem 2: Weak Context Continuity

### Observed Issue

The conversation begins with loneliness and gradually develops into fear about romantic relationships and marriage. However, Calma does not consistently connect these themes.

The user’s actual emotional story is:

```text
I feel lonely even though I know people.
I do not feel deeply connected.
I have not had a girlfriend for a long time.
I thought I would be married by now.
I am afraid I may never get married.
```

Calma responds to each message separately instead of building a coherent understanding of the user’s core concern.

### Why This Is a Problem

Psychological conversations require continuity. If the system treats each user message as isolated, it may miss the deeper concern behind the words.

In this case, the deeper concern is not only loneliness. It is also the fear that loneliness may continue permanently.

### Recommended Rule

```text
The system should maintain a short internal user concern summary during the conversation and update it after each emotional disclosure.
```

### Suggested Internal Context Summary

```text
User core concern:
- Feels lonely despite knowing many people
- Wants to understand why they feel emotionally alone
- Has not had a girlfriend for a long time
- Expected to be married around this age
- Fears they may never find a partner or get married
- Needs explanation and guidance, not only reflective questions
```

---

## 5.3 Problem 3: RAG Source Relevance Is Weak

### Observed Issue

The system retrieves sources such as:

- Social Anxiety Scotland - Page 17
- Dealing with Distress - Page 36

These sources may contain generally relevant mental health information, but the answers generated from them do not always directly match the user’s current question.

For example, when the user asks for clarification about “prioritizing yourself,” Calma responds by discussing the importance of a relationship and what the user wants to achieve in it. This does not directly answer the user’s question.

### Why This Is a Problem

A RAG system should not force a source into the answer just because it is somewhat related to the general domain. The source must be relevant to:

- The user’s latest question
- The emotional theme
- The conversation history
- The specific concept being explained

### Recommended Rule

```text
Before using a retrieved source, the system should check whether the source directly answers the user’s latest question and fits the current emotional context. If relevance is low, the system should not force the source into the answer.
```

### Recommended RAG Relevance Checklist

```text
1. Does the source directly answer the user’s latest question?
2. Does it match the main emotional topic?
3. Does it fit the conversation context?
4. Does it explain the concept the user is asking about?
5. Is the citation being used naturally rather than forced?
```

---

## 5.4 Problem 4: Too Much Abstract Language

### Observed Issue

Calma uses phrases such as:

- “Focusing on personal growth and self-care...”
- “Evaluating its significance in our lives...”
- “Future stressors...”
- “Break the cycle of repetitive overwhelming emotions...”

These phrases are not necessarily wrong, but they are too abstract for a user who is asking for emotional support and simple guidance.

### Why This Is a Problem

The user explicitly says they did not fully understand. This indicates that the system’s explanation was too vague or theoretical.

The system should translate psychological concepts into everyday language.

### Recommended Rule

```text
When the user asks for clarification, the system should explain the previous concept in simple, concrete, user-specific terms.
```

### Improved Explanation of “Prioritizing Yourself”

```text
Prioritizing yourself means not measuring your value only by whether you are in a relationship. In your situation, it could mean building a life that makes you feel more confident, stable, and connected, while also staying open to meeting someone. It does not mean ignoring relationships. It means not treating being single as proof that something is wrong with you.
```

---

## 5.5 Problem 5: Overuse of Questions

### Observed Issue

Calma repeatedly ends responses with questions:

- “Have you tried sharing how you feel with someone close to you?”
- “How might you start building more meaningful relationships?”
- “How do you feel about sharing your thoughts with someone close to you?”
- “How do you feel about trying to share one small thought or concern?”
- “How do you think you might start prioritizing yourself in this period?”
- “Does this help frame the importance of reflecting on these aspects?”
- “How might these insights apply to a current situation you're facing?”

### Why This Is a Problem

Questions are useful, but too many questions can make the system feel like it is avoiding responsibility. The user came to the system for help, explanation, and guidance. If the system only reflects and asks questions, the user may feel unsupported.

### Recommended Rule

```text
Each response should contain useful explanation or guidance before asking a follow-up question. The system should ask a maximum of one question per response.
```

### Recommended Response Structure

```text
1. Validate the user’s emotion.
2. Reflect the user’s actual concern.
3. Explain the concept simply.
4. Give one practical micro-step.
5. Ask one relevant follow-up question only if needed.
```

---

## 5.6 Problem 6: Technical RAG Language Appears in User-Facing Response

### Observed Issue

Calma says:

> “I can give you a general answer, but the source-backed detail is limited.”

### Why This Is a Problem

This sounds technical and breaks the emotional flow of the conversation. The user does not need to hear internal RAG limitations in this form. It makes the assistant feel less natural and less supportive.

### Recommended Rule

```text
The system should not expose technical retrieval limitations directly to the user unless necessary. If source confidence is low, the system should provide a safe general psychoeducational answer without mentioning retrieval failure in a technical way.
```

### Better Alternative

```text
I can explain this in a general psychoeducational way.
```

or

```text
We can look at this gently and step by step.
```

---

## 5.7 Problem 7: User’s Request to Talk to the Assistant Is Missed

### Observed Issue

The user says:

> “I am coming here for talk to you”

This means the user wants to talk to Calma directly before speaking with another person. However, Calma continues suggesting that the user share thoughts with someone close to them.

### Why This Is a Problem

The assistant should recognize that the user is asking for a safe conversational space. Encouraging external support can be useful, but it should not replace the current conversation when the user explicitly wants to talk here.

### Recommended Rule

```text
If the user says they came here to talk, the system should acknowledge that and continue the conversation safely within the chat before suggesting external sharing.
```

### Improved Example

```text
I am here with you. We can talk about it here first. You do not have to share it with someone else before you feel ready.
```

---

## 6. Missing System Components

## 6.1 Conversation Memory / Context Tracker

The system needs a short-term conversation memory that tracks the user’s main emotional concern.

### Suggested Component

```text
Conversation Context Tracker
- Stores the user’s current emotional theme
- Stores repeated fears or concerns
- Stores the user’s stated needs
- Updates after each message
- Guides response generation
```

### Example Stored Context

```text
Current theme: loneliness and fear of not finding a romantic partner
User need: wants explanation and guidance
User emotional state: anxious, uncertain, afraid of future loneliness
Important detail: user expected to be married around this age
```

---

## 6.2 Intent Detection Layer

The system should classify the user’s message intent before generating a response.

### Suggested Intent Categories

```text
- emotional_disclosure
- clarification_request
- guidance_request
- self_application_request
- crisis_or_safety_check
- off_topic_request
```

### Intent Examples from This Test

```text
“I feel lonely even when I am around people.”
Intent: emotional_disclosure

“I don’t know, I am coming for learn from you.”
Intent: guidance_request

“Could you explain what you mean?”
Intent: clarification_request

“What can I take from this for my own situation?”
Intent: self_application_request
```

---

## 6.3 RAG Relevance Validator

The system needs a relevance validation layer before using retrieved chunks.

### Suggested Validation Criteria

```text
- Topic match
- Emotional context match
- User intent match
- Direct answer match
- Citation usefulness
```

If a source does not pass the relevance threshold, it should not be used as the main foundation of the answer.

---

## 6.4 Response Planner

The system needs a structured response planner to prevent generic or disconnected answers.

### Recommended Response Planner

```text
For each user message:
1. Identify the user’s emotion.
2. Identify the user’s actual need.
3. Retrieve relevant sources if needed.
4. Validate source relevance.
5. Generate a response using:
   - validation
   - context reflection
   - simple psychoeducation
   - one practical step
   - one optional follow-up question
```

---

## 6.5 Clarification Handler

When the user says they do not understand, the system should not introduce a new topic. It should explain the previous answer more simply.

### Suggested Rule

```text
If the user asks for clarification, explain the exact concept from the previous assistant response using simpler language and examples from the user’s own situation.
```

---

## 6.6 Micro-Step Generator

The system should provide small, realistic, non-overwhelming actions.

### Example Micro-Steps for This Test

```text
- Write down the difference between the fact and the fear.
- Identify one person you feel slightly comfortable with.
- Practice one honest sentence about how you feel.
- Avoid treating every new interaction as a test for marriage.
- Build one weekly activity that increases confidence or social connection.
- Use compassionate self-talk when the fear of “I will never marry” appears.
```

---

## 7. Recommended Improvements for Calma

## 7.1 Improve Context-Aware Responses

Calma should connect the user’s messages across the conversation. For example, when the user reveals fear about not getting married, the system should connect it to the earlier loneliness theme.

### Better Direction

```text
It sounds like your loneliness is not only about being physically alone. It may also be connected to a deeper fear that you will not find the kind of relationship and future you hoped for.
```

---

## 7.2 Use Simpler and Warmer Language

The system should avoid overly academic expressions and use more natural language.

### Avoid

```text
This awareness helps break the cycle of repetitive overwhelming emotions.
```

### Prefer

```text
Noticing this pattern can help you pause before the fear takes over again.
```

---

## 7.3 Answer Before Asking

When the user asks for help, the system should not immediately ask another question.

### Recommended Pattern

```text
I can explain it more clearly. In your situation, this means...
```

Then the system can ask one relevant follow-up question.

---

## 7.4 Separate Facts from Fears

For this conversation, a useful CBT-based psychoeducational technique would be separating facts from fears.

### Example

```text
Fact: I have not had a girlfriend for a long time.
Fear: I may never get married.
Balanced view: Not having a relationship right now does not prove that I will never have one.
```

This is simple, practical, and directly related to the user’s concern.

---

## 7.5 Avoid Forced Externalization

The system should not repeatedly tell the user to share with someone close if the user says they came to the assistant to talk.

### Better Response

```text
We can talk about it here first. Later, if you feel ready, you might choose one safe person to share a small part of this with.
```

---

## 8. Ideal Response Example for the Tested Scenario

### User Message

```text
I think I can share it. Actually, I haven’t had a girlfriend for a long time, and I used to think I would get married around this age. Now I’m afraid that if I still can’t find someone, maybe I’ll never get married.
```

### Ideal Calma Response

```text
That sounds really heavy to carry. It makes sense that you feel anxious if your current life does not match the timeline you once imagined for yourself. But not having a girlfriend for a long time does not mean you will never find a meaningful relationship.

A helpful first step could be separating the fact from the fear. The fact is: “I haven’t had a girlfriend for a long time.” The fear is: “I may never get married.” These two thoughts feel connected, but they are not the same.

For now, instead of trying to solve your whole future at once, we can focus on what would help you feel more connected, confident, and open to meeting people again.
```

### Why This Response Is Better

This response is stronger because it:

- Validates the user’s emotional pain.
- Does not minimize the fear.
- Does not diagnose the user.
- Connects the current fear to the user’s life expectations.
- Uses a simple CBT-style distinction between fact and fear.
- Gives a practical direction without overwhelming the user.
- Avoids forcing the user to talk to someone else immediately.

---

## 9. Implementation Recommendations

## 9.1 Add a Response Quality Checklist

Before sending each answer, the system should check:

```text
1. Did I validate the user’s emotion?
2. Did I reflect the actual concern?
3. Did I answer the user’s latest request?
4. Did I avoid diagnosis?
5. Did I avoid overusing generic advice?
6. Did I provide one useful explanation or step?
7. Did I ask no more than one question?
8. Is the retrieved source directly relevant?
```

---

## 9.2 Add a Retrieval Quality Gate

Before using retrieved content, the system should score the source relevance.

### Suggested Scoring

```text
0 = Not relevant
1 = Weakly related
2 = Generally related
3 = Directly relevant
```

Only sources scoring **3** should be used as primary evidence in the answer. Sources scoring **2** may be used cautiously, but should not dominate the response. Sources scoring **0–1** should not be cited.

---

## 9.3 Add User-State-Aware Prompt Rules

The system prompt should include rules such as:

```text
If the user expresses fear, respond with validation and grounding.
If the user asks for clarification, simplify the previous explanation.
If the user says they do not know, provide guidance before asking another question.
If the user says they came to talk to you, acknowledge the chat as a safe space.
If the user reveals a personal fear, do not redirect too quickly to another person.
```

---

## 9.4 Add Human-Like Language Rules

The system should prefer warm and simple sentences.

### Prefer

```text
That fear makes sense.
We can look at this step by step.
This does not mean something is wrong with you.
Your mind may be turning uncertainty into a worst-case scenario.
```

### Avoid

```text
Source-backed detail is limited.
Does this help frame the importance of reflecting on these aspects?
Future stressors may create repetitive overwhelming emotions.
```

---

## 10. Final Conclusion

This test shows that Calma has a useful foundation for a psychology-oriented RAG assistant. It can validate emotions, avoid diagnosis, and keep the conversation going. However, the system currently behaves too much like a generic reflective chatbot and not enough like a context-aware psychoeducational support assistant.

The most critical improvement areas are:

1. Stronger conversation context tracking
2. Better RAG source relevance validation
3. Improved handling of clarification requests
4. More practical guidance when the user says they do not know what to do
5. Warmer and simpler language
6. Reduced overuse of broad follow-up questions
7. Better recognition of the user’s need to talk within the chat

For a global-level graduation project, Calma should not only retrieve psychological resources. It should also understand the user’s emotional story, explain concepts clearly, and provide safe, small, practical steps while staying within a non-diagnostic psychoeducational role.

The target behavior should be:

```text
A safe, warm, context-aware, source-supported psychoeducational assistant that validates the user, follows the emotional narrative, explains psychological concepts simply, and offers practical micro-steps without diagnosing or overwhelming the user.
```
