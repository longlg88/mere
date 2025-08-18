"""
LangGraph-based Conversation State Management
Day 8 Task 8.1: LangGraph Core Implementation
"""

from typing import Dict, Any, Optional, List, Literal
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import uuid
import logging

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

class ConversationState(str, Enum):
    """Conversation state definitions"""
    PARSING = "parsing"              # STT + NLU processing
    VALIDATION = "validation"        # Entity validation & completion
    CONFIRMATION = "confirmation"    # User confirmation required
    EXECUTION = "execution"         # Business action execution
    RESPONSE = "response"           # TTS generation & delivery
    INTERRUPTED = "interrupted"     # User interruption handling
    COMPLETED = "completed"         # Conversation complete

@dataclass
class ConversationContext:
    """Context information for conversation"""
    user_id: str
    conversation_id: str
    current_state: ConversationState
    intent: Optional[str] = None
    entities: Dict[str, Any] = None
    confidence: float = 0.0
    previous_context: Optional[Dict[str, Any]] = None
    interruption_reason: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

class ConversationStateGraph:
    """LangGraph-based conversation state machine"""
    
    def __init__(self):
        self.graph = None
        self.checkpointer = MemorySaver()  # In-memory state persistence
        self.active_conversations: Dict[str, ConversationContext] = {}
        self._build_graph()
        
    def _build_graph(self) -> None:
        """Build the conversation state graph"""
        
        # Define state graph
        workflow = StateGraph(ConversationContext)
        
        # Add nodes for each state
        workflow.add_node(ConversationState.PARSING, self._handle_parsing)
        workflow.add_node(ConversationState.VALIDATION, self._handle_validation)
        workflow.add_node(ConversationState.CONFIRMATION, self._handle_confirmation)
        workflow.add_node(ConversationState.EXECUTION, self._handle_execution)
        workflow.add_node(ConversationState.RESPONSE, self._handle_response)
        workflow.add_node(ConversationState.INTERRUPTED, self._handle_interruption)
        
        # Set entry point
        workflow.set_entry_point(ConversationState.PARSING)
        
        # Define state transitions
        workflow.add_conditional_edges(
            ConversationState.PARSING,
            self._route_from_parsing,
            {
                ConversationState.VALIDATION: ConversationState.VALIDATION,
                ConversationState.INTERRUPTED: ConversationState.INTERRUPTED,
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            ConversationState.VALIDATION,
            self._route_from_validation,
            {
                ConversationState.CONFIRMATION: ConversationState.CONFIRMATION,
                ConversationState.EXECUTION: ConversationState.EXECUTION,
                ConversationState.INTERRUPTED: ConversationState.INTERRUPTED
            }
        )
        
        workflow.add_conditional_edges(
            ConversationState.CONFIRMATION,
            self._route_from_confirmation,
            {
                ConversationState.EXECUTION: ConversationState.EXECUTION,
                ConversationState.VALIDATION: ConversationState.VALIDATION,
                ConversationState.INTERRUPTED: ConversationState.INTERRUPTED,
                END: END
            }
        )
        
        workflow.add_edge(ConversationState.EXECUTION, ConversationState.RESPONSE)
        workflow.add_edge(ConversationState.RESPONSE, END)
        workflow.add_edge(ConversationState.INTERRUPTED, END)
        
        # Compile graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
    def _handle_parsing(self, state: ConversationContext) -> ConversationContext:
        """Handle STT + NLU parsing state"""
        logger.info(f"[PARSING] Processing: {state.conversation_id}")
        
        # This will be called by the main pipeline
        # For now, just update the state
        state.current_state = ConversationState.PARSING
        state.updated_at = datetime.now()
        
        return state
    
    def _handle_validation(self, state: ConversationContext) -> ConversationContext:
        """Handle entity validation and completion"""
        logger.info(f"[VALIDATION] Validating entities: {state.entities}")
        
        state.current_state = ConversationState.VALIDATION
        state.updated_at = datetime.now()
        
        # Entity validation logic will be implemented here
        return state
    
    def _handle_confirmation(self, state: ConversationContext) -> ConversationContext:
        """Handle user confirmation"""
        logger.info(f"[CONFIRMATION] Requesting confirmation for: {state.intent}")
        
        state.current_state = ConversationState.CONFIRMATION
        state.updated_at = datetime.now()
        
        return state
    
    def _handle_execution(self, state: ConversationContext) -> ConversationContext:
        """Handle business action execution"""
        logger.info(f"[EXECUTION] Executing: {state.intent}")
        
        state.current_state = ConversationState.EXECUTION
        state.updated_at = datetime.now()
        
        return state
    
    def _handle_response(self, state: ConversationContext) -> ConversationContext:
        """Handle response generation"""
        logger.info(f"[RESPONSE] Generating response")
        
        state.current_state = ConversationState.RESPONSE
        state.updated_at = datetime.now()
        
        return state
    
    def _handle_interruption(self, state: ConversationContext) -> ConversationContext:
        """Handle user interruption"""
        logger.info(f"[INTERRUPTED] Handling interruption: {state.interruption_reason}")
        
        state.current_state = ConversationState.INTERRUPTED
        state.updated_at = datetime.now()
        
        return state
    
    def _route_from_parsing(self, state: ConversationContext) -> str:
        """Route decisions from parsing state"""
        
        # Check for interruption keywords
        if self._is_interruption(state):
            state.interruption_reason = "user_cancel"
            return ConversationState.INTERRUPTED
        
        # Check if we have valid intent and entities
        if state.intent and state.confidence > 0.7:
            return ConversationState.VALIDATION
        
        # Low confidence or no intent
        logger.warning(f"Low confidence ({state.confidence}) or no intent detected")
        return END
    
    def _route_from_validation(self, state: ConversationContext) -> str:
        """Route decisions from validation state"""
        
        if self._is_interruption(state):
            return ConversationState.INTERRUPTED
        
        # Check if confirmation is required
        if self._requires_confirmation(state):
            return ConversationState.CONFIRMATION
        
        # Proceed to execution
        return ConversationState.EXECUTION
    
    def _route_from_confirmation(self, state: ConversationContext) -> str:
        """Route decisions from confirmation state"""
        
        if self._is_interruption(state):
            return ConversationState.INTERRUPTED
        
        # This will be set by user response to confirmation
        # For now, assume confirmation is given
        return ConversationState.EXECUTION
    
    def _is_interruption(self, state: ConversationContext) -> bool:
        """Check if current input is an interruption"""
        if not state.intent:
            return False
            
        interruption_intents = [
            "cancel", "stop", "no", "abort", 
            "nevermind", "forget_it", "취소"
        ]
        
        return state.intent.lower() in interruption_intents
    
    def _requires_confirmation(self, state: ConversationContext) -> bool:
        """Check if the action requires user confirmation"""
        
        # High-impact actions that need confirmation
        confirmation_required_intents = [
            "delete_memo", "delete_todo", "cancel_event",
            "delete_all", "clear_data"
        ]
        
        if state.intent in confirmation_required_intents:
            return True
        
        # Low confidence actions need confirmation
        if state.confidence < 0.9:
            return True
            
        return False
    
    def start_conversation(self, user_id: str, initial_context: Dict[str, Any] = None) -> str:
        """Start a new conversation"""
        conversation_id = str(uuid.uuid4())
        
        context = ConversationContext(
            user_id=user_id,
            conversation_id=conversation_id,
            current_state=ConversationState.PARSING,
            entities=initial_context or {}
        )
        
        self.active_conversations[conversation_id] = context
        logger.info(f"Started conversation {conversation_id} for user {user_id}")
        
        return conversation_id
    
    def process_input(self, conversation_id: str, intent: str, entities: Dict[str, Any], 
                     confidence: float) -> ConversationContext:
        """Process user input through the state machine"""
        
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        context = self.active_conversations[conversation_id]
        
        # Update context with new input
        context.intent = intent
        context.entities.update(entities)
        context.confidence = confidence
        
        # For now, use simple rule-based state transitions instead of LangGraph
        # This is a simplified implementation for testing
        try:
            # Check for interruption
            if self._is_interruption(context):
                context.current_state = ConversationState.INTERRUPTED
                context.interruption_reason = "user_cancel"
            # Check if confirmation is required
            elif self._requires_confirmation(context):
                context.current_state = ConversationState.CONFIRMATION
            # Otherwise proceed to execution
            else:
                context.current_state = ConversationState.EXECUTION
            
            context.updated_at = datetime.now()
            self.active_conversations[conversation_id] = context
            
            logger.info(f"Processed input for {conversation_id}: "
                       f"intent={intent} -> {context.current_state}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error processing conversation {conversation_id}: {e}")
            context.current_state = ConversationState.INTERRUPTED
            context.interruption_reason = f"processing_error: {str(e)}"
            return context
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context"""
        return self.active_conversations.get(conversation_id)
    
    def end_conversation(self, conversation_id: str) -> None:
        """End and cleanup conversation"""
        if conversation_id in self.active_conversations:
            context = self.active_conversations[conversation_id]
            context.current_state = ConversationState.COMPLETED
            logger.info(f"Ended conversation {conversation_id}")
            # Keep in memory for a while for debugging
            # del self.active_conversations[conversation_id]
    
    def get_active_conversations(self) -> Dict[str, ConversationContext]:
        """Get all active conversations"""
        return {k: v for k, v in self.active_conversations.items() 
                if v.current_state != ConversationState.COMPLETED}


# Global state manager instance
conversation_state_manager = ConversationStateGraph()


def get_state_manager() -> ConversationStateGraph:
    """Get the global state manager instance"""
    return conversation_state_manager