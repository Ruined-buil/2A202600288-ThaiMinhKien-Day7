import os
import sys
import traceback
from pathlib import Path

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from dotenv import load_dotenv
from src.chunking import ChunkingStrategyComparator
from src.embeddings import LocalEmbedder

load_dotenv()

DEFAULT_FILE_PATH = "output/first_2000.md"
DEFAULT_QUERY = "What are the definitions of Information Systems governance, urbanization, and alignment?"


def get_openai_llm():
    """Return a safe LLM function. Falls back to mock on any runtime error."""
    try:
        from openai import OpenAI
        client = OpenAI()

        def mock_llm_fn(prompt: str) -> str:
            keywords = ["however", "furthermore", "finally", "specifically", "in contrast"]
            if any(k in prompt.lower() for k in keywords):
                return "YES"
            return "NO"

        def llm_fn(prompt: str) -> str:
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                print(f"[WARN] OpenAI call failed: {e}")
                print("[WARN] Falling back to mock LLM.")
                return mock_llm_fn(prompt)

        return llm_fn

    except Exception as e:
        print(f"[WARN] Could not initialize OpenAI client: {e}")
        print("[WARN] Falling back to mock keyword-based LLM.")

        def mock_llm_fn(prompt: str) -> str:
            keywords = ["however", "furthermore", "finally", "specifically", "in contrast"]
            if any(k in prompt.lower() for k in keywords):
                return "YES"
            return "NO"

        return mock_llm_fn


def resolve_embedding_fn(embedder):
    """
    Return the real embedding callable from LocalEmbedder.
    Adjust method names here if your class uses a different API.
    """
    if callable(embedder):
        return embedder

    for method_name in ["embed", "encode", "get_embedding", "embed_text"]:
        if hasattr(embedder, method_name):
            method = getattr(embedder, method_name)
            if callable(method):
                print(f"[INFO] Using embedder method: {method_name}")
                return method

    raise TypeError(
        "LocalEmbedder is not callable and no known embedding method was found. "
        "Expected one of: embed, encode, get_embedding, embed_text"
    )


def demo_agentic_chunking(file_path: str = None):
    print("--- Agentic Chunking Demo & Comparison ---")

    if file_path and Path(file_path).exists():
        print(f"Loading document: {file_path}")
        sample_text = Path(file_path).read_text(encoding="utf-8")

        if len(sample_text) > 5000:
            print(f"Document is very large ({len(sample_text)} chars). Slicing first 5000 chars for demo.")
            sample_text = sample_text[:5000]
    else:
        print("No file provided or file not found. Using default sample text.")
        sample_text = """
Python is a popular programming language. It is known for its readability and large ecosystem of libraries.
Data science applications often use Python for analysis. Libraries like Pandas and NumPy are essential for this field.
Moving to a different topic, climate change is a global concern. Rising temperatures affect ecosystems worldwide.
Renewable energy sources such as solar and wind power can help reduce carbon emissions.
The transition to a green economy requires international cooperation.
In conclusion, both technology and environmental policy are crucial for the future.
"""

    query = DEFAULT_QUERY

    llm_fn = get_openai_llm()

    try:
        print("[INFO] Initializing LocalEmbedder...")
        embedder = LocalEmbedder()
        embedding_fn = resolve_embedding_fn(embedder)
    except Exception as e:
        print(f"[ERROR] Failed to initialize embedder: {e}")
        traceback.print_exc()
        return

    try:
        comparator = ChunkingStrategyComparator()
    except Exception as e:
        print(f"[ERROR] Failed to initialize comparator: {e}")
        traceback.print_exc()
        return

    print(f"\nBenchmark Query: '{query}'")
    print("-" * 80)
    print(f"{'Strategy':<15} | {'Count':<5} | {'Avg Len':<8} | {'Quality':<8}")
    print("-" * 80)

    try:
        results = comparator.compare_with_quality(
            text=sample_text,
            chunk_size=500,
            llm_fn=llm_fn,
            query=query,
            embedding_fn=embedding_fn,
        )
    except Exception as e:
        print(f"[ERROR] compare_with_quality failed: {e}")
        traceback.print_exc()
        return

    if not results:
        print("[WARN] No results returned.")
        print("[WARN] This usually means one strategy failed silently or compare_with_quality returned an empty dict.")
        return

    for name, data in results.items():
        try:
            print(
                f"{name:<15} | "
                f"{data.get('count', 0):<5} | "
                f"{data.get('avg_length', 0):<8.2f} | "
                f"{data.get('retrieval_quality', 0):<8.3f}"
            )
        except Exception as e:
            print(f"[WARN] Failed to print result for strategy '{name}': {e}")
            print(f"[WARN] Raw data: {data}")


if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE_PATH
    demo_agentic_chunking(path_arg)