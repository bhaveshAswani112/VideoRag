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
import re
from webvtt import WebVTT
from .services.retriever import MetadataRetriever
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .serializers import VideoQuerySerializer


class VideoProcessingAPIView(APIView):
    def post(self, request):
        from django.conf import settings
        from .serializers import VideoProcessingRequestSerializer
        serializer = VideoProcessingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video_url = serializer.validated_data['video_url']
        print("request reached ")
        print(video_url)
        transcript_output_path = ""
        try:
            # Step 1: Download the video
            downloader = VideoDownloader()
            downloaded_video_path,downloaded_audio_path,title,description = downloader.download_video_and_audio(video_url)
            # print(video_name)
            # print("Reached below")
            # Step 2: Extract scenes from the video
            scene_extractor = SceneExtractor(interval=2)
            scenes = scene_extractor.extract(downloaded_video_path)
            caption_processor = CaptionProcessor(deepgram_api_key="17bdd81afce172d05d26e239264c1c274e76bbfe")
            transcript_output_path = os.path.join(settings.BASE_DIR, "uploads", "captions", f"{title}.vtt")
            os.makedirs(os.path.dirname(transcript_output_path), exist_ok=True)
            pattern = r"(?<=watch\?v=)[\w-]+"
            match = re.search(pattern, video_url)
            video_id = match.group(0) if match else None
            asyncio.run(caption_processor.process_captions(
                video_id=video_id,  
                audio_path=downloaded_audio_path,
                output_path=transcript_output_path,
                target_lang="en",
                fallback_lang="hi"
            ))
            chunker = MetadataChunker()
            vtt = WebVTT.read(transcript_output_path)
            transcript_data = [
                {
                    "text": caption.text,
                    "start_time": float(caption.start_in_seconds),
                    "end_time": float(caption.end_in_seconds)
                } for caption in vtt.captions
            ]
            transcript_chunks = chunker.chunk_transcript(transcript_data,title,description) 
            scene_chunks = chunker.chunk_scenes(scenes,title,description)
            
            vector_db = VectorDBStore()
            vector_db.add_chunks({
                "video_uri": video_url,
                "transcript_chunks": transcript_chunks,
                "scene_chunks": scene_chunks,
            })
            
            print(title)
            return Response({
            "message": "Video processed successfully",
            "title": title,
            "scene_count": len(scenes),
            "transcript_chunks": len(transcript_chunks),
            "processed_file": transcript_output_path,
            "description": description
        }, status=status.HTTP_200_OK)


        except Exception as e:
            if transcript_output_path and transcript_output_path!='' and  os.path.exists(transcript_output_path) : 
                os.remove(transcript_output_path)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# class VideoQueryAPIView(APIView):
#     def post(self, request):
#         from .serializers import VideoQuerySerializer
#         """
#         API endpoint for querying video metadata
#         Example POST body:
#         {
#             "question": "What did the speaker say about machine learning?",
#             "top_k": 5
#         }
#         """
#         serializer = VideoQuerySerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             question = serializer.validated_data['question']
#             top_k = serializer.validated_data.get('top_k', 3)
            
#             retriever = MetadataRetriever()
#             results = retriever.query(question, top_k=top_k)
            
#             return Response({
#                 "query": question,
#                 "results": results,
#                 "count": len(results)
#             }, status=status.HTTP_200_OK)
            
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class VideoQueryAPIView(APIView):
    def post(self, request):
        """
        Enhanced API endpoint with Groq LLM integration
        Example POST body:
        {
            "question": "Explain the key points about AI safety",
            "top_k": 5,
            "model": "llama"  # Optional Groq model selection
        }
        """
        serializer = VideoQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = serializer.validated_data['question']
            top_k = serializer.validated_data.get('top_k', 10)
            title = serializer.validated_data["title"]
            model_name = serializer.validated_data.get('model', 'llama-3.1-8b-instant')
            print("----------------------------")
            print(question)
            print(top_k)
            print(title)
            print("----------------------------")
            # Retrieve context chunks
            retriever = MetadataRetriever()
            context_chunks = retriever.get_relevant_context(question, top_k=top_k,title=title)
            # Initialize Groq LLM
            groq_llm = ChatGroq(
                temperature=0.4,
                model_name=model_name,
                api_key=os.getenv("GROQ_API_KEY")  
            )
            # Create processing chain
            prompt = ChatPromptTemplate.from_template(
                """You are an AI assistant tasked with analyzing the content of a video and answering a given question with clarity and accuracy. 

                **Instructions:**  
                - Carefully analyze the provided video context to extract key details.  
                - Answer the question concisely while ensuring completeness.  
                - If timestamps are available, include them to indicate where relevant discussions occur.  
                - If certain chunks are irrelevant, provide timestamps for when the relevant conversation starts.  
                - Structure your response in a way that makes it easy to follow.

                **Video Context:**  
                {context}

                **User Question:**  
                {question}

                **Detailed Response:**  
                (Provide your answer here, including timestamps where applicable.)"""
            )


            chain = prompt | groq_llm | StrOutputParser()
            
            # Generate answer
            answer = chain.invoke({
                "context": context_chunks,
                "question": question
            })

            return Response({
                "query": question,
                "answer": answer,
                "sources": context_chunks,
                "model": model_name
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

