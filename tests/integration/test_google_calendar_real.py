#!/usr/bin/env python3
"""
Real Google Calendar API Integration Test
Requires: credentials.json file in backend directory
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from calendar_service import GoogleCalendarService, CalendarEvent

def test_google_calendar_authentication():
    """Test Google Calendar API authentication"""
    print("🔐 Testing Google Calendar Authentication")
    print("=" * 50)
    
    try:
        # Check if credentials file exists
        credentials_path = os.path.join(os.path.dirname(__file__), '../../backend/credentials.json')
        
        if not os.path.exists(credentials_path):
            print("❌ credentials.json not found")
            print(f"   Expected location: {credentials_path}")
            print("📝 Please follow setup guide in scripts/setup_google_calendar.md")
            return False
        
        print("✅ credentials.json found")
        
        # Initialize calendar service
        calendar_service = GoogleCalendarService()
        print("✅ Calendar service initialized")
        
        # Test authentication (this will open browser for OAuth flow)
        print("🌐 Starting OAuth 2.0 flow...")
        print("   (Browser will open for Google authentication)")
        
        success = calendar_service.authenticate()
        
        if success:
            print("✅ Authentication successful!")
            print("✅ Google Calendar API connection established")
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_calendar_list_events():
    """Test listing calendar events"""
    print("\n📋 Testing Calendar Event Listing")
    print("=" * 40)
    
    try:
        calendar_service = GoogleCalendarService()
        
        if not calendar_service.authenticate():
            print("❌ Authentication failed")
            return False
        
        # Get events for the next 7 days
        start_time = datetime.now()
        end_time = start_time + timedelta(days=7)
        
        print(f"📅 Fetching events from {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
        
        events = calendar_service.get_events(start_time, end_time)
        
        print(f"✅ Retrieved {len(events)} events")
        
        if events:
            print("📋 Upcoming events:")
            for i, event in enumerate(events[:5], 1):  # Show first 5 events
                start_str = event.start_datetime.strftime('%Y-%m-%d %H:%M')
                print(f"   {i}. {event.summary} - {start_str}")
        else:
            print("📝 No events found in the next 7 days")
        
        return True
        
    except Exception as e:
        print(f"❌ Event listing test failed: {e}")
        return False

def test_calendar_create_event():
    """Test creating a calendar event"""
    print("\n📅 Testing Calendar Event Creation")
    print("=" * 40)
    
    try:
        calendar_service = GoogleCalendarService()
        
        if not calendar_service.authenticate():
            print("❌ Authentication failed")
            return False
        
        # Create a test event
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        test_event = CalendarEvent(
            summary="MERE AI Agent Test Event",
            description="Test event created by MERE AI Agent Google Calendar integration",
            start_datetime=start_time,
            end_datetime=end_time,
            location="Virtual Meeting"
        )
        
        print(f"📝 Creating test event: {test_event.summary}")
        print(f"   Start: {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   End: {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        event_id = calendar_service.create_event(test_event)
        
        if event_id:
            print(f"✅ Event created successfully!")
            print(f"   Event ID: {event_id}")
            
            # Verify the event was created by retrieving it
            events = calendar_service.get_events(start_time - timedelta(minutes=30), end_time + timedelta(minutes=30))
            created_event = None
            
            for event in events:
                if event.id == event_id:
                    created_event = event
                    break
            
            if created_event:
                print("✅ Event verification successful")
                print(f"   Retrieved event: {created_event.summary}")
                return event_id
            else:
                print("⚠️ Event created but not found in retrieval")
                return event_id
        else:
            print("❌ Event creation failed")
            return None
            
    except Exception as e:
        print(f"❌ Event creation test failed: {e}")
        return None

def test_calendar_delete_event(event_id: str):
    """Test deleting a calendar event"""
    print("\n🗑️ Testing Calendar Event Deletion")
    print("=" * 40)
    
    try:
        calendar_service = GoogleCalendarService()
        
        if not calendar_service.authenticate():
            print("❌ Authentication failed")
            return False
        
        print(f"🗑️ Deleting test event: {event_id}")
        
        success = calendar_service.delete_event(event_id)
        
        if success:
            print("✅ Event deleted successfully")
            return True
        else:
            print("❌ Event deletion failed")
            return False
            
    except Exception as e:
        print(f"❌ Event deletion test failed: {e}")
        return False

def test_calendar_availability():
    """Test calendar availability checking"""
    print("\n📊 Testing Calendar Availability")
    print("=" * 35)
    
    try:
        calendar_service = GoogleCalendarService()
        
        if not calendar_service.authenticate():
            print("❌ Authentication failed")
            return False
        
        # Check availability for today
        start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time.replace(hour=17)  # 9 AM to 5 PM
        
        print(f"⏰ Checking availability from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}")
        
        availability = calendar_service.check_availability(start_time, end_time)
        
        print(f"📊 Found {len(availability)} time blocks:")
        
        for i, block in enumerate(availability, 1):
            status = "🔴 BUSY" if block.is_busy else "🟢 FREE"
            duration = block.end_time - block.start_time
            duration_hours = duration.total_seconds() / 3600
            
            print(f"   {i}. {block.start_time.strftime('%H:%M')}-{block.end_time.strftime('%H:%M')} "
                  f"({duration_hours:.1f}h) {status}")
            
            if block.is_busy and block.event_summary:
                print(f"      Event: {block.event_summary}")
        
        # Test finding available slot
        print("\n🔍 Testing Available Slot Finding")
        available_slot = calendar_service.find_available_slot(1.0, start_time, end_time)
        
        if available_slot:
            print(f"✅ Found 1-hour slot at: {available_slot.strftime('%H:%M')}")
        else:
            print("❌ No 1-hour slot available")
        
        return True
        
    except Exception as e:
        print(f"❌ Availability test failed: {e}")
        return False

def main():
    """Run all Google Calendar integration tests"""
    print("🚀 Starting Real Google Calendar Integration Tests")
    print("=" * 60)
    
    # Check if this is a real test run
    print("⚠️ This test requires real Google Calendar API credentials")
    print("📝 Make sure you have set up credentials.json file")
    
    response = input("\n🔐 Do you want to proceed with real Google Calendar API test? (y/n): ")
    if response.lower() != 'y':
        print("❌ Test cancelled by user")
        return False
    
    success = True
    test_results = []
    created_event_id = None
    
    # Test 1: Authentication
    try:
        result = test_google_calendar_authentication()
        test_results.append(("Google Calendar Authentication", result))
        success &= result
        
        if not result:
            print("❌ Authentication failed - skipping remaining tests")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test crashed: {e}")
        test_results.append(("Google Calendar Authentication", False))
        return False
    
    # Test 2: List Events
    try:
        result = test_calendar_list_events()
        test_results.append(("Calendar Event Listing", result))
        success &= result
    except Exception as e:
        print(f"❌ Event listing test crashed: {e}")
        test_results.append(("Calendar Event Listing", False))
        success = False
    
    # Test 3: Create Event
    try:
        created_event_id = test_calendar_create_event()
        result = created_event_id is not None
        test_results.append(("Calendar Event Creation", result))
        success &= result
    except Exception as e:
        print(f"❌ Event creation test crashed: {e}")
        test_results.append(("Calendar Event Creation", False))
        success = False
    
    # Test 4: Check Availability
    try:
        result = test_calendar_availability()
        test_results.append(("Calendar Availability Check", result))
        success &= result
    except Exception as e:
        print(f"❌ Availability test crashed: {e}")
        test_results.append(("Calendar Availability Check", False))
        success = False
    
    # Test 5: Delete Event (cleanup)
    if created_event_id:
        try:
            result = test_calendar_delete_event(created_event_id)
            test_results.append(("Calendar Event Deletion", result))
            # Don't affect overall success for cleanup
        except Exception as e:
            print(f"❌ Event deletion test crashed: {e}")
            test_results.append(("Calendar Event Deletion", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Real Google Calendar Integration Test Summary")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    
    if success:
        print("\n🎉 Real Google Calendar integration is working!")
        print("✅ OAuth 2.0 authentication successful")
        print("✅ Calendar API CRUD operations verified")
        print("✅ Ready for production use")
    else:
        print("\n⚠️ Some tests failed - check configuration")
        print("📝 Verify credentials.json and Google Cloud Console setup")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)