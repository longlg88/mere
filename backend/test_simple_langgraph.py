#!/usr/bin/env python3
"""
Simple LangGraph test inside Docker container
"""

from conversation_state import ConversationStateGraph, ConversationState
import traceback

def test_basic_functionality():
    """Test basic LangGraph functionality"""
    try:
        print("🧪 Testing Basic LangGraph Functionality")
        print("=" * 45)
        
        # Test 1: Create state manager
        print("📝 Test 1: Create State Manager")
        state_manager = ConversationStateGraph()
        print("   ✅ State manager created successfully")
        
        # Test 2: Start conversation
        print("\n💬 Test 2: Start Conversation")
        user_id = "docker-test-user"
        conversation_id = state_manager.start_conversation(user_id)
        print(f"   ✅ Conversation ID: {conversation_id}")
        
        # Test 3: Get context
        print("\n📋 Test 3: Get Conversation Context")
        context = state_manager.get_conversation(conversation_id)
        print(f"   ✅ Current state: {context.current_state}")
        print(f"   ✅ User ID: {context.user_id}")
        print(f"   ✅ Created at: {context.created_at}")
        
        # Test 4: Process input
        print("\n🔄 Test 4: Process Input (State Transition)")
        result = state_manager.process_input(
            conversation_id=conversation_id,
            intent="create_memo",
            entities={"content": "Docker test memo"},
            confidence=0.95
        )
        print(f"   ✅ New state: {result.current_state}")
        print(f"   ✅ Intent: {result.intent}")
        print(f"   ✅ Entities: {result.entities}")
        
        # Test 5: Test interruption
        print("\n🚫 Test 5: Interruption Handling")
        interrupted = state_manager.process_input(
            conversation_id=conversation_id,
            intent="cancel",
            entities={},
            confidence=0.9
        )
        print(f"   ✅ Interrupted state: {interrupted.current_state}")
        
        # Test 6: Active conversations
        print("\n📊 Test 6: Active Conversations")
        active = state_manager.get_active_conversations()
        print(f"   ✅ Active conversations count: {len(active)}")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return False

def test_state_transitions():
    """Test state transition logic"""
    try:
        print("\n🔄 Testing State Transitions")
        print("=" * 30)
        
        state_manager = ConversationStateGraph()
        conversation_id = state_manager.start_conversation("transition-test")
        
        # Test different intents and confidence levels
        test_cases = [
            ("create_memo", {"content": "test"}, 0.95, "Expected high confidence memo"),
            ("create_todo", {"task": "test task"}, 0.85, "Expected medium confidence todo"),
            ("delete_memo", {"memo_id": "123"}, 0.9, "Expected confirmation required"),
            ("cancel", {}, 0.9, "Expected interruption"),
        ]
        
        for intent, entities, confidence, description in test_cases:
            print(f"\n   Testing: {description}")
            result = state_manager.process_input(conversation_id, intent, entities, confidence)
            print(f"   ➡️  State: {result.current_state}")
            print(f"   ➡️  Intent: {result.intent}")
            
        print("\n✅ State transition tests completed")
        return True
        
    except Exception as e:
        print(f"\n❌ State transition test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = True
    
    print("🚀 Starting LangGraph Tests in Docker")
    print("=" * 50)
    
    # Run tests
    success &= test_basic_functionality()
    success &= test_state_transitions()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All LangGraph Docker tests passed!")
    else:
        print("❌ Some tests failed")
    
    exit(0 if success else 1)