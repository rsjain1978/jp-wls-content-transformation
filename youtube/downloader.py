import os
from pathlib import Path
import requests
from termcolor import colored
from pytube import YouTube

class YouTubeDownloader:
    """Class to handle YouTube video/audio downloads"""
    
    def __init__(self):
        self.static_dir = Path("static")
        self.uploads_dir = self.static_dir / "uploads"
        self.thumbnails_dir = self.static_dir / "thumbnails"
        
        # Ensure directories exist
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    async def download_thumbnail(self, video_id: str) -> str:
        """Download video thumbnail"""
        try:
            thumbnail_path = f"static/thumbnails/{video_id}.jpg"
            if os.path.exists(thumbnail_path):
                return f"/static/thumbnails/{video_id}.jpg"

            # Try different thumbnail resolutions
            thumbnail_options = [
                f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                f"https://img.youtube.com/vi/{video_id}/sddefault.jpg",
                f"https://img.youtube.com/vi/{video_id}/default.jpg"
            ]
            
            for thumb_url in thumbnail_options:
                response = requests.get(thumb_url)
                if response.status_code == 200 and len(response.content) > 1000:
                    with open(thumbnail_path, 'wb') as f:
                        f.write(response.content)
                    return f"/static/thumbnails/{video_id}.jpg"
            
            raise Exception("No suitable thumbnail found")
            
        except Exception as e:
            print(colored(f"Error downloading thumbnail: {str(e)}", "red"))
            raise

    async def download_audio(self, video_id: str) -> str:
        """Download video audio"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            yt = YouTube(url)
            yt.bypass_age_gate()
            
            # Get highest quality audio stream
            audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
            if not audio_streams:
                raise Exception("No audio streams available")
            
            audio_stream = audio_streams[0]
            
            # Download to temporary file
            audio_path = f"static/uploads/{video_id}.mp4"
            audio_stream.download(output_path="static/uploads", filename=f"{video_id}.mp4")
            
            if not os.path.exists(audio_path):
                raise Exception("Failed to download audio file")
            
            return audio_path
            
        except Exception as e:
            print(colored(f"Error downloading audio: {str(e)}", "red"))
            raise 