"""Chat service for handling AI conversations with OpenAI.

This module provides functionality for generating AI responses to user questions
about leads using OpenAI's GPT models with context from Follow Up Boss data.
"""

from typing import Optional

import openai
from loguru import logger
from sqlmodel import Session

from config import settings
from models import Account, ChatMessage
from utils import format_chat_response, get_cached_lead_data, cache_lead_data, summarize_lead_activities
from .fub_service import FubService


class ChatService:
    """Service for handling AI chat conversations."""
    
    def __init__(self):
        """Initialize the chat service."""
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.fub_service = FubService()
    
    async def generate_response(
        self,
        session: Session,
        account: Account,
        person_id: str,
        question: str
    ) -> str:
        """Generate AI response for a user question about a lead.
        
        Args:
            session: Database session.
            account: User account.
            person_id: Follow Up Boss person ID.
            question: User's question.
            
        Returns:
            Formatted AI response.
        """
        try:
            # Get lead data (cached or fresh)
            lead_data = await self._get_lead_context(account, person_id)
            
            # Generate AI response
            ai_response = await self._call_openai(question, lead_data)
            
            # Format response according to requirements
            formatted_response = format_chat_response(ai_response)
            
            # Save conversation to database
            if account.id:
                await self._save_conversation(session, account.id, person_id, question, formatted_response)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Chat response generation error: {e}")
            return "• Sorry, I encountered an error while processing your request.\n• Please try again or contact support if the issue persists."
    
    async def _get_lead_context(self, account: Account, person_id: str) -> str:
        """Get lead context data for AI prompt.
        
        Args:
            account: User account.
            person_id: Follow Up Boss person ID.
            
        Returns:
            Summarized lead context.
        """
        # Check cache first
        cached_data = await get_cached_lead_data(person_id)
        
        if cached_data:
            logger.info(f"Using cached lead data for person {person_id}")
            return cached_data.get('summary', 'No lead data available.')
        
        # Fetch fresh data from FUB
        try:
            lead_data = await self.fub_service.get_lead_data(
                account.access_token,
                account.refresh_token,
                person_id
            )
            
            # Update tokens if they were refreshed
            if lead_data.get('new_access_token'):
                account.access_token = lead_data['new_access_token']
                account.refresh_token = lead_data['new_refresh_token']
            
            # Summarize the data
            summary = self._create_lead_summary(lead_data.get('person', {}), lead_data.get('activities', []))
            
            # Cache the summary
            await cache_lead_data(person_id, {'summary': summary})
            
            return summary
            
        except Exception as e:
            logger.error(f"Error fetching lead data: {e}")
            return "Unable to retrieve lead information at this time."
    
    def _create_lead_summary(self, person_data: dict, activities: list) -> str:
        """Create a summary of lead data for AI context.
        
        Args:
            person_data: Person information from FUB.
            activities: Recent activities from FUB.
            
        Returns:
            Lead summary string.
        """
        name = person_data.get('name', 'Unknown')
        email = person_data.get('email', 'No email')
        phone = person_data.get('phone', 'No phone')
        source = person_data.get('source', 'Unknown source')
        
        # Summarize activities
        activity_summary = summarize_lead_activities(activities)
        
        return f"Lead: {name} ({email}, {phone}). Source: {source}. Recent activities: {activity_summary}"
    
    async def _call_openai(self, question: str, lead_context: str) -> str:
        """Call OpenAI API to generate response.
        
        Args:
            question: User's question.
            lead_context: Lead context information.
            
        Returns:
            AI response text.
        """
        system_prompt = """You are a helpful assistant for real estate professionals using Follow Up Boss CRM.
        
        Guidelines:
        - Provide concise, actionable advice about lead follow-up
        - Focus on the specific lead's context and recent activities
        - Suggest concrete next steps
        - Keep responses to 3 bullet points maximum
        - Be professional and sales-focused
        - If you don't have enough information, ask clarifying questions
        """
        
        user_prompt = f"""Lead Context: {lead_context}
        
        Question: {question}
        
        Please provide specific follow-up advice for this lead."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=128,
                temperature=0.6
            )
            
            return response.choices[0].message.content or "I'm sorry, I couldn't generate a response."
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _save_conversation(
        self,
        session: Session,
        account_id: int,
        person_id: str,
        question: str,
        response: str
    ) -> None:
        """Save conversation to database.
        
        Args:
            session: Database session.
            account_id: Account ID.
            person_id: Person ID.
            question: User question.
            response: AI response.
        """
        try:
            # Save user message
            user_message = ChatMessage(
                account_id=account_id,
                person_id=person_id,
                role="user",
                message=question
            )
            session.add(user_message)
            
            # Save assistant response
            assistant_message = ChatMessage(
                account_id=account_id,
                person_id=person_id,
                role="assistant",
                message=response
            )
            session.add(assistant_message)
            
            session.commit()
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            session.rollback() 