import os
import logging
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GroqService:
    """
    Wrapper for Groq Cloud API to handle assistant reasoning using Llama 3.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.error("GROQ_API_KEY not found in environment.")
            # We don't raise here to allow the server to boot even if key is missing (for UI testing)
        
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        # Using Llama 3.3 70B (latest recommended replacement)
        self.model = "llama-3.3-70b-versatile"
        logger.info(f"Groq Service initialized with model: {self.model}")

    async def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Sends a prompt to Groq and returns the generated text.
        """
        if not self.client:
            return "Assistant is offline. Please configure GROQ_API_KEY."

        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            
            messages.append({"role": "user", "content": prompt})

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2, # Low temperature for factual precision
                max_tokens=500
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return "I'm sorry, I've encountered an issue with the Groq service. Please try again soon."
