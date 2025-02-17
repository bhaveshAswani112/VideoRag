import os
import sys
import subprocess
import django
from django.conf import settings
import logging
from typing import Optional, Tuple
from slugify import slugify
from unidecode import unidecode
import re

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

    def custom_slugify(self, text): 
        # Transliterate Hindi characters to their closest ASCII equivalents
        text = unidecode(text)
        # Convert to lowercase
        text = text.lower()
        # Replace spaces with hyphens
        text = re.sub(r'\s+', '-', text)
        # Remove non-word characters (except hyphens)
        text = re.sub(r'[^\w\-]', '', text)
        # Remove consecutive hyphens
        text = re.sub(r'\-+', '-', text)
        return text.strip('-')

    def get_video_title(self, url: str) -> str:
        """
        Retrieve the title of the video from the given URL.

        :param url: URL of the video
        :return: Title of the video
        """
        try:
            cmd = [
                "yt-dlp",
                "--get-title",
                "--skip-download",
                url
            ]

            self.logger.info(f"Fetching title for {url}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            title = result.stdout.strip()

            if not title:
                raise Exception("Could not retrieve video title")

            return self.custom_slugify(title)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to fetch video title: {e}")
            self.logger.error(f"Command output: {e.output}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            raise

    def get_video_description(self, url: str) -> str:
        """
        Retrieve the description of the video from the given URL.

        :param url: URL of the video
        :return: Description of the video
        """
        try:
            cmd = [
                "yt-dlp",
                "--get-description",
                "--skip-download",
                url
            ]

            self.logger.info(f"Fetching description for {url}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            description = result.stdout.strip()

            if not description:
                self.logger.warning("Could not retrieve video description")
                return ""

            return description

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to fetch video description: {e}")
            self.logger.error(f"Command output: {e.output}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            raise

    def download_video_and_audio(self, url: str) -> Tuple[str, str, str]:
        """
        Download both video and audio from the given URL.

        :param url: URL of the video to download
        :return: Tuple containing paths to the downloaded video and audio files, and the video title
        """
        try:
            title = self.get_video_title(url)
            description = self.get_video_description(url)

            video_output = os.path.join(self.output_dir, f"{title}.mp4")
            audio_output = os.path.join(self.output_dir, f"{title}.m4a")

            video_cmd = [
                "yt-dlp",
                "-f", "bestvideo[ext=mp4]",
                "-o", video_output,
                url
            ]

            audio_cmd = [
                "yt-dlp",
                "-f", "bestaudio[ext=m4a]",
                "-o", audio_output,
                url
            ]

            self.logger.info(f"Downloading video for {url}")
            subprocess.run(video_cmd, check=True)

            self.logger.info(f"Downloading audio for {url}")
            subprocess.run(audio_cmd, check=True)

            return video_output, audio_output, title, description

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to download video or audio: {e}")
            self.logger.error(f"Command output: {e.output}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vd = VideoDownloader()
    try:
        video_path, audio_path, title, description = vd.download_video_and_audio("https://www.youtube.com/watch?v=ftDsSB3F5kg")
        print(f"Video downloaded to: {video_path}")
        print(f"Audio downloaded to: {audio_path}")
        print(f"Title: {title}")
        print(f"Description: {description}...")  
    except Exception as e:
        print(f"Failed to download video and audio: {e}")
