"""
Enhanced NLU Service with LangGraph State Management Integration
Day 8: Context-Aware NLU with Conversation State
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI
from dataclasses import dataclass
from datetime import datetime, timedelta

from conversation_state import (
    ConversationContext, ConversationState, get_state_manager
)
from nlu_service import GPT5NLUService, Intent, NLUResult

logger = logging.getLogger(__name__)

@dataclass
class ContextualNLUResult(NLUResult):
    """NLU result with conversation context"""
    conversation_id: Optional[str] = None
    requires_confirmation: bool = False
    context_entities: Dict[str, Any] = None
    previous_intent: Optional[str] = None
    
    def __post_init__(self):
        if self.context_entities is None:
            self.context_entities = {}

class EnhancedNLUService(GPT5NLUService):
    """Context-aware NLU service with LangGraph integration"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.state_manager = get_state_manager()
        
        # Context-aware prompts
        self.context_aware_prompt = """
        You are an advanced NLU system that understands conversation context.
        
        CONVERSATION CONTEXT:
        - Previous Intent: {previous_intent}
        - Previous Entities: {previous_entities}
        - Current State: {current_state}
        - User History: {user_context}
        
        CURRENT INPUT: "{text}"
        
        Consider the conversation context when interpreting the user's intent.
        Handle references like "그것", "방금 말한", "아까", "그 회의" by using context.
        
        Available Intents: {intents}
        
        Respond with JSON:
        {{
            "intent": "intent_name",
            "confidence": 0.95,
            "entities": {{}},
            "context_resolved": {{}},  # Resolved contextual references
            "requires_confirmation": false
        }}
        """
        
        # Reference resolution patterns
        self.reference_patterns = {
            "그것": ["that", "it"],
            "그거": ["that", "it"], 
            "방금": ["just now", "previous"],
            "아까": ["earlier", "before"],
            "그": ["that", "the"],
            "이": ["this"],
            "저": ["that over there"]
        }
    
    def process_with_context(self, text: str, user_id: str, 
                           conversation_id: str = None) -> ContextualNLUResult:
        """Process text with conversation context"""
        
        # Get or create conversation context
        if conversation_id:
            context = self.state_manager.get_conversation(conversation_id)
        else:
            conversation_id = self.state_manager.start_conversation(user_id)
            context = self.state_manager.get_conversation(conversation_id)
        
        # Build context for GPT
        context_data = self._build_context_data(context)
        
        # Enhanced NLU with context
        result = self._process_with_context_prompt(text, context_data)
        
        # Create contextual result
        contextual_result = ContextualNLUResult(
            intent=Intent(
                name=result["intent"],
                confidence=result["confidence"],
                entities=result.get("entities", {})
            ),
            text=text,
            confidence=result["confidence"],
            entities=result.get("entities", {}),
            conversation_id=conversation_id,
            requires_confirmation=result.get("requires_confirmation", False),
            context_entities=result.get("context_resolved", {}),
            previous_intent=context.intent if context else None
        )
        
        # Update state machine
        if context:
            updated_context = self.state_manager.process_input(
                conversation_id=conversation_id,
                intent=result["intent"],
                entities=result.get("entities", {}),
                confidence=result["confidence"]
            )
            
            # Add state-specific processing
            contextual_result = self._enhance_with_state_logic(
                contextual_result, updated_context
            )
        
        return contextual_result
    
    def _build_context_data(self, context: Optional[ConversationContext]) -> Dict[str, Any]:
        """Build context data for GPT prompt"""
        if not context:
            return {
                "previous_intent": None,
                "previous_entities": {},
                "current_state": "initial",
                "user_context": {}
            }
        
        return {
            "previous_intent": context.intent,
            "previous_entities": context.entities,
            "current_state": context.current_state.value,
            "user_context": context.previous_context or {}
        }
    
    def _process_with_context_prompt(self, text: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process text using context-aware prompt"""
        
        # Build enhanced prompt
        prompt = self.context_aware_prompt.format(
            previous_intent=context_data.get("previous_intent"),
            previous_entities=json.dumps(context_data.get("previous_entities", {})),
            current_state=context_data.get("current_state"),
            user_context=json.dumps(context_data.get("user_context", {})),
            text=text,
            intents=", ".join(self.intents.keys())
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using available model
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert NLU system with conversation context awareness."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            logger.info(f"Context-aware NLU result: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in context NLU: {e}")
            return self._fallback_to_basic_nlu(text)
        except Exception as e:
            logger.error(f"Error in context-aware NLU: {e}")
            return self._fallback_to_basic_nlu(text)
    
    def _fallback_to_basic_nlu(self, text: str) -> Dict[str, Any]:
        """Fallback to basic NLU when context processing fails"""
        basic_result = self.process_text(text)
        return {
            "intent": basic_result.intent.name,
            "confidence": basic_result.confidence,
            "entities": basic_result.entities or {},
            "context_resolved": {},
            "requires_confirmation": False
        }
    
    def _enhance_with_state_logic(self, result: ContextualNLUResult, 
                                context: ConversationContext) -> ContextualNLUResult:
        """Add state-specific enhancements to NLU result"""
        
        # Confirmation state handling
        if context.current_state == ConversationState.CONFIRMATION:
            result = self._handle_confirmation_response(result, context)
        
        # Validation state handling
        elif context.current_state == ConversationState.VALIDATION:
            result = self._handle_validation_response(result, context)
        
        # Interruption detection
        if self._is_interruption_intent(result.intent.name):
            result.requires_confirmation = True
            
        return result
    
    def _handle_confirmation_response(self, result: ContextualNLUResult,
                                    context: ConversationContext) -> ContextualNLUResult:
        """Handle responses during confirmation state"""
        
        # Map confirmation responses
        confirmation_mapping = {
            "yes": "confirm",
            "no": "reject", 
            "네": "confirm",
            "아니요": "reject",
            "맞아": "confirm",
            "틀려": "reject",
            "확인": "confirm",
            "취소": "reject"
        }
        
        intent_name = result.intent.name.lower()
        if intent_name in confirmation_mapping:
            result.intent.name = confirmation_mapping[intent_name]
            result.confidence = min(result.confidence + 0.1, 1.0)  # Boost confidence
        
        return result
    
    def _handle_validation_response(self, result: ContextualNLUResult,
                                  context: ConversationContext) -> ContextualNLUResult:
        """Handle responses during validation state"""
        
        # Entity completion logic
        if context.intent and not result.entities:
            # User might be providing missing entities
            result.intent.name = f"complete_{context.intent}"
            result.entities = self._extract_completion_entities(result.text)
        
        return result
    
    def _extract_completion_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities for completion responses"""
        entities = {}
        
        # Time expressions
        time_patterns = {
            r'(\d+)시': 'time_hour',
            r'(\d+)분': 'time_minute', 
            r'(내일|오늘|모레)': 'date_relative',
            r'(\d+월|\d+일)': 'date_specific'
        }
        
        for pattern, entity_type in time_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = matches[0]
        
        return entities
    
    def _is_interruption_intent(self, intent: str) -> bool:
        """Check if intent represents an interruption"""
        interruption_intents = {
            "cancel", "stop", "abort", "quit", "exit",
            "취소", "중단", "그만", "나가기"
        }
        return intent.lower() in interruption_intents
    
    def resolve_references(self, text: str, context: ConversationContext) -> str:
        """Resolve contextual references in text"""
        if not context or not context.entities:
            return text
        
        resolved_text = text
        
        # Simple reference resolution
        for reference, replacements in self.reference_patterns.items():
            if reference in text:
                # Try to find appropriate replacement from context
                for entity_key, entity_value in context.entities.items():
                    if isinstance(entity_value, str):
                        resolved_text = resolved_text.replace(reference, entity_value)
                        break
        
        return resolved_text
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of conversation for context"""
        context = self.state_manager.get_conversation(conversation_id)
        if not context:
            return None
        
        return {
            "conversation_id": conversation_id,
            "current_state": context.current_state.value,
            "intent": context.intent,
            "entities": context.entities,
            "confidence": context.confidence,
            "duration": (datetime.now() - context.created_at).total_seconds()
        }

# Global enhanced NLU service instance
enhanced_nlu_service = None

def get_enhanced_nlu_service() -> EnhancedNLUService:
    """Get the global enhanced NLU service instance"""
    global enhanced_nlu_service
    if enhanced_nlu_service is None:
        enhanced_nlu_service = EnhancedNLUService()
    return enhanced_nlu_service