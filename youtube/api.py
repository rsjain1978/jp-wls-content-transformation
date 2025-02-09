import os
from typing import Dict, Any
from termcolor import colored
import re
from googleapiclient.discovery import build
from dotenv import load_dotenv
from pytube import YouTube
import isodate

load_dotenv()

# Initialize YouTube API client
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY) if YOUTUBE_API_KEY else None

class YouTubeAPI:
    """Class to handle YouTube Data API operations"""
    
    @staticmethod
    async def get_video_details(video_id: str) -> Dict[str, Any]:
        """Get video details using YouTube Data API"""
        try:
            if not youtube:
                raise Exception("YouTube API key not configured")

            request = youtube.videos().list(
                part="snippet,contentDetails",
                id=video_id
            )
            response = request.execute()

            if not response['items']:
                raise Exception(f"No video found with ID: {video_id}")

            video_info = response['items'][0]['snippet']
            duration = response['items'][0]['contentDetails']['duration']  # Returns in ISO 8601 format
            
            # Convert duration from ISO 8601 format to minutes:seconds
            duration_obj = isodate.parse_duration(duration)
            total_seconds = int(duration_obj.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            formatted_duration = f"{minutes}:{seconds:02d}"

            return {
                'title': video_info['title'],
                'publish_date': video_info['publishedAt'].split('T')[0],
                'duration': formatted_duration
            }
        except Exception as e:
            print(colored(f"Error getting video details from API: {str(e)}", "red"))
            return None

    @staticmethod
    async def get_video_captions(video_id: str) -> str:
        """Get video captions using pytube"""
        try:
            print(colored(f"Attempting to fetch captions for video {video_id} using pytube...", "yellow"))
            url = f"https://www.youtube.com/watch?v={video_id}"
            yt = YouTube(url)
            
            # Get all caption tracks
            captions = yt.captions
            
            # Try to get English captions first
            caption_track = None
            for lang_code in ['en', 'a.en']:  # Try both standard English and auto-generated English
                if lang_code in captions:
                    caption_track = captions[lang_code]
                    break
            
            # If no English captions found, try to get any available captions
            if not caption_track and captions:
                caption_track = list(captions.values())[0]
            
            if not caption_track:
                print(colored("No captions available for this video", "yellow"))
                return None
            
            # Get the caption track as XML
            xml_captions = caption_track.xml_captions
            
            # Clean up the captions (remove XML tags and timestamps)
            clean_text = re.sub(r'<[^>]+>', '', xml_captions)
            clean_text = '\n'.join(line.strip() for line in clean_text.split('\n') if line.strip())
            
            return clean_text
            
        except Exception as e:
            print(colored(f"Error getting captions: {str(e)}", "red"))
            return None 