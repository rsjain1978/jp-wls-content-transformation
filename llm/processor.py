"""Content processing functions using LLM"""

import os
from termcolor import colored
from .client import LLMClient
import logging
from pathlib import Path
import time
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
import json
from fastapi import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentProcessor:
    """Process content using LLM"""
    
    def __init__(self):
        self.llm = LLMClient()

    async def detect_language(self, text: str) -> str:
        """Detect the language of the text using GPT-4"""
        try:
            logger.info("Detecting text language...")
            response = await self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a language detection expert. Analyze the given text and return a JSON object with a 'language' field containing ONLY the language name in English (e.g., {'language': 'Japanese'}). Do not include any other text in your response."
                    },
                    {
                        "role": "user",
                        "content": text[:1000]  # Use first 1000 chars for detection
                    }
                ],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            detected_lang = result.get('language', 'English')
            logger.info(f"Detected language: {detected_lang}")
            return detected_lang
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            return "English"
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return "English"  # Default to English on error

    async def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target language using GPT-4"""
        try:
            logger.info(f"Translating text to {target_language}...")
            response = await self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate the following text to {target_language} and return a JSON object with a 'translation' field containing the translated text. Maintain the original formatting and ensure the translation is natural and fluent."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            translated_text = result.get('translation', text)
            logger.info("Translation completed")
            return translated_text
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response during translation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            raise

    async def generate_audio(self, text: str, voice: str) -> bytes:
        """Generate audio using OpenAI TTS with longform support"""
        try:
            logger.info("Generating audio with longform support...")
            
            # OpenAI TTS has a character limit, so we need to split long text
            MAX_CHARS = 4000  # OpenAI's TTS limit per request
            text_chunks = []
            
            # Split text into sentences and group them into chunks
            sentences = text.replace('\n', ' ').split('. ')
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence = sentence.strip() + '. '
                if current_length + len(sentence) > MAX_CHARS:
                    text_chunks.append(''.join(current_chunk))
                    current_chunk = [sentence]
                    current_length = len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_length += len(sentence)
            
            if current_chunk:
                text_chunks.append(''.join(current_chunk))
            
            logger.info(f"Split content into {len(text_chunks)} chunks for processing")
            
            # Generate audio for each chunk
            audio_chunks = []
            for i, chunk in enumerate(text_chunks, 1):
                logger.info(f"Processing chunk {i}/{len(text_chunks)}")
                response = await self.llm.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=chunk
                )
                audio_chunks.append(response.content)
            
            # Combine all audio chunks
            return b''.join(audio_chunks)
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise

    async def generate_podcast(self, file_path: str, target_language: str) -> str:
        """Generate podcast audio from document in specified language"""
        try:
            # Load document content using langchain
            logger.info(f"Loading document: {file_path}")
            
            if file_path.lower().endswith('.docx') or file_path.lower().endswith('.doc'):
                # Use Word document loader
                loader = UnstructuredWordDocumentLoader(file_path)
                doc = loader.load()
                content = ' '.join([page.page_content for page in doc])
            else:
                # For text files, read directly
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            logger.info("Document loaded successfully")

            try:
                # Detect the language of the content
                detected_language = await self.detect_language(content)
                
                # Translate if needed
                if detected_language.lower() != target_language.lower():
                    logger.info(f"Content is in {detected_language}, translating to {target_language}")
                    try:
                        content = await self.translate_text(content, target_language)
                    except Exception as e:
                        logger.error(f"Translation failed: {str(e)}")
                        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
                else:
                    logger.info(f"Content is already in {target_language}, no translation needed")
            except Exception as e:
                logger.error(f"Language processing failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Language processing failed: {str(e)}")
            
            # Create output directory if it doesn't exist
            os.makedirs("static/podcasts", exist_ok=True)
            
            # Generate unique output filename
            output_path = f"static/podcasts/podcast_{int(time.time())}.mp3"
            
            # Generate audio in target language
            logger.info(f"Generating podcast in {target_language}")
            
            # Select voice based on language
            voice = self._get_voice_for_language(target_language)
            
            # Generate audio with longform support
            audio_content = await self.generate_audio(content, voice)
            
            # Save the audio file
            with open(output_path, "wb") as f:
                f.write(audio_content)
            
            logger.info(f"Generated podcast saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating podcast: {str(e)}")
            raise

    def _get_voice_for_language(self, language: str) -> str:
        """Select appropriate voice based on target language"""
        # Map languages to voices that sound most natural for each
        voice_map = {
            "Japanese": "nova",
            "Chinese": "nova",
            "Korean": "nova",
            "English": "alloy",
            "Spanish": "shimmer",
            "French": "echo",
            "German": "onyx",
            "Italian": "shimmer",
            "Portuguese": "shimmer"
        }
        return voice_map.get(language, "alloy")  # Default to alloy if language not found 