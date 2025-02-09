from typing import Dict, Any, List
from termcolor import colored
from pytube import Playlist
from .api import YouTubeAPI
from .downloader import YouTubeDownloader

class PlaylistProcessor:
    """Class to handle YouTube playlist processing"""
    
    def __init__(self):
        self.youtube_api = YouTubeAPI()
        self.downloader = YouTubeDownloader()

    async def process_playlist(self, playlist_url: str) -> List[Dict[str, Any]]:
        """Process YouTube playlist and get latest 15 videos"""
        try:
            print(colored("Processing YouTube playlist...", "cyan"))
            
            # Get playlist
            playlist = Playlist(playlist_url)
            video_ids = [url.split('v=')[1] for url in playlist.video_urls]
            
            # Get video details and sort by date
            videos_with_dates = []
            for video_id in video_ids:
                try:
                    api_details = await self.youtube_api.get_video_details(video_id)
                    if api_details:
                        videos_with_dates.append({
                            'video_id': video_id,
                            'details': api_details,
                            'url': f"https://www.youtube.com/watch?v={video_id}"
                        })
                except Exception as e:
                    print(colored(f"Error getting details for video {video_id}: {str(e)}", "red"))
                    continue
            
            # Sort by publish date and get latest 15
            videos_with_dates.sort(key=lambda x: x['details']['publish_date'], reverse=True)
            latest_videos = videos_with_dates[:15]
            
            # Process each video
            videos_info = []
            for video in latest_videos:
                try:
                    video_id = video['video_id']
                    thumbnail_path = await self.downloader.download_thumbnail(video_id)
                    
                    videos_info.append({
                        'video_id': video_id,
                        'title': video['details']['title'],
                        'thumbnail_path': thumbnail_path,
                        'publish_date': video['details']['publish_date'],
                        'url': video['url'],
                        'duration': video['details']['duration']
                    })
                    
                except Exception as e:
                    print(colored(f"Error processing video {video['url']}: {str(e)}", "red"))
                    continue
            
            return videos_info
            
        except Exception as e:
            print(colored(f"Error processing playlist: {str(e)}", "red"))
            raise 