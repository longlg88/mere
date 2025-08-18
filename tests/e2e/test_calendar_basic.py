#!/usr/bin/env python3
"""
Basic Google Calendar Integration Test (No Database Required)
Day 9: Test calendar functionality end-to-end  
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

def test_calendar_imports():
    """Test that calendar service can be imported"""
    print("🧪 Testing Calendar Service Imports")
    print("=" * 40)
    
    try:
        from calendar_service import (
            GoogleCalendarService, 
            CalendarEvent, 
            CalendarIntentProcessor,
            CalendarAvailability
        )
        
        print("✅ GoogleCalendarService imported successfully")
        print("✅ CalendarEvent imported successfully") 
        print("✅ CalendarIntentProcessor imported successfully")
        print("✅ CalendarAvailability imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_calendar_event_creation():
    """Test calendar event data structure"""
    print("\n📅 Testing Calendar Event Creation")
    print("=" * 40)
    
    try:
        from calendar_service import CalendarEvent
        
        # Test basic event creation
        event = CalendarEvent(
            summary="MERE AI Agent Test Meeting",
            description="Testing calendar integration for MERE AI Agent",
            start_datetime=datetime.now() + timedelta(hours=1),
            end_datetime=datetime.now() + timedelta(hours=2),
            location="Virtual Meeting Room",
            attendees=["test@example.com"]
        )
        
        print(f"✅ Event created: {event.summary}")
        print(f"✅ Start time: {event.start_datetime.strftime('%Y-%m-%d %H:%M')}")
        print(f"✅ End time: {event.end_datetime.strftime('%Y-%m-%d %H:%M')}")
        print(f"✅ Duration: {(event.end_datetime - event.start_datetime).total_seconds() / 3600:.1f} hours")
        print(f"✅ Location: {event.location}")
        print(f"✅ Attendees: {event.attendees}")
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar event creation failed: {e}")
        return False

def test_calendar_service_init():
    """Test calendar service initialization"""
    print("\n🔧 Testing Calendar Service Initialization")
    print("=" * 45)
    
    try:
        from calendar_service import GoogleCalendarService
        
        # Test service initialization without authentication
        calendar_service = GoogleCalendarService()
        
        print("✅ Calendar service initialized")
        print(f"✅ Credentials file: {calendar_service.credentials_file}")
        print(f"✅ Token file: {calendar_service.token_file}")
        print("✅ Service ready for authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar service initialization failed: {e}")
        return False

def test_calendar_intent_processor():
    """Test calendar intent processing logic"""
    print("\n🎯 Testing Calendar Intent Processor")
    print("=" * 40)
    
    try:
        from calendar_service import CalendarIntentProcessor
        
        processor = CalendarIntentProcessor()
        
        # Test create event intent
        print("📝 Test 1: Create Event Intent")
        entities = {
            "item_name": "프로젝트 회의",
            "date_time": "2024-01-20T15:00:00", 
            "duration": 1.5,
            "location": "회의실 B"
        }
        
        result = processor.process_create_event_intent(entities)
        print(f"   Success: {result['success']}")
        print(f"   Message: {result['message']}")
        
        # Test query event intent
        print("\n📋 Test 2: Query Event Intent")
        query_entities = {
            "date_time": "2024-01-20"
        }
        
        query_result = processor.process_query_event_intent(query_entities)
        print(f"   Success: {query_result['success']}")
        print(f"   Message: {query_result['message']}")
        
        # Test missing information handling
        print("\n⚠️  Test 3: Missing Information Handling")
        empty_result = processor.process_create_event_intent({})
        print(f"   Requires confirmation: {empty_result.get('requires_confirmation', False)}")
        print(f"   Message: {empty_result['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar intent processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_calendar_availability():
    """Test calendar availability data structure"""
    print("\n📊 Testing Calendar Availability")
    print("=" * 35)
    
    try:
        from calendar_service import CalendarAvailability
        
        # Test availability creation
        availability = CalendarAvailability(
            start_time=datetime(2024, 1, 20, 9, 0),
            end_time=datetime(2024, 1, 20, 10, 0),
            is_busy=False
        )
        
        busy_slot = CalendarAvailability(
            start_time=datetime(2024, 1, 20, 10, 0),
            end_time=datetime(2024, 1, 20, 11, 0),
            is_busy=True,
            event_summary="Existing Meeting"
        )
        
        print(f"✅ Free slot: {availability.start_time.strftime('%H:%M')}-{availability.end_time.strftime('%H:%M')} (Available)")
        print(f"✅ Busy slot: {busy_slot.start_time.strftime('%H:%M')}-{busy_slot.end_time.strftime('%H:%M')} ({busy_slot.event_summary})")
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar availability test failed: {e}")
        return False

def main():
    """Run all basic calendar tests"""
    print("🚀 Starting Basic Google Calendar Integration Tests")
    print("=" * 60)
    
    success = True
    test_results = []
    
    # Test 1: Imports
    try:
        result = test_calendar_imports()
        test_results.append(("Calendar Imports", result))
        success &= result
    except Exception as e:
        print(f"❌ Import test crashed: {e}")
        test_results.append(("Calendar Imports", False))
        success = False
    
    # Test 2: Event Creation
    try:
        result = test_calendar_event_creation()
        test_results.append(("Calendar Event Creation", result))
        success &= result
    except Exception as e:
        print(f"❌ Event creation test crashed: {e}")
        test_results.append(("Calendar Event Creation", False))
        success = False
    
    # Test 3: Service Initialization
    try:
        result = test_calendar_service_init()
        test_results.append(("Calendar Service Init", result))
        success &= result
    except Exception as e:
        print(f"❌ Service init test crashed: {e}")
        test_results.append(("Calendar Service Init", False))
        success = False
    
    # Test 4: Intent Processing
    try:
        result = test_calendar_intent_processor()
        test_results.append(("Calendar Intent Processing", result))
        success &= result
    except Exception as e:
        print(f"❌ Intent processing test crashed: {e}")
        test_results.append(("Calendar Intent Processing", False))
        success = False
    
    # Test 5: Availability
    try:
        result = test_calendar_availability()
        test_results.append(("Calendar Availability", result))
        success &= result
    except Exception as e:
        print(f"❌ Availability test crashed: {e}")
        test_results.append(("Calendar Availability", False))
        success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Basic Calendar Integration Test Summary")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    
    if success:
        print("\n🎉 Google Calendar integration basic functionality is working!")
        print("📝 Day 9: Google Calendar Integration - COMPLETED")
        print("📋 Next steps:")
        print("   • Set up Google Cloud Console project")
        print("   • Create OAuth 2.0 credentials")
        print("   • Test with actual Google Calendar API")
    else:
        print("\n⚠️  Some tests failed - review implementation")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)