"""
Hybrid Semantic Intent Detection Engine
Combines embedding-based classification with LLM validation
Following global best practices from OpenAI, Microsoft, Google
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


@dataclass
class IntentResult:
    """Intent detection result with confidence and reasoning"""
    primary_intent: str
    confidence: float
    reasoning: str
    embedding_score: float
    llm_validation: bool
    alternative_intents: List[Tuple[str, float]]
    context_aware: bool = False


class SemanticIntentEngine:
    """
    3-Layer Hybrid Intent Detection System
    
    Layer 1: Semantic Embedding Classification
    Layer 2: LLM-Based Validation  
    Layer 3: Context-Aware Refinement
    """
    
    # Intent Definitions with rich semantic descriptions
    INTENT_DEFINITIONS = {
        "emotional_support": {
            "description": "User expressing emotional distress, seeking empathy, validation, or someone to listen",
            "examples": [
                "I feel so alone and nobody understands me",
                "I'm going through a really difficult time right now",
                "Everything feels overwhelming and I can't cope",
                "I need someone to talk to about what I'm feeling",
                "It hurts so much and I don't know what to do",
            ],
            "keywords": ["feel", "lonely", "alone", "hurt", "pain", "sad", "overwhelmed", "struggling"],
        },
        "psychoeducation": {
            "description": "User seeking information, knowledge, or understanding about mental health concepts",
            "examples": [
                "What is anxiety and how does it work?",
                "Can you explain the symptoms of depression?",
                "I want to understand why I feel this way",
                "What causes panic attacks?",
                "Tell me about coping mechanisms",
            ],
            "keywords": ["what is", "how does", "explain", "understand", "causes", "symptoms", "tell me about"],
        },
        "coping_strategy": {
            "description": "User asking for practical techniques, exercises, or actionable steps",
            "examples": [
                "What can I do to feel better?",
                "Give me techniques to manage my anxiety",
                "How should I deal with panic attacks?",
                "What exercises help with stress?",
                "Tell me some grounding techniques",
            ],
            "keywords": ["what can I do", "how to", "techniques", "exercises", "manage", "deal with", "cope"],
        },
        "symptom_exploration": {
            "description": "User describing specific symptoms and seeking to understand them",
            "examples": [
                "I've been having trouble sleeping and losing appetite",
                "My heart races and I feel dizzy sometimes",
                "I can't concentrate and I feel restless",
                "Why do I feel numb and disconnected?",
                "I've noticed I'm avoiding people more",
            ],
            "keywords": ["symptoms", "trouble", "can't", "unable", "notice", "experiencing"],
        },
        "crisis": {
            "description": "User expressing suicidal ideation, self-harm, or immediate danger",
            "examples": [
                "I want to end my life",
                "I can't go on anymore",
                "I have thoughts of hurting myself",
                "There's no point in living",
                "I feel hopeless and want to die",
            ],
            "keywords": ["suicide", "kill myself", "hurt myself", "end my life", "hopeless", "no point"],
        },
        "clarification": {
            "description": "User seeking clarification or expressing confusion",
            "examples": [
                "I don't understand what you mean",
                "Can you explain that again?",
                "What did you mean by that?",
                "I'm confused about what you said",
                "Could you be more specific?",
            ],
            "keywords": ["don't understand", "confused", "explain again", "what did you mean"],
        },
    }
    
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        """
        Initialize the semantic intent engine
        
        Args:
            model_name: Sentence transformer model for embeddings
        """
        print(f"[SemanticIntentEngine] Loading embedding model: {model_name}")
        self.embedder = SentenceTransformer(model_name)
        
        # Pre-compute intent embeddings
        self.intent_embeddings = self._precompute_intent_embeddings()
        print(f"[SemanticIntentEngine] Initialized with {len(self.INTENT_DEFINITIONS)} intents")
    
    def _precompute_intent_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Pre-compute embeddings for all intent definitions and examples
        This improves performance at inference time
        """
        intent_embeddings = {}
        
        for intent_name, intent_data in self.INTENT_DEFINITIONS.items():
            # Combine description and examples
            texts = [intent_data["description"]] + intent_data["examples"]
            
            # Compute embeddings
            embeddings = self.embedder.encode(texts, convert_to_numpy=True)
            
            # Average embeddings for this intent
            intent_embeddings[intent_name] = np.mean(embeddings, axis=0)
        
        return intent_embeddings
    
    def detect(
        self, 
        message: str, 
        conversation_history: Optional[List[str]] = None,
        use_llm_validation: bool = False
    ) -> IntentResult:
        """
        Main detection method - 3 Layer System
        
        Args:
            message: User message
            conversation_history: Previous messages for context
            use_llm_validation: Whether to use LLM for validation
            
        Returns:
            IntentResult with confidence and reasoning
        """
        # Layer 1: Semantic Embedding Classification
        embedding_scores = self._layer1_embedding_classification(message)
        
        # Layer 2: LLM-Based Validation (if enabled)
        if use_llm_validation:
            llm_validation = self._layer2_llm_validation(message, embedding_scores)
        else:
            llm_validation = {"validated": True, "primary_intent": max(embedding_scores, key=embedding_scores.get)}
        
        # Layer 3: Context-Aware Refinement
        if conversation_history:
            refined_intent = self._layer3_context_refinement(
                message, embedding_scores, conversation_history
            )
        else:
            refined_intent = max(embedding_scores, key=embedding_scores.get)
        
        # Calculate final confidence
        primary_score = embedding_scores[refined_intent]
        confidence = self._calculate_confidence(primary_score, llm_validation)
        
        # Get alternative intents
        alternatives = sorted(
            [(intent, score) for intent, score in embedding_scores.items() if intent != refined_intent],
            key=lambda x: x[1],
            reverse=True
        )[:2]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(refined_intent, embedding_scores, message)
        
        return IntentResult(
            primary_intent=refined_intent,
            confidence=confidence,
            reasoning=reasoning,
            embedding_score=primary_score,
            llm_validation=llm_validation.get("validated", False),
            alternative_intents=alternatives,
            context_aware=conversation_history is not None
        )
    
    def _layer1_embedding_classification(self, message: str) -> Dict[str, float]:
        """
        Layer 1: Semantic similarity using embeddings
        
        Returns:
            Dictionary of intent -> similarity_score
        """
        # Encode user message
        message_embedding = self.embedder.encode(message, convert_to_numpy=True)
        
        # Calculate cosine similarity with each intent
        similarities = {}
        for intent_name, intent_embedding in self.intent_embeddings.items():
            similarity = cosine_similarity(
                message_embedding.reshape(1, -1),
                intent_embedding.reshape(1, -1)
            )[0][0]
            similarities[intent_name] = float(similarity)
        
        return similarities
    
    def _layer2_llm_validation(self, message: str, embedding_scores: Dict[str, float]) -> Dict:
        """
        Layer 2: LLM-based validation
        Lightweight validation using few-shot prompting
        
        Note: This is a placeholder - in production, integrate with your LLM
        """
        # Get top 2 intents from embedding
        sorted_intents = sorted(embedding_scores.items(), key=lambda x: x[1], reverse=True)
        top_intent = sorted_intents[0]
        
        # Simple rule-based validation for now
        # In production: Call GPT-3.5-turbo or local LLM
        validation_result = {
            "validated": top_intent[1] > 0.7,  # Threshold validation
            "primary_intent": top_intent[0],
            "top_score": top_intent[1],
            "needs_review": top_intent[1] < 0.6,
        }
        
        return validation_result
    
    def _layer3_context_refinement(
        self, 
        message: str, 
        embedding_scores: Dict[str, float],
        conversation_history: List[str]
    ) -> str:
        """
        Layer 3: Context-aware refinement
        
        Maintains intent consistency across conversation
        Detects intent switches
        """
        # Get current top intent
        current_intent = max(embedding_scores, key=embedding_scores.get)
        current_score = embedding_scores[current_intent]
        
        # If we have conversation history, check for consistency
        if len(conversation_history) >= 2:
            # Get previous message
            prev_message = conversation_history[-2]
            
            # Calculate similarity with previous message
            prev_embedding = self.embedder.encode(prev_message, convert_to_numpy=True)
            curr_embedding = self.embedder.encode(message, convert_to_numpy=True)
            
            message_similarity = cosine_similarity(
                prev_embedding.reshape(1, -1),
                curr_embedding.reshape(1, -1)
            )[0][0]
            
            # If messages are similar but intent changed significantly, prefer consistency
            if message_similarity > 0.7:
                # Messages are semantically similar
                # Keep previous intent unless new intent is much stronger
                prev_scores = self._layer1_embedding_classification(prev_message)
                prev_intent = max(prev_scores, key=prev_scores.get)
                
                if current_intent != prev_intent and current_score < 0.8:
                    # Likely same topic, keep previous intent
                    return prev_intent
        
        return current_intent
    
    def _calculate_confidence(self, embedding_score: float, llm_validation: Dict) -> float:
        """Calculate final confidence score"""
        base_confidence = embedding_score
        
        # Adjust based on LLM validation
        if llm_validation.get("validated"):
            base_confidence = min(0.99, base_confidence * 1.1)
        elif llm_validation.get("needs_review"):
            base_confidence = base_confidence * 0.9
        
        return round(base_confidence, 3)
    
    def _generate_reasoning(
        self, 
        intent: str, 
        scores: Dict[str, float], 
        message: str
    ) -> str:
        """Generate human-readable reasoning"""
        score = scores[intent]
        
        if score > 0.8:
            confidence_desc = "very high"
        elif score > 0.6:
            confidence_desc = "high"
        elif score > 0.4:
            confidence_desc = "moderate"
        else:
            confidence_desc = "low"
        
        intent_desc = self.INTENT_DEFINITIONS[intent]["description"]
        
        reasoning = (
            f"Detected intent: {intent} ({confidence_desc} confidence: {score:.2f}). "
            f"Message shows characteristics of: {intent_desc}. "
            f"Semantic similarity score indicates {confidence_desc} match."
        )
        
        return reasoning
    
    def batch_detect(
        self, 
        messages: List[str], 
        conversation_histories: Optional[List[List[str]]] = None
    ) -> List[IntentResult]:
        """Batch processing for multiple messages"""
        results = []
        
        for i, message in enumerate(messages):
            history = conversation_histories[i] if conversation_histories else None
            result = self.detect(message, history)
            results.append(result)
        
        return results


# Factory function for easy integration
def create_semantic_intent_engine(model_name: str = "intfloat/multilingual-e5-large") -> SemanticIntentEngine:
    """Factory function to create the intent engine"""
    return SemanticIntentEngine(model_name)


if __name__ == "__main__":
    # Test the engine
    engine = create_semantic_intent_engine()
    
    test_messages = [
        "I feel so lonely even when I'm around people",
        "What is anxiety and how does it work?",
        "Give me techniques to calm down",
        "I want to end my life",
        "Can you explain what you mean?",
    ]
    
    print("\n" + "="*80)
    print("SEMANTIC INTENT ENGINE TEST")
    print("="*80 + "\n")
    
    for msg in test_messages:
        result = engine.detect(msg)
        print(f"Message: {msg}")
        print(f"Intent: {result.primary_intent} (confidence: {result.confidence})")
        print(f"Reasoning: {result.reasoning}")
        print(f"Alternatives: {result.alternative_intents}")
        print("-" * 80)
