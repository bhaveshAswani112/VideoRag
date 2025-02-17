from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document


class VectorDBStore:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        self.vector_store = Chroma(
            collection_name="video_metadata",
            embedding_function=self.embedding_model,
            persist_directory=".chromadb"
        )

    def add_chunks(self, metadata: dict):
        documents = []
        
        # For transcript chunks
        for chunk in metadata["transcript_chunks"]:
            documents.append(Document(
                page_content=f"Transcript: {chunk['text']}",  
                metadata={
                    "type": "transcript",
                    "start_time": chunk["start_time"],
                    "end_time": chunk["end_time"],
                    "video_uri": metadata["video_uri"],
                    "title": chunk["title"],
                    "description": chunk.get("description", "N/A")  
                }
            ))

        # For scene chunks
        for chunk in metadata["scene_chunks"]:
            documents.append(Document(
                page_content=f"Scene: {chunk['description']}", 
                metadata={
                    "type": "scene",
                    "start_time": chunk["start_time"],
                    "end_time": chunk.get("end_time", chunk["start_time"] + 2),  # Handle missing end_time
                    "video_uri": metadata["video_uri"],
                    "title": chunk["title"],
                    "description": chunk["description"]
                }
            ))

        # Single call with proper document structure
        self.vector_store.add_documents(documents=documents)


    def persist(self):
        self.vector_store.persist()
