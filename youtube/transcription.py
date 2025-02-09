import os
from typing import Dict, List
from termcolor import colored
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

class TranscriptionProcessor:
    """Class to handle video transcription using YouTube Transcript API"""
    
    async def process_videos(self, video_ids: List[str]) -> Dict[str, str]:
        """Process and get transcriptions for selected videos using YouTube Transcript API"""
        try:
            print(colored("Getting transcriptions for selected videos...", "cyan"))
            
            transcriptions = {}
            for video_id in video_ids:
                try:
                    print(colored(f"Fetching captions for video {video_id}...", "yellow"))
                    
                    # Get transcript with fallback to auto-generated if available
                    try:
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        
                        # Try to get English transcript first
                        try:
                            transcript = transcript_list.find_transcript(['en'])
                        except NoTranscriptFound:
                            # If no English, try to get any transcript and translate to English
                            transcript = transcript_list.find_manually_created_transcript()
                            transcript = transcript.translate('en')
                        
                        # Get the actual transcript text
                        transcript_pieces = transcript.fetch()
                        
                        # Combine all pieces into one text
                        full_transcript = "\n".join(
                            f"[{int(piece['start'])}s] {piece['text']}"
                            for piece in transcript_pieces
                        )
                        
                        transcriptions[video_id] = full_transcript
                        print(colored(f"Successfully fetched captions for video {video_id}", "green"))
                        
                    except TranscriptsDisabled:
                        error_msg = "Transcripts are disabled for this video"
                        print(colored(f"Error: {error_msg}", "red"))
                        transcriptions[video_id] = f"Error: {error_msg}"
                        
                    except NoTranscriptFound:
                        error_msg = "No transcripts found for this video"
                        print(colored(f"Error: {error_msg}", "red"))
                        transcriptions[video_id] = f"Error: {error_msg}"
                    
                except Exception as e:
                    print(colored(f"Error getting captions for video {video_id}: {str(e)}", "red"))
                    transcriptions[video_id] = f"Error: {str(e)}"
                    continue
            
            return transcriptions
            
        except Exception as e:
            print(colored(f"Error processing videos: {str(e)}", "red"))
            raise 