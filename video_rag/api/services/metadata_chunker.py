from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

class MetadataChunker:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def chunk_transcript(self, transcript: list) -> list:
        full_text = " ".join([seg["text"] for seg in transcript])
        chunks = self.text_splitter.create_documents([full_text])
        
        chunked_transcript = []
        start_index = 0
        for chunk in chunks:
            end_index = start_index + len(chunk.page_content.split())
            chunked_transcript.append({
                "start_time": transcript[start_index]["start_time"],
                "end_time": transcript[min(end_index, len(transcript) - 1)]["end_time"],
                "text": chunk.page_content
            })
            start_index = end_index
        
        return chunked_transcript

    def chunk_scenes(self, scenes: list) -> list:
        full_text = " ".join([scene["description"] for scene in scenes])
        chunks = self.text_splitter.create_documents([full_text])
        
        chunked_scenes = []
        start_index = 0
        for chunk in chunks:
            end_index = start_index + len(chunk.page_content.split())
            chunked_scenes.append({
                "start_time": scenes[start_index]["start_time"],
                "descriptions": chunk.page_content.split(". ")
            })
            start_index = end_index
        
        return chunked_scenes
