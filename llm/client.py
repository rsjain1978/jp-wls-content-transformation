"""OpenAI client wrapper for LLM interactions"""

from openai import AsyncOpenAI
from termcolor import colored

class LLMClient:
    """Wrapper for OpenAI client with common functionality"""
    
    def __init__(self):
        self.client = AsyncOpenAI()
        
    async def generate_completion(self, system_prompt: str, user_content: str) -> str:
        """Generate completion using GPT-4"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(colored(f"Error in LLM completion: {str(e)}", "red"))
            raise 