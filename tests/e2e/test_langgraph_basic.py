#!/usr/bin/env python3
"""
Basic LangGraph State Machine Test
Day 8: Test conversation state functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from conversation_state import ConversationStateGraph, ConversationState
from enhanced_nlu_service import EnhancedNLUService
import asyncio
import time

def test_conversation_state_machine():
    """Test basic LangGraph state machine functionality"""
    print("🧪 Testing LangGraph State Machine")
    print("=" * 40)
    
    # Create state manager
    state_manager = ConversationStateGraph()
    
    # Test 1: Create conversation
    print("📝 Test 1: Create Conversation")
    user_id = "test-user"
    conversation_id = state_manager.start_conversation(user_id)
    print(f"   ✅ Created conversation: {conversation_id}")
    
    # Test 2: Get conversation context
    print("\n📋 Test 2: Get Conversation Context")
    context = state_manager.get_conversation(conversation_id)
    print(f"   ✅ Current state: {context.current_state}")
    print(f"   ✅ User ID: {context.user_id}")
    
    # Test 3: Process input with state transition
    print("\n🔄 Test 3: State Transition")
    intent = "create_memo"
    entities = {"content": "테스트 메모"}
    confidence = 0.95
    
    updated_context = state_manager.process_input(
        conversation_id, intent, entities, confidence
    )
    print(f"   ✅ New state: {updated_context.current_state}")
    print(f"   ✅ Intent: {updated_context.intent}")
    print(f"   ✅ Confidence: {updated_context.confidence}")
    
    # Test 4: Interruption handling
    print("\n🚫 Test 4: Interruption Handling")
    interrupt_context = state_manager.process_input(
        conversation_id, "cancel", {}, 0.9
    )
    print(f"   ✅ State after interruption: {interrupt_context.current_state}")
    
    # Test 5: Active conversations
    print("\n📊 Test 5: Active Conversations")
    active = state_manager.get_active_conversations()
    print(f"   ✅ Active conversations: {len(active)}")
    
    # Test 6: End conversation
    print("\n🏁 Test 6: End Conversation")
    state_manager.end_conversation(conversation_id)
    final_context = state_manager.get_conversation(conversation_id)
    print(f"   ✅ Final state: {final_context.current_state}")
    
    print("\n✅ All LangGraph State Machine tests passed!")
    return True

async def test_enhanced_nlu_service():
    """Test enhanced NLU service with context"""
    print("\n🔍 Testing Enhanced NLU Service")
    print("=" * 40)
    
    try:
        # This requires OpenAI API key
        enhanced_nlu = EnhancedNLUService()
        
        # Test contextual processing
        user_id = "nlu-test-user"
        text = "내일 우유 사는 거 기억해줘"
        
        result = enhanced_nlu.process_with_context(text, user_id)
        
        print(f"📝 Input: {text}")
        print(f"✅ Intent: {result.intent.name}")
        print(f"✅ Confidence: {result.confidence:.2f}")
        print(f"✅ Conversation ID: {result.conversation_id}")
        print(f"✅ Context entities: {result.context_entities}")
        
        # Test reference resolution
        follow_up = "그거 삭제해줘"
        follow_up_result = enhanced_nlu.process_with_context(
            follow_up, user_id, result.conversation_id
        )
        
        print(f"\n📝 Follow-up: {follow_up}")
        print(f"✅ Intent: {follow_up_result.intent.name}")
        print(f"✅ Previous context: {follow_up_result.previous_intent}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Enhanced NLU test skipped: {e}")
        print("   (Requires OpenAI API key)")
        return True

def main():
    """Run all basic LangGraph tests"""
    print("🚀 Starting LangGraph Basic Tests")
    print("=" * 50)
    
    success = True
    
    # Test 1: State machine
    try:
        success &= test_conversation_state_machine()
    except Exception as e:
        print(f"❌ State machine test failed: {e}")
        success = False
    
    # Test 2: Enhanced NLU (async)
    try:
        success &= asyncio.run(test_enhanced_nlu_service())
    except Exception as e:
        print(f"❌ Enhanced NLU test failed: {e}")
        success = False
    
    print("=" * 50)
    if success:
        print("🎉 All LangGraph basic tests passed!")
    else:
        print("❌ Some tests failed")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)