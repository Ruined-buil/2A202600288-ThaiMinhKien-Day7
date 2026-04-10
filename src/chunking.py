from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        
        # Sentence detection: split on ". ", "! ", "? " or ".\n"
        # We use a non-capturing group for the delimiters but we want to keep them if possible?
        # The prompt says "split on", which usually means the delimiter is consumed or we keep it.
        # Looking at common sentence splitting, we usually keep the delimiter.
        # However, the task description says "Sentence detection: split on...".
        # Let's use re.split and handle the whitespace.
        
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sentences = sentences[i : i + self.max_sentences_per_chunk]
            chunk_text = " ".join(chunk_sentences).strip()
            if chunk_text:
                chunks.append(chunk_text)
        
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            # Fallback for when no separators left: hard cut
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Split text by the current separator
        if separator == "":
            parts = list(current_text)
        else:
            parts = current_text.split(separator)

        final_chunks: list[str] = []
        current_chunk_buffer = ""

        for part in parts:
            # Re-attach separator if it's not the last part and separator is not empty
            # Actually, split() removes it. We should probably keep it for context if it's a sentence end or newline.
            # But high-level logic usually reconstructs it or just uses it as a boundary.
            
            p = part if separator == "" else part + separator
            
            # If the part itself is too long, recurse on it
            if len(p) > self.chunk_size:
                # If there's something in the buffer, add it first
                if current_chunk_buffer:
                    final_chunks.append(current_chunk_buffer.strip())
                    current_chunk_buffer = ""
                
                # Recurse on the oversized part with next separators
                # Wait, if separator is "", we can't do much more.
                # If there ARE next separators, use them.
                if next_separators:
                    final_chunks.extend(self._split(part, next_separators))
                else:
                    # Hard cut if no more separators
                    for i in range(0, len(part), self.chunk_size):
                        final_chunks.append(part[i : i + self.chunk_size])
            else:
                # Check if adding this part would exceed chunk_size
                if len(current_chunk_buffer) + len(p) > self.chunk_size:
                    if current_chunk_buffer:
                        final_chunks.append(current_chunk_buffer.strip())
                    current_chunk_buffer = p
                else:
                    current_chunk_buffer += p

        if current_chunk_buffer:
            final_chunks.append(current_chunk_buffer.strip())

        return [c for c in final_chunks if c]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_prod = _dot(vec_a, vec_b)
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))
    
    if mag_a == 0 or mag_b == 0:
        return 0.0
    
    return dot_prod / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size)
        }
        
        results = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0
            results[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks
            }
        
        return results
