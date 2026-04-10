import os
import time
from src.chunking import FixedSizeChunker, SentenceChunker, RecursiveChunker
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.models import Document
from agentic_demo import get_openai_llm
from src.chunking import AgenticChunker

# ==========================================
# 1. CAU HINH NHOM (THAY DOI TAI DAY)
# ==========================================

GROUP_FILES = [
    "output/first_1000.md",
    # "data/your_group_file_1.md",
    # "data/your_group_file_2.txt",
]

llm_fn = get_openai_llm()
MY_CHUNKER = AgenticChunker(llm_fn=llm_fn, max_chunk_sentences=3)

BENCHMARK_QUERIES = [
    "Core benefits of Information Systems",
    "Governance in IT environments?",
    "Explain alignment?",
    "Role of a Series Editor?",
    "Who is Jean-Charles Pomerol?"
]

# ==========================================
# 2. HELPER
# ==========================================

def print_step(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(title)
    print(f"{'=' * 60}")

def print_progress(prefix: str, current: int, total: int) -> None:
    if total <= 0:
        print(f"{prefix}: 0/0")
        return

    percent = (current / total) * 100
    print(f"{prefix}: {current}/{total} ({percent:.1f}%)")

def build_context_from_results(results, max_items=3) -> str:
    context_parts = []

    for idx, res in enumerate(results[:max_items], 1):
        content = res["content"].strip()
        score = res.get("score", 0.0)
        context_parts.append(
            f"[Chunk {idx} | score={score:.3f}]\n{content}"
        )

    return "\n\n".join(context_parts)

def generate_llm_answer(query: str, results, llm_fn) -> str:
    if not results:
        return "Khong tim thay context phu hop."

    context = build_context_from_results(results, max_items=3)

    prompt = f"""You are a QA assistant.
Answer the user question only from the provided context.
If the context does not contain enough information, say so clearly.
Keep the answer concise and factual.

Question:
{query}

Context:
{context}

Answer:
"""

    try:
        answer = llm_fn(prompt)
        if not answer:
            return "LLM khong tra ve noi dung."
        return answer.strip().replace("\n", " ")
    except Exception as e:
        return f"Loi khi goi LLM: {e}"

def shorten_text(text: str, max_len: int) -> str:
    clean = text.replace("\n", " ").strip()
    if len(clean) <= max_len:
        return clean
    return clean[:max_len] + "..."

# ==========================================
# 3. QUY TRINH CHAY
# ==========================================

def run_group_benchmark():
    start_time = time.time()

    print_step("BAT DAU CHAY BENCHMARK CHO NHOM")

    # Pre-check
    print("[1/5] Kiem tra file dau vao...")
    for i, f in enumerate(GROUP_FILES, 1):
        print_progress("  Dang kiem tra file", i, len(GROUP_FILES))
        if not os.path.exists(f):
            print(f"[LOI] Khong tim thay file: {f}")
            return
        print(f"  [OK] Tim thay: {f}")

    # Khoi tao Store
    print("\n[2/5] Khoi tao EmbeddingStore...")
    store = EmbeddingStore()
    print("[OK] EmbeddingStore da san sang.")

    # Nap va Chunk du lieu
    print("\n[3/5] Doc file va chunk du lieu...")
    all_docs = []

    for file_index, file_path in enumerate(GROUP_FILES, 1):
        file_start_time = time.time()

        print_step(f"XU LY FILE {file_index}/{len(GROUP_FILES)}: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"[INFO] So ky tu trong file: {len(content)}")

        print("[INFO] Dang chunk noi dung...")
        chunks = MY_CHUNKER.chunk(content)
        print(f"[OK] Chunk xong. So chunks tao ra: {len(chunks)}")

        metadata = {
            "source": file_path,
            "category": "support" if "support" in file_path else "general"
        }

        print("[INFO] Dang tao Document objects...")
        for i, chunk_text in enumerate(chunks, 1):
            all_docs.append(Document(
                id=f"{os.path.basename(file_path)}_{i - 1}",
                content=chunk_text,
                metadata=metadata
            ))

            if i == 1 or i == len(chunks) or i % 10 == 0:
                print_progress("  Documents da tao", i, len(chunks))

        elapsed_file = time.time() - file_start_time
        print(f"[DONE] Hoan tat file: {file_path} trong {elapsed_file:.2f}s")

    print(f"\n[INFO] Tong so Document chunks: {len(all_docs)}")

    print("\n[4/5] Nap documents vao Knowledge Base...")
    store_add_start = time.time()
    store.add_documents(all_docs)
    store_add_elapsed = time.time() - store_add_start
    print(f"[OK] Da nap {len(all_docs)} chunks vao Knowledge Base trong {store_add_elapsed:.2f}s.")

    # Khoi tao Agent
    print("\n[INFO] Khoi tao KnowledgeBaseAgent...")
    agent = KnowledgeBaseAgent(store, llm_fn=llm_fn)
    print("[OK] Agent da san sang.")

    # Chay Benchmark
    print_step("KET QUA BENCHMARK")
    print("| # | Query | Top-1 Chunk Preview | Score | LLM Answer | Relevant? |")
    print("|---|-------|---------------------|-------|------------|-----------|")

    print("[5/5] Dang chay benchmark queries...")
    for i, query in enumerate(BENCHMARK_QUERIES, 1):
        print_progress("  Dang benchmark query", i, len(BENCHMARK_QUERIES))
        print(f"  [QUERY] {query}")

        results = store.search(query, top_k=3)

        if results:
            res = results[0]
            preview = shorten_text(res["content"], 50)
            score = f"{res['score']:.3f}"

            print("  [INFO] Dang goi LLM de tao cau tra loi...")
            llm_answer = generate_llm_answer(query, results, llm_fn)
            llm_answer = shorten_text(llm_answer, 120)

            print(f"| {i} | {query} | {preview} | {score} | {llm_answer} | [ ] Yes / [ ] No |")
        else:
            print(f"| {i} | {query} | KHONG TIM THAY | 0.000 | Khong co context de tra loi. | No |")

    total_elapsed = time.time() - start_time
    print("\nHuong dan: Kiem tra cot 'Relevant?' neu Top-1 chunk va LLM Answer chua dung cau tra loi ban can.")
    print(f"\n[DONE] Tong thoi gian chay: {total_elapsed:.2f}s")


if __name__ == "__main__":
    run_group_benchmark()