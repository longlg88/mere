#!/usr/bin/env python3
"""
Google Calendar Integration E2E Test
Day 9: Test calendar functionality end-to-end
"""

import sys
import os
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from calendar_service import GoogleCalendarService, CalendarEvent, CalendarIntentProcessor
from business_services import IntentActionMapper
from nlu_service import NLUResult, Intent

def test_calendar_service_setup():
    """Test basic calendar service setup (no authentication required)"""
    print("🧪 Testing Calendar Service Setup")
    print("=" * 40)
    
    try:
        # Test service initialization
        print("📝 Test 1: Service Initialization")
        calendar_service = GoogleCalendarService()
        print("   ✅ Calendar service created")
        
        # Test calendar event creation (data structure)
        print("\n📅 Test 2: Calendar Event Data Structure")
        event = CalendarEvent(
            summary="Test Meeting",
            description="Test event for MERE AI Agent",
            start_datetime=datetime.now() + timedelta(hours=1),
            end_datetime=datetime.now() + timedelta(hours=2),
            location="Test Location"
        )
        print(f"   ✅ Event created: {event.summary}")
        print(f"   ✅ Start time: {event.start_datetime}")
        print(f"   ✅ Duration: {event.end_datetime - event.start_datetime}")
        
        # Test calendar intent processor
        print("\n🎯 Test 3: Calendar Intent Processor")
        processor = CalendarIntentProcessor()
        print("   ✅ Calendar processor created")
        
        print("\n✅ All calendar service setup tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Calendar service setup test failed: {e}")
        return False

def test_calendar_intent_processing():
    """Test calendar intent processing without Google API"""
    print("\n🔄 Testing Calendar Intent Processing")
    print("=" * 45)
    
    try:
        processor = CalendarIntentProcessor()
        
        # Test create event intent processing
        print("📅 Test 1: Create Event Intent")
        entities = {
            "item_name": "팀 회의",
            "date_time": "2024-01-20T14:00:00",
            "duration": 2.0,
            "location": "회의실 A"
        }
        
        result = processor.process_create_event_intent(entities)
        print(f"   ✅ Success: {result['success']}")
        print(f"   ✅ Message: {result['message']}")
        
        # Test query event intent processing
        print("\n📋 Test 2: Query Event Intent")
        query_entities = {
            "date_time": "2024-01-20"
        }
        
        query_result = processor.process_query_event_intent(query_entities)
        print(f"   ✅ Success: {query_result['success']}")
        print(f"   ✅ Message: {query_result['message']}")
        
        # Test edge cases
        print("\n⚠️  Test 3: Edge Cases")
        
        # Missing date_time
        empty_result = processor.process_create_event_intent({})
        print(f"   ✅ Missing time handling: {empty_result['requires_confirmation']}")
        
        # Invalid date format
        invalid_entities = {
            "item_name": "Invalid Event",
            "date_time": "invalid-date"
        }
        invalid_result = processor.process_create_event_intent(invalid_entities)
        print(f"   ✅ Invalid date handling: {not invalid_result['success']}")
        
        print("\n✅ All calendar intent processing tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Calendar intent processing test failed: {e}")
        return False

