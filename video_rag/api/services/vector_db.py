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
        metadatas = []

        for chunk in metadata["transcript_chunks"]:
            documents.append(Document(page_content=chunk["text"]))
            metadatas.append({
                "type": "transcript",
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "video_uri": metadata["video_uri"]
            })

        for chunk in metadata["scene_chunks"]:
            text = ". ".join(chunk["descriptions"])
            documents.append(Document(page_content=text))
            metadatas.append({
                "type": "scene",
                "start_time": chunk["start_time"],
                "video_uri": metadata["video_uri"]
            })

        self.vector_store.add_documents(documents=documents, metadatas=metadatas)

    def persist(self):
        self.vector_store.persist()
