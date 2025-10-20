"""
Email service using SendGrid
"""

import httpx
from typing import Optional
from app.config import settings
from app.exceptions.custom_exceptions import ApiException
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.base_url = "https://api.sendgrid.com/v3"
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        plain_text_content: str,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Send email via SendGrid
        Returns True if successful, False otherwise
        """
        try:
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "subject": subject
                    }
                ],
                "from": {"email": "info@rentme.group"},
                "content": [
                    {
                        "type": "text/plain",
                        "value": plain_text_content
                    }
                ]
            }
            
            if html_content:
                payload["content"].append({
                    "type": "text/html",
                    "value": html_content
                })
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/mail/send",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 202:
                    logger.info(f"Email sent successfully to {to_email}")
                    return True
                else:
                    logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    async def send_contact_message(
        self, 
        subject: str, 
        message: str
    ) -> bool:
        """
        Send contact message to info@rentme.group
        """
        return await self.send_email(
            to_email="info@rentme.group",
            subject=subject,
            plain_text_content=message
        )
