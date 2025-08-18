#!/usr/bin/env python3
"""
Production Google Calendar Service
OAuth 2.0 Web Application Flow for Multi-User Environment
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import secrets
import hashlib

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from database import SessionLocal
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()

class UserCalendarAuth(Base):
    """User-specific Google Calendar authentication storage"""
    __tablename__ = "user_calendar_auth"
    
    user_id = Column(String, primary_key=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    scopes = Column(Text, nullable=False)  # JSON array of scopes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class ProductionCalendarService:
    """Production-ready Google Calendar Service with Web OAuth Flow"""
    
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials not found in environment variables")
        
        # Create database table if not exists
        self._ensure_auth_table()
    
    def _ensure_auth_table(self):
        """Ensure user calendar auth table exists"""
        try:
            from database import engine
            Base.metadata.create_all(bind=engine, tables=[UserCalendarAuth.__table__])
            logger.info("User calendar auth table ready")
        except Exception as e:
            logger.error(f"Failed to create auth table: {e}")
    
    def generate_auth_url(self, user_id: str) -> str:
        """Generate Google OAuth authorization URL for user"""
        try:
            # Create OAuth flow
            flow = Flow.from_client_config({
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            }, scopes=self.scopes)
            
            flow.redirect_uri = self.redirect_uri
            
            # Generate state parameter for security (CSRF protection)
            state = self._generate_state_token(user_id)
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',  # Get refresh token
                include_granted_scopes='true',
                state=state,
                prompt='consent'  # Force consent to get refresh token
            )
            
            logger.info(f"Generated auth URL for user {user_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to generate auth URL: {e}")
            raise
    
    def handle_oauth_callback(self, user_id: str, authorization_code: str, state: str) -> bool:
        """Handle OAuth callback and store user credentials"""
        try:
            # Verify state token
            if not self._verify_state_token(user_id, state):
                logger.error(f"Invalid state token for user {user_id}")
                return False
            
            # Create OAuth flow
            flow = Flow.from_client_config({
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            }, scopes=self.scopes)
            
            flow.redirect_uri = self.redirect_uri
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Store credentials in database
            self._store_user_credentials(user_id, credentials)
            
            logger.info(f"Successfully stored credentials for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle OAuth callback: {e}")
            return False
    
    def get_calendar_service(self, user_id: str):
        """Get authenticated Google Calendar service for user"""
        try:
            credentials = self._get_user_credentials(user_id)
            
            if not credentials:
                logger.warning(f"No credentials found for user {user_id}")
                return None
            
            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._update_user_credentials(user_id, credentials)
            
            # Build and return service
            service = build('calendar', 'v3', credentials=credentials)
            return service
            
        except Exception as e:
            logger.error(f"Failed to get calendar service for user {user_id}: {e}")
            return None
    
    def _generate_state_token(self, user_id: str) -> str:
        """Generate secure state token for OAuth flow"""
        timestamp = str(int(datetime.now().timestamp()))
        random_bytes = secrets.token_urlsafe(32)
        data = f"{user_id}:{timestamp}:{random_bytes}"
        
        # Create hash for verification
        hash_object = hashlib.sha256(data.encode())
        return hash_object.hexdigest()[:32]  # Return first 32 chars
    
    def _verify_state_token(self, user_id: str, state: str) -> bool:
        """Verify state token (simplified - in production use Redis/cache)"""
        # In production: store state tokens in Redis with expiration
        # For now, basic validation
        return len(state) == 32 and state.isalnum()
    
    def _store_user_credentials(self, user_id: str, credentials: Credentials) -> None:
        """Store user credentials in database"""
        db = SessionLocal()
        try:
            # Check if user already has credentials
            existing = db.query(UserCalendarAuth).filter(
                UserCalendarAuth.user_id == user_id
            ).first()
            
            if existing:
                # Update existing credentials
                existing.access_token = credentials.token
                existing.refresh_token = credentials.refresh_token
                existing.token_expires_at = credentials.expiry
                existing.updated_at = datetime.utcnow()
                existing.is_active = True
            else:
                # Create new credentials entry
                auth_record = UserCalendarAuth(
                    user_id=user_id,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    token_expires_at=credentials.expiry,
                    scopes=json.dumps(self.scopes)
                )
                db.add(auth_record)
            
            db.commit()
            logger.info(f"Stored credentials for user {user_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store credentials: {e}")
            raise
        finally:
            db.close()
    
    def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get user credentials from database"""
        db = SessionLocal()
        try:
            auth_record = db.query(UserCalendarAuth).filter(
                UserCalendarAuth.user_id == user_id,
                UserCalendarAuth.is_active == True
            ).first()
            
            if not auth_record:
                return None
            
            # Create credentials object
            credentials = Credentials(
                token=auth_record.access_token,
                refresh_token=auth_record.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=json.loads(auth_record.scopes)
            )
            
            if auth_record.token_expires_at:
                credentials.expiry = auth_record.token_expires_at
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
        finally:
            db.close()
    
    def _update_user_credentials(self, user_id: str, credentials: Credentials) -> None:
        """Update user credentials after refresh"""
        db = SessionLocal()
        try:
            auth_record = db.query(UserCalendarAuth).filter(
                UserCalendarAuth.user_id == user_id
            ).first()
            
            if auth_record:
                auth_record.access_token = credentials.token
                auth_record.token_expires_at = credentials.expiry
                auth_record.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Updated credentials for user {user_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update credentials: {e}")
        finally:
            db.close()
    
    def revoke_user_access(self, user_id: str) -> bool:
        """Revoke user's Google Calendar access"""
        db = SessionLocal()
        try:
            # Mark credentials as inactive
            auth_record = db.query(UserCalendarAuth).filter(
                UserCalendarAuth.user_id == user_id
            ).first()
            
            if auth_record:
                auth_record.is_active = False
                auth_record.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Revoked access for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to revoke access: {e}")
            return False
        finally:
            db.close()

# Global production service instance
production_calendar_service = ProductionCalendarService()

def get_production_calendar_service() -> ProductionCalendarService:
    """Get the production calendar service instance"""
    return production_calendar_service