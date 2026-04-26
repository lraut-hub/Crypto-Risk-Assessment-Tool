import os
import google.generativeai as genai
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GeminiService:
    """
    Wrapper for Google Gemini API to handle assistant reasoning.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")
        
        genai.configure(api_key=self.api_key)
        # Using a more robust model string
        self.model_name = 'gemini-1.5-flash'
        logger.info(f"Gemini Service configured for {self.model_name}.")

    async def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Sends a prompt to Gemini and returns the generated text.
        """
        try:
            full_content = f"{system_instruction}\n\nUSER QUERY: {prompt}" if system_instruction else prompt
            
            # Use gemini-1.5-flash if available, otherwise fallback to gemini-pro
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = await asyncio.to_thread(model.generate_content, full_content)
            except Exception:
                logger.warning("gemini-1.5-flash failed, falling back to gemini-pro")
                model = genai.GenerativeModel('gemini-pro')
                response = await asyncio.to_thread(model.generate_content, full_content)
            
            if response and response.text:
                return response.text
            return "No response generated."
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return "Assistant is currently updating. Please try again in 30 seconds."

# We need asyncio for the to_thread call
import asyncio
