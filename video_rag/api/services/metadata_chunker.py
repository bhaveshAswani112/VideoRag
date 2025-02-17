from typing import List, Dict
from langchain_community.embeddings import HuggingFaceEmbeddings

class MetadataChunker:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def chunk_transcript(self, transcript: List[Dict], title: str, description: str) -> List[Dict]:
        """Store transcript text as-is while preserving metadata."""
        return [
            {
                "text": seg["text"],
                "start_time": seg["start_time"],
                "end_time": seg["end_time"],
                "title": title,
                "description": description
            }
            for seg in transcript
        ]

    def chunk_scenes(self, scenes: List[Dict], title: str, description: str) -> List[Dict]:
        """Store scene descriptions as-is while preserving metadata."""
        return [
            {
                "start_time": scene["start_time"],
                "end_time": scene["end_time"],
                "description": scene["description"],
                "title": title,
                "description": description,
            }
            for scene in scenes
        ]
