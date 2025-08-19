#!/usr/bin/env python3
"""
Google Calendar Integration Service
Day 9 Task 9.1: Google Calendar API Setup & Management
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from dotenv import load_dotenv

# Load environment variables from .env file (look in parent directory)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

@dataclass
class CalendarEvent:
    """Calendar event data structure"""
    id: Optional[str] = None
    summary: str = ""
    description: str = ""
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    location: str = ""
    attendees: List[str] = None
    status: str = "confirmed"  # confirmed, tentative, cancelled
    recurring: bool = False
    recurrence_rule: Optional[str] = None
    
    def __post_init__(self):
        if self.attendees is None:
            self.attendees = []

@dataclass
class CalendarAvailability:
    """Calendar availability information"""
    start_time: datetime
    end_time: datetime
    is_busy: bool
    event_summary: Optional[str] = None

class GoogleCalendarService:
    """Google Calendar API service implementation"""
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.credentials = None
        
        # Check if we should use environment variables (production mode)
        self.use_env_vars = os.getenv('GOOGLE_CLIENT_ID') is not None
        
        if self.use_env_vars:
            logger.info("Using environment variables for Google Calendar authentication")
            self.client_id = os.getenv('GOOGLE_CLIENT_ID')
            self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            
            if not self.client_id or not self.client_secret:
                raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables")
        else:
            logger.info("Using credentials.json file for Google Calendar authentication")
        
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API using OAuth 2.0"""
        try:
            if self.use_env_vars:
                return self._authenticate_with_env_vars()
            else:
                return self._authenticate_with_credentials_file()
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _authenticate_with_env_vars(self) -> bool:
        """Authenticate using environment variables (development/production mode)"""
        try:
            # For development: use environment variables with InstalledAppFlow
            # This allows testing OAuth flow without credentials.json file
            
            # Create client config from environment variables
            client_config = {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"]
                }
            }
            
            # Load existing credentials if available
            if os.path.exists(self.token_file):
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_file, SCOPES
                )
            
            # If no valid credentials are available, request authorization
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.credentials.refresh(Request())
                else:
                    logger.info("Starting OAuth 2.0 flow with environment variables")
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
                    
                logger.info("Authentication successful with environment variables")
            
            # Build the Calendar service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
            
        except Exception as e:
            logger.error(f"Environment variable authentication failed: {e}")
            return False
    
    def _authenticate_with_credentials_file(self) -> bool:
        """Authenticate using credentials.json file (development mode)"""
        try:
            # Load existing credentials
            if os.path.exists(self.token_file):
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_file, SCOPES
                )
            
            # If no valid credentials are available, request authorization
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.credentials.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file not found: {self.credentials_file}")
                        return False
                    
                    logger.info("Starting OAuth 2.0 flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
                    
                logger.info("Authentication successful")
            
            # Build the Calendar service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
            
        except Exception as e:
            logger.error(f"Credentials file authentication failed: {e}")
            return False
    
    def create_event(self, event: CalendarEvent, calendar_id: str = 'primary') -> Optional[str]:
        """Create a new calendar event"""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            # Build event body
            event_body = {
                'summary': event.summary,
                'description': event.description,
                'location': event.location,
                'start': {
                    'dateTime': event.start_datetime.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'end': {
                    'dateTime': event.end_datetime.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'status': event.status
            }
            
            # Add attendees if provided
            if event.attendees:
                event_body['attendees'] = [{'email': email} for email in event.attendees]
            
            # Add recurrence if specified
            if event.recurring and event.recurrence_rule:
                event_body['recurrence'] = [event.recurrence_rule]
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()
            
            event_id = created_event.get('id')
            logger.info(f"Calendar event created: {event_id}")
            return event_id
            
        except HttpError as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating event: {e}")
            return None
    
    def get_events(self, start_time: datetime, end_time: datetime, 
                   calendar_id: str = 'primary', max_results: int = 50) -> List[CalendarEvent]:
        """Get events within a time range"""
        try:
            if not self.service:
                if not self.authenticate():
                    return []
            
            # Query events
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Convert to CalendarEvent objects
            calendar_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse datetime strings
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                calendar_event = CalendarEvent(
                    id=event.get('id'),
                    summary=event.get('summary', ''),
                    description=event.get('description', ''),
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    location=event.get('location', ''),
                    status=event.get('status', 'confirmed'),
                    attendees=[attendee.get('email', '') for attendee in event.get('attendees', [])]
                )
                calendar_events.append(calendar_event)
            
            logger.info(f"Retrieved {len(calendar_events)} events")
            return calendar_events
            
        except HttpError as e:
            logger.error(f"Failed to get calendar events: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting events: {e}")
            return []
    
    def update_event(self, event_id: str, event: CalendarEvent, 
                     calendar_id: str = 'primary') -> bool:
        """Update an existing calendar event"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False
            
            # Get existing event
            existing_event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields
            if event.summary:
                existing_event['summary'] = event.summary
            if event.description:
                existing_event['description'] = event.description
            if event.location:
                existing_event['location'] = event.location
            if event.start_datetime:
                existing_event['start'] = {
                    'dateTime': event.start_datetime.isoformat(),
                    'timeZone': 'Asia/Seoul',
                }
            if event.end_datetime:
                existing_event['end'] = {
                    'dateTime': event.end_datetime.isoformat(),
                    'timeZone': 'Asia/Seoul',
                }
            if event.attendees:
                existing_event['attendees'] = [{'email': email} for email in event.attendees]
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=existing_event
            ).execute()
            
            logger.info(f"Calendar event updated: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to update calendar event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating event: {e}")
            return False
    
    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """Delete a calendar event"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False
            
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Calendar event deleted: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to delete calendar event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting event: {e}")
            return False
    
    def check_availability(self, start_time: datetime, end_time: datetime,
                          calendar_id: str = 'primary') -> List[CalendarAvailability]:
        """Check availability within a time range"""
        try:
            events = self.get_events(start_time, end_time, calendar_id)
            
            # Create availability blocks
            availability = []
            current_time = start_time
            
            for event in events:
                # Add free time before event if exists
                if current_time < event.start_datetime:
                    availability.append(CalendarAvailability(
                        start_time=current_time,
                        end_time=event.start_datetime,
                        is_busy=False
                    ))
                
                # Add busy time for event
                availability.append(CalendarAvailability(
                    start_time=event.start_datetime,
                    end_time=event.end_datetime,
                    is_busy=True,
                    event_summary=event.summary
                ))
                
                current_time = max(current_time, event.end_datetime)
            
            # Add remaining free time
            if current_time < end_time:
                availability.append(CalendarAvailability(
                    start_time=current_time,
                    end_time=end_time,
                    is_busy=False
                ))
            
            return availability
            
        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            return []
    
    def find_available_slot(self, duration_hours: float, 
                          preferred_start: datetime, 
                          preferred_end: datetime,
                          calendar_id: str = 'primary') -> Optional[datetime]:
        """Find the next available time slot of specified duration"""
        try:
            availability = self.check_availability(preferred_start, preferred_end, calendar_id)
            duration_delta = timedelta(hours=duration_hours)
            
            for block in availability:
                if not block.is_busy:
                    slot_duration = block.end_time - block.start_time
                    if slot_duration >= duration_delta:
                        return block.start_time
            
            logger.info(f"No available slot found for {duration_hours} hours")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find available slot: {e}")
            return None

class CalendarIntentProcessor:
    """Process calendar-related intents and map to calendar operations"""
    
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        
    def process_create_event_intent(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process create_event intent"""
        try:
            # Extract required information
            summary = entities.get('item_name', 'New Event')
            start_time_str = entities.get('date_time')
            duration = entities.get('duration', 1.0)  # Default 1 hour
            location = entities.get('location', '')
            description = entities.get('description', '')
            
            if not start_time_str:
                return {
                    'success': False,
                    'message': '일정 시작 시간을 알려주세요.',
                    'requires_confirmation': True
                }
            
            # Parse start time (simplified - in real implementation, use proper datetime parsing)
            try:
                start_datetime = datetime.fromisoformat(start_time_str)
            except:
                return {
                    'success': False,
                    'message': '시간 형식을 이해할 수 없습니다. 다시 말씀해 주세요.'
                }
            
            end_datetime = start_datetime + timedelta(hours=float(duration))
            
            # Create event object
            event = CalendarEvent(
                summary=summary,
                description=description,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                location=location
            )
            
            # Create the event
            event_id = self.calendar_service.create_event(event)
            
            if event_id:
                return {
                    'success': True,
                    'message': f'일정 "{summary}"이(가) {start_datetime.strftime("%m월 %d일 %H:%M")}에 등록되었습니다.',
                    'event_id': event_id
                }
            else:
                return {
                    'success': False,
                    'message': '일정 생성에 실패했습니다. 다시 시도해 주세요.'
                }
                
        except Exception as e:
            logger.error(f"Failed to process create_event intent: {e}")
            return {
                'success': False,
                'message': '일정 생성 중 오류가 발생했습니다.'
            }
    
    def process_query_event_intent(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process query_event intent"""
        try:
            # Extract time range
            date_str = entities.get('date_time')
            
            if not date_str:
                # Default to today if no date specified
                start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(days=1)
                time_desc = "오늘"
            else:
                # Parse the date (simplified)
                try:
                    query_date = datetime.fromisoformat(date_str.split('T')[0])
                    start_time = query_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(days=1)
                    time_desc = query_date.strftime("%m월 %d일")
                except:
                    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(days=1)
                    time_desc = "오늘"
            
            # Get events
            events = self.calendar_service.get_events(start_time, end_time)
            
            if not events:
                return {
                    'success': True,
                    'message': f'{time_desc} 일정이 없습니다.',
                    'events': []
                }
            
            # Format event list
            event_list = []
            message_parts = [f'{time_desc} 일정:']
            
            for event in events:
                start_str = event.start_datetime.strftime("%H:%M")
                event_info = f"• {start_str} {event.summary}"
                if event.location:
                    event_info += f" ({event.location})"
                message_parts.append(event_info)
                event_list.append({
                    'id': event.id,
                    'summary': event.summary,
                    'start_time': event.start_datetime.isoformat(),
                    'location': event.location
                })
            
            return {
                'success': True,
                'message': '\n'.join(message_parts),
                'events': event_list
            }
            
        except Exception as e:
            logger.error(f"Failed to process query_event intent: {e}")
            return {
                'success': False,
                'message': '일정 조회 중 오류가 발생했습니다.'
            }
    
    def process_update_event_intent(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process update_event intent"""
        try:
            # This would require more complex logic to identify which event to update
            # For now, return a placeholder response
            return {
                'success': False,
                'message': '일정 수정 기능은 아직 구현 중입니다.',
                'requires_confirmation': True
            }
            
        except Exception as e:
            logger.error(f"Failed to process update_event intent: {e}")
            return {
                'success': False,
                'message': '일정 수정 중 오류가 발생했습니다.'
            }
    
    def process_cancel_event_intent(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process cancel_event intent"""
        try:
            # This would require event identification logic
            return {
                'success': False,
                'message': '일정 취소 기능은 아직 구현 중입니다.',
                'requires_confirmation': True
            }
            
        except Exception as e:
            logger.error(f"Failed to process cancel_event intent: {e}")
            return {
                'success': False,
                'message': '일정 취소 중 오류가 발생했습니다.'
            }
    
    def get_events_by_date(self, target_date):
        """Get calendar events for a specific date"""
        try:
            # This is a placeholder implementation
            # In a real system, this would integrate with Google Calendar API
            # For now, return empty list since calendar integration is not fully implemented
            return []
        except Exception as e:
            logger.error(f"Failed to get events by date: {e}")
            return []

# Global calendar processor instance
calendar_processor = CalendarIntentProcessor()

def get_calendar_processor() -> CalendarIntentProcessor:
    """Get the global calendar processor instance"""
    return calendar_processor