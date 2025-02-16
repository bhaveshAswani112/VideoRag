from .vector_db import VectorDBStore
from langchain_community.embeddings import HuggingFaceEmbeddings

class MetadataRetriever:
    def __init__(self):
        self.vector_db = VectorDBStore()
        self.embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

    def query(self, question: str, top_k: int = 3):
        """
        Retrieve relevant chunks based on a user query.
        :param question: User query.
        :param top_k: Number of results to return.
        :return: List of relevant chunks with metadata.
        """
        # Query the VectorDB
        results = self.vector_db.vector_store.similarity_search_with_score(
            query=question,
            k=top_k
        )

        # Process and format the results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'relevance_score': score
            })

        return formatted_results

    def get_relevant_context(self, question: str, top_k: int = 3):
        """
        Retrieve and format relevant context for a given question.
        :param question: User query.
        :param top_k: Number of results to return.
        :return: Formatted string with relevant context.
        """
        results = self.query(question, top_k)
        context = ""

        for idx, result in enumerate(results, 1):
            context += f"Chunk {idx}:\n"
            context += f"Content: {result['content']}\n"
            context += f"Type: {result['metadata']['type']}\n"
            context += f"Start Time: {result['metadata']['start_time']}\n"
            if 'end_time' in result['metadata']:
                context += f"End Time: {result['metadata']['end_time']}\n"
            context += f"Video URI: {result['metadata']['video_uri']}\n"
            context += f"Relevance Score: {result['relevance_score']}\n\n"

        return context
