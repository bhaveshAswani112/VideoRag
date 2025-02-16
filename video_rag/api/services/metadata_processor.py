from .metadata_chunker import MetadataChunker
from .vector_db import VectorDBStore

class VideoMetadataProcessor:
    def __init__(self):
        self.chunker = MetadataChunker()
        self.vector_db = VectorDBStore()

    def process_video(self, video_metadata: dict):
        """
        Process video metadata: chunk and store in VectorDB.
        :param video_metadata: Dictionary containing all metadata.
        """
        # Chunk transcript and scenes
        transcript_chunks = self.chunker.chunk_transcript(video_metadata["transcript"])
        scene_chunks = self.chunker.chunk_scenes(video_metadata["frame_descriptions"])

        # Prepare metadata for VectorDB
        processed_metadata = {
            "video_uri": video_metadata["video_uri"],
            "transcript_chunks": transcript_chunks,
            "scene_chunks": scene_chunks
        }

        # Store in VectorDB
        self.vector_db.add_chunks(processed_metadata)
        self.vector_db.persist()
        print("Metadata processed and stored in VectorDB.")