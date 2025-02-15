import subprocess
import os

class VideoDownloader:
    def __init__(self, output_dir="uploads/videos"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def download(self, url):
        try:
            cmd = [
                "yt-dlp",
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "-o", f"{self.output_dir}/%(title)s.%(ext)s",
                url
            ]

            subprocess.run(cmd, check=True)
            # Return the path of the downloaded video
            return os.path.join(self.output_dir, os.listdir(self.output_dir)[-1])
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to download video: {e}")
        

if __name__ == "__main__" :
    vd = VideoDownloader()
    vd.download("https://www.youtube.com/watch?v=ftDsSB3F5kg")