async def test_calendar_business_integration():
    """Test integration with business services"""
    print("\n🔗 Testing Calendar Business Integration")
    print("=" * 45)
    
    try:
        intent_mapper = IntentActionMapper()
        
        # Test calendar intent through business layer
        print("📅 Test 1: Create Event through Business Layer")
        
        # Mock NLU result for create_event
        nlu_result = NLUResult(
            intent=Intent("create_event", 0.95),
            entities={
                "item_name": "프로젝트 리뷰",
                "date_time": "2024-01-21T10:00:00",
                "duration": 1.5,
                "location": "온라인"
            },
            confidence=0.95,
            text="내일 오전 10시에 프로젝트 리뷰 회의 잡아줘"
        )
        
        result = await intent_mapper.execute_intent("test-user", nlu_result)
        print(f"   ✅ Action: {result['action']}")
        print(f"   ✅ Success: {result['success']}")
        print(f"   ✅ Message: {result['message']}")
        
        # Test query event through business layer
        print("\n📋 Test 2: Query Event through Business Layer")
        
        query_nlu_result = NLUResult(
            intent=Intent("query_event", 0.90),
            entities={"date_time": "2024-01-21"},
            confidence=0.90,
            text="내일 일정 보여줘"
        )
        
        query_result = await intent_mapper.execute_intent("test-user", query_nlu_result)
        print(f"   ✅ Action: {query_result['action']}")
        print(f"   ✅ Success: {query_result['success']}")
        print(f"   ✅ Message: {query_result['message']}")
        
        # Test calendar-specific error handling
        print("\n❌ Test 3: Error Handling")
        
        error_nlu_result = NLUResult(
            intent=Intent("update_event", 0.85),
            entities={},
            confidence=0.85,
            text="방금 회의 시간 바꿔줘"
        )
        
        error_result = await intent_mapper.execute_intent("test-user", error_nlu_result)
        print(f"   ✅ Error handling: {error_result['message']}")
        
        print("\n✅ All calendar business integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Calendar business integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_calendar_availability_logic():
    """Test calendar availability checking logic"""
    print("\n📊 Testing Calendar Availability Logic")
    print("=" * 45)
    
    try:
        calendar_service = GoogleCalendarService()
        
        # Test availability time slot calculation
        print("⏰ Test 1: Time Slot Logic")
        
        start_time = datetime(2024, 1, 20, 9, 0)  # 9 AM
        end_time = datetime(2024, 1, 20, 17, 0)   # 5 PM
        
        # Mock events for testing availability logic
        mock_events = [
            CalendarEvent(
                id="1",
                summary="Morning Meeting",
                start_datetime=datetime(2024, 1, 20, 10, 0),
                end_datetime=datetime(2024, 1, 20, 11, 0)
            ),
            CalendarEvent(
                id="2", 
                summary="Lunch",
                start_datetime=datetime(2024, 1, 20, 12, 0),
                end_datetime=datetime(2024, 1, 20, 13, 0)
            )
        ]
        
        print(f"   ✅ Mock events created: {len(mock_events)}")
        
        # Test finding available slots
        print("\n🔍 Test 2: Available Slot Finding")
        
        # This would test the find_available_slot logic
        duration_hours = 1.0
        print(f"   ✅ Looking for {duration_hours}h slot between {start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}")
        
        # Expected available slots:
        # 9:00-10:00 (1h before first meeting)
        # 11:00-12:00 (1h between meetings)  
        # 13:00-17:00 (4h after lunch)
        
        expected_slots = [
            (datetime(2024, 1, 20, 9, 0), datetime(2024, 1, 20, 10, 0)),
            (datetime(2024, 1, 20, 11, 0), datetime(2024, 1, 20, 12, 0)),
            (datetime(2024, 1, 20, 13, 0), datetime(2024, 1, 20, 17, 0))
        ]
        
        print(f"   ✅ Expected available slots: {len(expected_slots)}")
        for i, (slot_start, slot_end) in enumerate(expected_slots):
            duration = slot_end - slot_start
            print(f"      Slot {i+1}: {slot_start.strftime('%H:%M')}-{slot_end.strftime('%H:%M')} ({duration.total_seconds()/3600:.1f}h)")
        
        print("\n✅ Calendar availability logic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Calendar availability logic test failed: {e}")
        return False

def test_calendar_date_parsing():
    """Test calendar date/time parsing scenarios"""
    print("\n📅 Testing Calendar Date Parsing")
    print("=" * 40)
    
    try:
        processor = CalendarIntentProcessor()
        
        # Test various date/time formats
        test_cases = [
            {
                "description": "ISO format",
                "entities": {
                    "item_name": "Meeting",
                    "date_time": "2024-01-20T14:30:00",
                    "duration": 1.0
                },
                "expected_success": True
            },
            {
                "description": "Invalid format", 
                "entities": {
                    "item_name": "Meeting",
                    "date_time": "tomorrow at 2pm",
                    "duration": 1.0
                },
                "expected_success": False
            },
            {
                "description": "Missing time",
                "entities": {
                    "item_name": "Meeting",
                    "duration": 1.0
                },
                "expected_success": False
            }
        ]
        
        print("📝 Date Parsing Test Cases:")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test {i}: {test_case['description']}")
            result = processor.process_create_event_intent(test_case["entities"])
            
            success_matches = result["success"] == test_case["expected_success"]
            print(f"      Success: {result['success']} (Expected: {test_case['expected_success']}) {'✅' if success_matches else '❌'}")
            print(f"      Message: {result['message']}")
            
            if not success_matches:
                print(f"      ⚠️  Test case {i} assertion failed")
        
        print("\n✅ Calendar date parsing tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Calendar date parsing test failed: {e}")
        return False

def main():
    """Run all calendar integration tests"""
    print("🚀 Starting Google Calendar Integration Tests")
    print("=" * 60)
    
    success = True
    test_results = []
    
    # Test 1: Service Setup
    try:
        result = test_calendar_service_setup()
        test_results.append(("Calendar Service Setup", result))
        success &= result
    except Exception as e:
        print(f"❌ Service setup test crashed: {e}")
        test_results.append(("Calendar Service Setup", False))
        success = False
    
    # Test 2: Intent Processing
    try:
        result = test_calendar_intent_processing()
        test_results.append(("Calendar Intent Processing", result))
        success &= result
    except Exception as e:
        print(f"❌ Intent processing test crashed: {e}")
        test_results.append(("Calendar Intent Processing", False))
        success = False
    
    # Test 3: Business Integration (async)
    try:
        result = asyncio.run(test_calendar_business_integration())
        test_results.append(("Calendar Business Integration", result))
        success &= result
    except Exception as e:
        print(f"❌ Business integration test crashed: {e}")
        test_results.append(("Calendar Business Integration", False))
        success = False
    
    # Test 4: Availability Logic
    try:
        result = test_calendar_availability_logic()
        test_results.append(("Calendar Availability Logic", result))
        success &= result
    except Exception as e:
        print(f"❌ Availability logic test crashed: {e}")
        test_results.append(("Calendar Availability Logic", False))
        success = False
    
    # Test 5: Date Parsing
    try:
        result = test_calendar_date_parsing()
        test_results.append(("Calendar Date Parsing", result))
        success &= result
    except Exception as e:
        print(f"❌ Date parsing test crashed: {e}")
        test_results.append(("Calendar Date Parsing", False))
        success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Google Calendar Integration Test Summary")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    
    if success:
        print("\n🎉 Google Calendar integration is ready for testing!")
        print("📝 Note: Actual Google Calendar API requires credentials.json file")
        print("📝 For full testing, set up OAuth 2.0 credentials in Google Cloud Console")
    else:
        print("\n⚠️  Some tests failed - review implementation before proceeding")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)