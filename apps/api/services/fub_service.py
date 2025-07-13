"""Follow Up Boss API service for fetching lead data.

This module provides functionality for interacting with the Follow Up Boss API
to retrieve lead information, activities, and other CRM data.
"""

from typing import Optional

from loguru import logger

from auth import make_fub_api_request, AuthenticationError


class FubService:
    """Service for interacting with Follow Up Boss API."""
    
    def __init__(self):
        """Initialize the FUB service."""
        self.base_url = "https://api.followupboss.com/v1"
    
    async def get_lead_data(
        self,
        access_token: str,
        refresh_token: str,
        person_id: str
    ) -> dict:
        """Get comprehensive lead data from Follow Up Boss.
        
        Args:
            access_token: OAuth access token.
            refresh_token: OAuth refresh token.
            person_id: Follow Up Boss person ID.
            
        Returns:
            Dictionary containing person data and activities.
            
        Raises:
            AuthenticationError: If API requests fail.
        """
        try:
            # Get person details
            person_data, new_access_token, new_refresh_token = await make_fub_api_request(
                access_token,
                refresh_token,
                f"{self.base_url}/people/{person_id}"
            )
            
            # Get activities for this person
            activities_data, final_access_token, final_refresh_token = await make_fub_api_request(
                new_access_token,
                new_refresh_token,
                f"{self.base_url}/people/{person_id}/activities",
                params={"limit": 20, "sort": "-created"}
            )
            
            result = {
                "person": person_data,
                "activities": activities_data.get("activities", [])
            }
            
            # Include updated tokens if they changed
            if final_access_token != access_token:
                result["new_access_token"] = final_access_token
                result["new_refresh_token"] = final_refresh_token
            
            return result
            
        except AuthenticationError as e:
            logger.error(f"FUB API authentication error: {e}")
            raise
        except Exception as e:
            logger.error(f"FUB API error: {e}")
            raise AuthenticationError("Failed to fetch lead data")
    
    async def get_person_details(
        self,
        access_token: str,
        refresh_token: str,
        person_id: str
    ) -> tuple[dict, str, str]:
        """Get person details from Follow Up Boss.
        
        Args:
            access_token: OAuth access token.
            refresh_token: OAuth refresh token.
            person_id: Follow Up Boss person ID.
            
        Returns:
            Tuple of (person_data, new_access_token, new_refresh_token).
        """
        return await make_fub_api_request(
            access_token,
            refresh_token,
            f"{self.base_url}/people/{person_id}"
        )
    
    async def get_person_activities(
        self,
        access_token: str,
        refresh_token: str,
        person_id: str,
        limit: int = 20
    ) -> tuple[dict, str, str]:
        """Get activities for a person from Follow Up Boss.
        
        Args:
            access_token: OAuth access token.
            refresh_token: OAuth refresh token.
            person_id: Follow Up Boss person ID.
            limit: Maximum number of activities to retrieve.
            
        Returns:
            Tuple of (activities_data, new_access_token, new_refresh_token).
        """
        return await make_fub_api_request(
            access_token,
            refresh_token,
            f"{self.base_url}/people/{person_id}/activities",
            params={"limit": limit, "sort": "-created"}
        )
    
    async def create_note(
        self,
        access_token: str,
        refresh_token: str,
        person_id: str,
        note_content: str
    ) -> tuple[dict, str, str]:
        """Create a note for a person in Follow Up Boss.
        
        Args:
            access_token: OAuth access token.
            refresh_token: OAuth refresh token.
            person_id: Follow Up Boss person ID.
            note_content: Content of the note.
            
        Returns:
            Tuple of (note_data, new_access_token, new_refresh_token).
        """
        return await make_fub_api_request(
            access_token,
            refresh_token,
            f"{self.base_url}/people/{person_id}/notes",
            method="POST",
            json={"content": note_content}
        )
    
    async def get_account_info(
        self,
        access_token: str,
        refresh_token: str
    ) -> tuple[dict, str, str]:
        """Get account information from Follow Up Boss.
        
        Args:
            access_token: OAuth access token.
            refresh_token: OAuth refresh token.
            
        Returns:
            Tuple of (account_data, new_access_token, new_refresh_token).
        """
        return await make_fub_api_request(
            access_token,
            refresh_token,
            f"{self.base_url}/account"
        ) 