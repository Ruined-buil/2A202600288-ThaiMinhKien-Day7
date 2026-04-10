from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieve top-k relevant chunks from the store
        results = self.store.search(question, top_k=top_k)
        
        if not results:
            return "I'm sorry, I couldn't find any relevant information in my knowledge base to answer that question."

        # 2. Build a prompt with the chunks as context
        context_text = "\n\n".join([f"Source {i+1}:\n{res['content']}" for i, res in enumerate(results)])
        
        prompt = f"""You are a helpful assistant answering questions based on the provided context.
If the context doesn't contain the answer, say you don't know based on the context.

Context:
{context_text}

Question: {question}

Answer:"""

        # 3. Call the LLM to generate an answer
        return self.llm_fn(prompt)
