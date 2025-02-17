from .vector_db import VectorDBStore
from langchain_community.embeddings import HuggingFaceEmbeddings

class MetadataRetriever:
    def __init__(self):
        self.vector_db = VectorDBStore()
        self.embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

    def query(self, question: str, top_k: int = 3,title=None):
        """
        Retrieve relevant chunks based on a user query.
        :param question: User query.
        :param top_k: Number of results to return.
        :return: List of relevant chunks with metadata.
        """
        # Query the VectorDB
        results = self.vector_db.vector_store.similarity_search(
            query=question,
            k=top_k,
            filter={
                "title": {"$eq": title if title else ""}
            }
        )
        print("query")
        # print(results)
        # Process and format the results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
            })

        return formatted_results

    def get_relevant_context(self, question: str, top_k: int = 3,title:str =None):
        """
        Retrieve and format relevant context for a given question.
        :param question: User query.
        :param top_k: Number of results to return.
        :return: Formatted string with relevant context.
        """
        # print()
        results = self.query(question, top_k, title)
        context = ""
        idx = 1
        for result in results:
            # print(result)
            context += f"Chunk {idx}:\n"
            context += f"Content: {result['content']=}\n"
            context += f"Type: {result['metadata']['type']}\n"
            context += f"Start Time: {result['metadata']['start_time']}\n"
            context += f"End Time: {result['metadata']['end_time']}\n"
            context += f"Video URI: {result['metadata']['video_uri']}\n"
            idx+=1
        return context
