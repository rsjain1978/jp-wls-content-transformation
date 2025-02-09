"""Content processing functions using LLM"""

from termcolor import colored
from .client import LLMClient
from prompts import TRANSCRIPT_CLEANING, TRANSLATION, TWEET_GENERATION, SUMMARY_GENERATION
import json

class ContentProcessor:
    """Process content using LLM"""
    
    def __init__(self):
        self.llm = LLMClient()
        
    async def clean_transcript(self, transcript: str) -> str:
        """Clean transcript using GPT-4 to make it more legible"""
        try:
            response = await self.llm.generate_completion(
                TRANSCRIPT_CLEANING,
                transcript
            )
            response_json = json.loads(response)
            return response_json['text']
        except Exception as e:
            print(colored(f"Error cleaning transcript: {str(e)}", "red"))
            raise
            
    async def translate_content(self, content: str, target_language: str) -> str:
        """Translate content to target language"""
        try:
            system_prompt = TRANSLATION.format(target_language=target_language)
            response = await self.llm.generate_completion(
                system_prompt,
                content
            )
            response_json = json.loads(response)
            return response_json['translation']
        except Exception as e:
            print(colored(f"Error translating content: {str(e)}", "red"))
            raise
            
    async def generate_tweet(self, content: str, target_language: str) -> str:
        """Generate and translate tweet from content"""
        try:
            # Generate tweet in English
            response = await self.llm.generate_completion(
                TWEET_GENERATION,
                content
            )
            response_json = json.loads(response)
            tweet = response_json['tweet']
            
            # Translate if needed
            if target_language.lower() != "english":
                tweet = await self.translate_content(tweet, target_language)
                
            return tweet
            
        except Exception as e:
            print(colored(f"Error generating tweet: {str(e)}", "red"))
            raise

    async def generate_summary(self, content: str, target_language: str) -> str:
        """Generate and translate summary"""
        try:
            # Generate summary in English
            response = await self.llm.generate_completion(
                SUMMARY_GENERATION,
                content
            )
            response_json = json.loads(response)
            summary = response_json['summary']
            
            # Translate if needed
            if target_language.lower() != "english":
                summary = await self.translate_content(summary, target_language)
                
            return summary
            
        except Exception as e:
            print(colored(f"Error generating summary: {str(e)}", "red"))
            raise 