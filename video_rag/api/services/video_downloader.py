import os
import sys
import subprocess
import django
from django.conf import settings
import logging
from typing import Optional, Tuple

# Setup Django environment
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "video_rag.settings")
django.setup()

class VideoDownloader:
    BASE_DIR = settings.BASE_DIR

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.join(self.BASE_DIR, 'uploads', 'videos')
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def download_video_and_audio(self, url: str) -> Tuple[str, str]:
        """
        Download both video and audio from the given URL.
        
        :param url: URL of the video to download
        :return: Tuple containing paths to the downloaded video and audio files
        """
        try:
            video_output_template = os.path.join(self.output_dir, '%(title)s.%(ext)s')
            audio_output_template = os.path.join(self.output_dir, '%(title)s.%(ext)s')
            
            cmd = [
                "yt-dlp",
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "-o", video_output_template,
                "--extract-audio",
                "--audio-format", "m4a",
                "--audio-quality", "0",
                "--keep-video",
                "--no-playlist",
                url,
            ]

            self.logger.info(f"Downloading video and audio from {url}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            video_path = None
            audio_path = None

            # Extract the output filenames from yt-dlp's output
            for line in result.stdout.split('\n'):
                if line.startswith('[download] Destination:'):
                    file_path = line.split(': ', 1)[1]
                    if file_path.endswith('.mp4'):
                        video_path = file_path
                    elif file_path.endswith('.m4a'):
                        audio_path = file_path

            if not video_path or not audio_path:
                raise Exception("Could not determine output filenames")

            return video_path, audio_path

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to download video and audio: {e}")
            self.logger.error(f"Command output: {e.output}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vd = VideoDownloader()
    try:
        video_path, audio_path = vd.download_video_and_audio("https://www.youtube.com/watch?v=lTxn2BuqyzU")
        print(f"Video downloaded to: {video_path}")
        print(f"Audio downloaded to: {audio_path}")
    except Exception as e:
        print(f"Failed to download video and audio: {e}")
