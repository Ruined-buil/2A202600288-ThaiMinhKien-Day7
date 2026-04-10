import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Them thu muc hien tai vao path de import src
sys.path.append(os.getcwd())

from src.embeddings import OpenAIEmbedder
from src.chunking import compute_similarity

def main():
    print("OPENAI_API_KEY exists:", bool(os.getenv("OPENAI_API_KEY")))

    # 1. Khoi tao Embedder
    try:
        embedder = OpenAIEmbedder()
    except Exception as e:
        print(f"Loi khoi tao OpenAI: {e}")
        return

    # 2. Dinh nghia 5 cap cau
    pairs = [
        (
            "The software architecture must be scalable to handle increasing user loads.",
            "Ensuring the system can scale is essential for managing growth in the number of users."
        ),
        (
            "Continuous Integration helps in detecting bugs early in the development cycle.",
            "By merging code frequently, CI pipelines allow teams to identify and fix issues sooner."
        ),
        (
            "Database indexing significantly improves query performance for large datasets.",
            "Relational databases use structured schemas to ensure data integrity."
        ),
        (
            "Monolithic architectures are easy to develop and deploy for small teams.",
            "Microservices offer high flexibility but introduce significant operational complexity."
        ),
        (
            "Unit tests verify the correctness of a single function in isolation.",
            "The user interface should follow modern design principles for better UX."
        )
    ]

    print("\n--- DANG TINH TOAN DO TUONG DONG BANG GPT EMBEDDINGS ---\n")
    print(f"{'No.':<4} | {'Similarity Score':<16} | {'Status'}")
    print("-" * 40)

    for i, (a, b) in enumerate(pairs, 1):
        vec_a = embedder(a)
        vec_b = embedder(b)

        score = compute_similarity(vec_a, vec_b)

        status = "High match" if score > 0.7 else ("Medium" if score > 0.4 else "Low/Irrelevant")

        print(f"{i:<4} | {score:>16.4f} | {status}")

    print("\n--- HOAN TAT ---")

if __name__ == "__main__":
    main()