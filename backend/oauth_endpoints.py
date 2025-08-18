#!/usr/bin/env python3
"""
Google Calendar OAuth 2.0 Endpoints for Production
FastAPI endpoints for handling OAuth flow
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging

from calendar_service_production import get_production_calendar_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/google", tags=["google-oauth"])

# OAuth response models
class AuthUrlResponse(BaseModel):
    auth_url: str
    message: str

class CallbackRequest(BaseModel):
    code: str
    state: str

@router.get("/authorize/{user_id}")
async def initiate_google_auth(user_id: str):
    """Initiate Google Calendar OAuth for a specific user"""
    try:
        calendar_service = get_production_calendar_service()
        auth_url = calendar_service.generate_auth_url(user_id)
        
        return AuthUrlResponse(
            auth_url=auth_url,
            message="Please visit the auth_url to authorize Google Calendar access"
        )
        
    except Exception as e:
        logger.error(f"Failed to initiate auth for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate Google authorization")

@router.get("/callback")
async def handle_oauth_callback(
    code: str = None,
    state: str = None,
    error: str = None
):
    """Handle Google OAuth callback"""
    try:
        if error:
            logger.error(f"OAuth error: {error}")
            return HTMLResponse(
                content=f"""
                <html>
                    <body>
                        <h2>❌ Authorization Failed</h2>
                        <p>Error: {error}</p>
                        <p>Please try again or contact support.</p>
                    </body>
                </html>
                """,
                status_code=400
            )
        
        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing authorization code or state")
        
        # Extract user_id from state (simplified - in production decode properly)
        calendar_service = get_production_calendar_service()
        
        # For now, we need to extract user_id from state or pass it differently
        # In production, encode user_id in state parameter
        user_id = "temp_user"  # This should be extracted from state
        
        success = calendar_service.handle_oauth_callback(user_id, code, state)
        
        if success:
            return HTMLResponse(
                content="""
                <html>
                    <body>
                        <h2>✅ Authorization Successful!</h2>
                        <p>Google Calendar access has been granted successfully.</p>
                        <p>You can now close this window and return to the MERE AI Agent app.</p>
                        <script>
                            // Auto-close window after 3 seconds
                            setTimeout(() => {
                                window.close();
                            }, 3000);
                        </script>
                    </body>
                </html>
                """
            )
        else:
            return HTMLResponse(
                content="""
                <html>
                    <body>
                        <h2>❌ Authorization Failed</h2>
                        <p>Failed to process the authorization. Please try again.</p>
                    </body>
                </html>
                """,
                status_code=500
            )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process OAuth callback")

@router.post("/revoke/{user_id}")
async def revoke_google_access(user_id: str):
    """Revoke Google Calendar access for a user"""
    try:
        calendar_service = get_production_calendar_service()
        success = calendar_service.revoke_user_access(user_id)
        
        if success:
            return {"message": "Google Calendar access revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="No active authorization found for user")
        
    except Exception as e:
        logger.error(f"Failed to revoke access for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke Google Calendar access")

@router.get("/status/{user_id}")
async def check_auth_status(user_id: str):
    """Check Google Calendar authorization status for a user"""
    try:
        calendar_service = get_production_calendar_service()
        service = calendar_service.get_calendar_service(user_id)
        
        if service:
            return {
                "authorized": True,
                "message": "User has valid Google Calendar authorization"
            }
        else:
            return {
                "authorized": False,
                "message": "User needs to authorize Google Calendar access"
            }
        
    except Exception as e:
        logger.error(f"Failed to check auth status for user {user_id}: {e}")
        return {
            "authorized": False,
            "message": "Failed to check authorization status"
        }