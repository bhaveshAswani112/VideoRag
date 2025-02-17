from .vector_db import VectorDBStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

class MetadataRetriever:
    def __init__(self):
        self.vector_db = VectorDBStore()
        self.embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        self.llm = ChatGroq()
        self.prompt = ChatPromptTemplate.from_template(
            "You are an AI assistant for a video content analysis system. "
            "Your task is to determine whether a user's query is asking about "
            "visual content (scene) or spoken content (transcription) of a video. "
            "This classification helps our system retrieve the most relevant information. "
            "\n\nQuery: {query}\n\n"
            "Respond with only one word: either 'scene' or 'transcription'. "
            "If you are unsure or the query could apply to both, respond with 'transcription'."
        )


    def determine_query_type(self, question: str) -> str:
        """
        Use Groq LLM to determine if the query is about a scene or transcription.
        """
        chain = self.prompt | self.llm
        response = chain.invoke({"query": question})
        query_type = response.content.strip().lower()
        return "scene" if query_type == "scene" else "transcription"

    def query(self, question: str, top_k: int = 3, title: str = None):
        query_type = self.determine_query_type(question)
        
       
        filter_conditions = [{"type": query_type}]
        if title:
            filter_conditions.append({"title": title})
        
        
        filter_dict = {"$and": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]

        # Query the VectorDB
        results = self.vector_db.vector_store.similarity_search(
            query=question,
            k=top_k,
            filter=filter_dict
        )

        # Process and format the results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
            })

        return formatted_results


    def get_relevant_context(self, question: str, top_k: int = 3, title: str = None):
        """
        Retrieve and format relevant context for a given question.
        :param question: User query.
        :param top_k: Number of results to return.
        :param title: Title of the video (optional).
        :return: Formatted string with relevant context.
        """
        results = self.query(question, top_k, title)
        context = ""
        for idx, result in enumerate(results, 1):
            context += f"Chunk {idx}:\n"
            context += f"Content: {result['content']}\n"
            context += f"Type: {result['metadata']['type']}\n"
            context += f"Start Time: {result['metadata']['start_time']}\n"
            context += f"End Time: {result['metadata']['end_time']}\n"
            context += f"Video URI: {result['metadata']['video_uri']}\n\n"
        return context
