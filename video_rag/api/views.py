import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.video_downloader import VideoDownloader
from .services.scene_extractor import SceneExtractor
from .services.metadata_chunker import MetadataChunker
from .services.vector_db import VectorDBStore
from .services.transcript_extractor import CaptionProcessor
import asyncio

class VideoProcessingAPIView(APIView):
    def post(self, request):
        from django.conf import settings

        # Validate input
        from .serializers import VideoProcessingRequestSerializer
        serializer = VideoProcessingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video_url = serializer.validated_data['video_url']
        try:
            # Step 1: Download the video
            downloader = VideoDownloader()
            downloaded_video_path = downloader.download(video_url)
            video_name = os.path.basename(downloaded_video_path)

            # Step 2: Extract scenes from the video
            scene_extractor = SceneExtractor(interval=10)  # Adjust interval as needed
            scenes = scene_extractor.extract(downloaded_video_path)

            # Step 3: Extract captions/transcripts (YouTube or Deepgram fallback)
            audio_path = os.path.splitext(downloaded_video_path)[0] + ".m4a"
            caption_processor = CaptionProcessor(deepgram_api_key="YOUR_DEEPGRAM_API_KEY")
            transcript_output_path = os.path.join(settings.BASE_DIR, "uploads", "captions", f"{video_name}.vtt")
            os.makedirs(os.path.dirname(transcript_output_path), exist_ok=True)
            asyncio.run(caption_processor.process_captions(
                video_id=None,  # You can extract this if it's a YouTube link.
                audio_path=audio_path,
                output_path=transcript_output_path,
                target_lang="en",
                fallback_lang="hi"
            ))

            # Step 4: Chunk metadata (transcripts and scenes)
            chunker = MetadataChunker(chunk_size=500, chunk_overlap=50)
            transcript_chunks = chunker.chunk_transcript([
                {"text": scene["description"], "start_time": scene["start_time"], "end_time": scene["start_time"] + 10}
                for scene in scenes
            ])
            scene_chunks = chunker.chunk_scenes(scenes)

            # Step 5: Store metadata in VectorDB
            vector_db = VectorDBStore()
            vector_db.add_chunks({
                "video_uri": video_url,
                "transcript_chunks": transcript_chunks,
                "scene_chunks": scene_chunks,
            })
            vector_db.persist()

            return Response({
                "message": "Video processed successfully",
                "video_name": video_name,
                "scenes": scenes,
                "transcript_file": transcript_output_path,
                "vector_db_status": "Metadata stored successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
