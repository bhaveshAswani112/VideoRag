import cv2
from transformers import Blip2Processor, Blip2ForConditionalGeneration
import torch

class SceneExtractor:
    def __init__(self, interval=10):  
        self.interval = interval
        self.processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            "Salesforce/blip2-opt-2.7b", torch_dtype=torch.float16, device_map="auto"
        )

    def extract(self, video_path):
        """
        Extract keyframes from the video and generate descriptions for each frame.
        :param video_path: Path to the video file.
        :return: List of dictionaries containing frame descriptions and timestamps.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Failed to open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * self.interval)  # Extract frames every `interval` seconds
        frame_count = 0
        scenes = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Extract frames at the specified interval
            if frame_count % frame_interval == 0:
                # Convert frame to RGB (BLIP-2 expects RGB images)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Generate description for the frame
                description = self._describe_frame(frame_rgb)
                scenes.append({
                    "start_time": frame_count / fps,  # Timestamp in seconds
                    "description": description
                })

            frame_count += 1

        cap.release()
        return scenes

    def _describe_frame(self, frame):
        """
        Generate a description for a single frame using BLIP-2.
        :param frame: RGB image (numpy array).
        :return: Text description of the frame.
        """
        # Preprocess the frame for BLIP-2
        inputs = self.processor(frame, return_tensors="pt")
        # Generate description
        generated_ids = self.model.generate(**inputs, max_new_tokens=50)
        description = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return description


if __name__ == "__main__" :
    sc = SceneExtractor()
    print("--------------------------------------")
    print(sc.extract("C:/Users/Bhavesh/Desktop/mindflix/uploads/videos/निर्देशक की भूमिका भाग - 1.f137.mp4"))
    print("--------------------------------------")