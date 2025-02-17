from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import cv2
from tqdm import tqdm
import logging
import os
import sys
import django
from django.conf import settings

# Setup Django environment
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "video_rag.settings")
django.setup()

class SceneExtractor:
    def __init__(self, interval=2, batch_size=16):
        self.interval = interval
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(self.device)
        logging.basicConfig(level=logging.INFO)

    def extract(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Failed to open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * self.interval)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        scenes = []

        frames_to_process = []
        frame_times = []

        with tqdm(total=total_frames, desc="Extracting scenes") as pbar:
            for frame_count in range(0, total_frames, frame_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
                ret, frame = cap.read()
                if not ret:
                    break

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames_to_process.append(frame_rgb)
                frame_times.append(frame_count / fps)

                if len(frames_to_process) == self.batch_size or frame_count + frame_interval >= total_frames:
                    batch_descriptions = self._describe_frames(frames_to_process)
                    for time, description in zip(frame_times, batch_descriptions):
                        # Ensure start_time is a float
                        start_time = self._convert_to_float(time)
                        end_time = start_time + self.interval

                        scenes.append({
                            "start_time": start_time,
                            "end_time": end_time,
                            "description": description
                        })

                    frames_to_process = []
                    frame_times = []

                pbar.update(frame_interval)

        cap.release()
        return scenes

    def _describe_frames(self, frames):
        try:
            inputs = self.processor(images=frames, return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=50)
            descriptions = self.processor.batch_decode(outputs, skip_special_tokens=True)
            return descriptions
        except Exception as e:
            logging.error(f"Error in frame description: {str(e)}")
            return ["Error in description"] * len(frames)

    def _convert_to_float(self, value):
        """Safely convert start_time to a float (from string or int)."""
        try:
            return float(value)
        except (ValueError, TypeError):
            logging.warning(f"Invalid time value: {value}. Defaulting to 0.0.")
            return 0.0


if __name__ == "__main__":
    sc = SceneExtractor()
    scenes = sc.extract(os.path.join(settings.BASE_DIR, 'uploads', 'videos', '-1.mp4'))
    print(scenes)
