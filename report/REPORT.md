# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Thái Minh Kiên
**Nhóm:** D1
**Ngày:** 11/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity cho biết hai vector có hướng rất gần nhau trong không gian đa chiều. Trong văn bản, điều này có nghĩa là hai đoạn văn có sự tương đồng rất lớn về mặt ngữ nghĩa (semantics), bất kể độ dài của chúng có khác nhau hay không.

**Ví dụ HIGH similarity:**
- Sentence A: "The AI system is learning to generate code."
- Sentence B: "Artificial intelligence models are gaining the ability to write software."
- Tại sao tương đồng: Cả hai câu đều nói về khả năng lập trình của trí tuệ nhân tạo dù sử dụng các từ ngữ khác nhau.

**Ví dụ LOW similarity:**
- Sentence A: "I enjoy drinking hot coffee in the morning."
- Sentence B: "Quantum physics is a fundamental theory in physics."
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn khác nhau (đời sống và khoa học), không có sự liên quan về từ vựng hay ý nghĩa.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Vì Cosine Similarity tập trung vào **hướng** của vector thay vì **đồ dài**. Trong văn bản, một câu ngắn và một đoạn văn dài có thể cùng nói về một chủ đề; Cosine Similarity sẽ nhận ra sự tương đồng này, trong khi Euclidean sẽ coi chúng là rất "xa" nhau đơn giản vì số lượng từ (độ dài vector) khác nhau.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
> - Bước nhảy thực tế (Step) = `ChunkSize - Overlap` = `500 - 50 = 450`.
> - Số lượng chunk = `ceil((Total - Overlap) / Step)` = `(10000 - 50) / 450` = `9950 / 450` ≈ `22.11`.
> *Đáp án:* **23 chunks**.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap tăng, bước nhảy (step) giảm xuống (`500 - 100 = 400`), dẫn đến **số lượng chunk sẽ tăng lên** (25 chunks). Chúng ta muốn overlap nhiều hơn để đảm bảo ngữ cảnh không bị đứt đoạn; thông tin quan trọng nằm ở cuối chunk này sẽ được lặp lại ở đầu chunk sau, giúp mô hình AI hiểu liên mạch hơn.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Software Engineering Principles

**Tại sao nhóm chọn domain này?**
> Nhóm chúng tôi chọn domain này vì nó chứa các khái niệm cốt lõi, có cấu trúc rõ ràng và phân cấp, rất phù hợp để thử nghiệm các chiến lược chunking khác nhau. Việc hiểu và truy xuất chính xác các nguyên lý như SOLID, DRY, KISS là một bài toán thực tế và hữu ích cho các kỹ sư phần mềm.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | book.md | https://onlinelibrary.wiley.com/doi/book/10.1002/9781394297696?msockid=342527e00a4661fb18ff345a0bdc6080 | 503401 | `{"category": "software-engineering", "source": "book.md"}` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | "software-engineering" | Giúp lọc các tài liệu theo chủ đề lớn, hữu ích khi hệ thống có nhiều domain khác nhau. |
| source | string | "book.md" | Cho phép truy xuất nguồn gốc của chunk, giúp xác minh thông tin và cung cấp thêm ngữ cảnh cho người dùng. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| book.md | FixedSizeChunker (`fixed_size`) |3 |366 | No |
| book.md | SentenceChunker (`by_sentences`) | 1| 998| Partial |
| book.md | RecursiveChunker (`recursive`) | 3| 331| Yes |
| book.md | Custom(AgenticChunking) |1 |998 | Yes |

### Strategy Của Tôi

**Loại:** Custom (Agentic Chunking)

**Mô tả cách hoạt động:**
> Agentic Chunking hoạt động bằng cách phân đoạn văn bản dựa trên ý nghĩa ngữ nghĩa thay vì giới hạn ký tự cứng nhắc. Quy trình bắt đầu bằng việc chia nhỏ tài liệu thành các câu đơn lẻ, sau đó sử dụng một mô hình ngôn ngữ (LLM) để đánh giá tuần tự: "Liệu câu tiếp theo có thuộc cùng một chủ đề với đoạn hiện tại hay không?". Nếu LLM phát hiện sự chuyển dịch về mặt chủ đề (topic shift), nó sẽ ra lệnh ngắt đoạn và bắt đầu một chunk mới, từ đó tạo ra những khối thông tin có tính gắn kết logic cao.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Trong domain Software Engineering, tài liệu thường có cấu trúc phức tạp với các khối code, định nghĩa thuật toán và hướng dẫn quy trình đan xen. Agentic Chunking giúp bảo toàn trọn vẹn ngữ cảnh của một giải thích kỹ thuật hoặc một đoạn logic code, tránh việc bị cắt đôi ở giữa chừng như các phương pháp truyền thống. Điều này cực kỳ quan trọng đối với retrieval vì nó đảm bảo Agent nhận được đầy đủ thông tin liên quan trong một chunk duy nhất, giúp câu trả lời chính xác và sâu sắc hơn.

**Code snippet (nếu custom):**
```python
class AgenticChunker:
    """
    Split text into semantically coherent chunks using a Language Model (LLM).

    Algorithm:
        1. Split text into sentences.
        2. Iteratively evaluate if the next sentence belongs to the current chunk's context.
        3. Break the chunk if the LLM detects a significant topic shift.
    """

    def __init__(self, llm_fn: Callable[[str], str], max_chunk_sentences: int = 5) -> None:
        self.llm_fn = llm_fn
        self.max_chunk_sentences = max_chunk_sentences

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Split into sentences using a simple regex (similar to SentenceChunker)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if not sentences:
            return []

        final_chunks: list[str] = []
        current_chunk_buffer: list[str] = [sentences[0]]

        for i in range(1, len(sentences)):
            next_sentence = sentences[i]
            
            # If current chunk is already too long, split for performance/token limits
            if len(current_chunk_buffer) >= self.max_chunk_sentences:
                final_chunks.append(" ".join(current_chunk_buffer).strip())
                current_chunk_buffer = [next_sentence]
                continue

            # Ask the LLM if the next sentence continues the current topic
            context = " ".join(current_chunk_buffer)
            prompt = f"""You are a document segmentation assistant.
Determine if the following sentence continues the same topic as the previous context.
Respond with 'YES' if it belongs to the same topic, or 'NO' if it introduces a new topic or significant shift.

Context: "{context}"

Sentence: "{next_sentence}"

Result (YES/NO):"""

            response = self.llm_fn(prompt).strip().upper()

            if "YES" in response:
                current_chunk_buffer.append(next_sentence)
            else:
                final_chunks.append(" ".join(current_chunk_buffer).strip())
                current_chunk_buffer = [next_sentence]

        if current_chunk_buffer:
            final_chunks.append(" ".join(current_chunk_buffer).strip())

        return final_chunks
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | **của tôi** | | | |

### So Sánh Với Thành Viên Khác


| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Tuấn Hưng | Semantic Chunking | 9.5 | Giữ trọn vẹn ngữ cảnh của từng mục, truy xuất chính xác. | Các chunk có thể rất lớn, không phù hợp với các mô hình có giới hạn context nhỏ. |
| Lê Minh Hoàng | SoftwareEngineeringChunker (Custom RecursiveTrunker) | 9 | Bảo tồn hoàn hảo cấu trúc tài liệu kỹ thuật nhờ ngắt theo Header; Giữ được mối liên kết logic. | Kích thước chunk trung bình lớn, gây tốn context window của mô hình. |
| Nguyễn Xuân Hải | Parent-Child Chunking| 8 |Child nhỏ giúp tìm kiếm vector đúng mục tiêu, ít nhiễu | Gửi cả khối Parent lớn vào Prompt làm tăng chi phí API.
| Nguyễn Đăng Hải | DocumentStructureChunker | 6.3 | Giữ ngữ cảnh theo heading/list/table; grounding tốt cho tài liệu dài | Phức tạp hơn và tốn xử lý hơn; lợi thế giảm khi dữ liệu ít cấu trúc |
|Thái Minh Kiên | Agentic Chunking | 8 | chunk giữ được ý nghĩa trọn vẹn, retrieval chính xác hơn, ít trả về nửa vời, Không cần một rule cố định cho mọi loại dữ liệu | Với dataset lớn cost sẽ tăng mạnh,  chậm hơn pipeline thường, không ổn định tuyệt đối |
Trần Trung Hậu |Token-Based Chunking (Chia theo Token) | 8 | Kiểm soát chính xác tuyệt đối giới hạn đầu vào (context window) và chi phí API của LLM. | Cắt rất máy móc, dễ làm đứt gãy ngữ nghĩa của một từ hoặc một câu giữa chừng.
| Tạ Bảo Ngọc | Sliding Window + Overlap | 7/10 | Giữ vẹn câu/khối logic, tối ưu length | bị trùng dữ liệu -> tăng số chunk |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> `Semantic Chunking` là tốt nhất cho domain này vì nó tôn trọng cấu trúc logic của tài liệu, đảm bảo mỗi chunk là một đơn vị thông tin hoàn chỉnh. Điều này giúp hệ thống RAG truy xuất được ngữ cảnh đầy đủ để trả lời các câu hỏi về các nguyên lý cụ thể một cách chính xác nhất.


## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Tôi sử dụng `re.split` với biểu thức chính quy `(?<=[.!?])\s+` để tách văn bản thành các câu dựa trên dấu chấm, hỏi, hoặc cảm thán theo sau là khoảng trắng. Sau đó, tôi gom nhóm số câu tối đa theo tham số `max_sentences_per_chunk` để tạo thành các chunk hoàn chỉnh, đảm bảo không ngắt quãng ý nghĩa giữa câu.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Tôi sử dụng thuật toán đệ quy thử nghiệm lần lượt các dấu ngăn cách có ưu tiên từ lớn đến nhỏ (`\n\n` -> `\n` -> `. ` -> ` `). Nếu đoạn văn bản sau khi tách vẫn vượt quá `chunk_size`, hàm sẽ tự gọi lại chính nó với bộ ngăn cách còn lại cho đến khi đạt được kích thước mục tiêu hoặc phải cắt cứng, giúp giữ tối đa cấu trúc logic của tài liệu.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Tôi xây dựng `EmbeddingStore` hỗ trợ cả lưu trữ trong bộ nhớ (list of dicts) và ChromaDB. Khi thêm tài liệu, tôi sử dụng `embedding_fn` để chuyển text thành vector. Hàm `search` sẽ tính toán Dot Product (hoặc dùng cosine space của Chroma) để xếp hạng mức độ liên quan và trả về top-k đoạn văn bản sát nhất với câu hỏi.

**`search_with_filter` + `delete_document`** — approach:
> Với `search_with_filter`, tôi thực hiện lọc metadata trước (pre-filtering) để thu hẹp phạm vi tìm kiếm, sau đó mới tính similarity. Với `delete_document`, tôi định danh tài liệu qua `doc_id` trong metadata và xóa toàn bộ các chunk liên quan để đảm bảo tính nhất quán của dữ liệu.

### KnowledgeBaseAgent

**`answer`** — approach:
> Agent thực hiện quy trình RAG chuẩn: truy xuất top-k context từ Store, sau đó đưa vào một Prompt template có cấu trúc rõ ràng (Context + Instruction + Question). Nếu không tìm thấy thông tin liên quan, Agent được hướng dẫn trả lời trung thực là không biết dựa trên ngữ cảnh thay vì tự suy diễn.

### Test Results

```
# Output of: pytest tests/ -v
====================== 42 passed, 176 warnings in 2.99s =======================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 |The software architecture must be scalable to handle increasing user loads.|Ensuring the system can scale is essential for managing growth in the number of users. | high | 0.7021 | Yes |
| 2 |Continuous Integration helps in detecting bugs early in the development cycle.|By merging code frequently, CI pipelines allow teams to identify and fix issues sooner. | high | 0.6336 | Yes |
| 3 |Database indexing significantly improves query performance for large datasets.|Relational databases use structured schemas to ensure data integrity. | medium | 0.3242 | No |
| 4 |Monolithic architectures are easy to develop and deploy for small teams.|Microservices offer high flexibility but introduce significant operational complexity. | medium | 0.4478 | Yes |
| 5 |Unit tests verify the correctness of a single function in isolation.|The user interface should follow modern design principles for better UX. | low | 0.1258 | Yes |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> ết quả bất ngờ nhất là **Cặp số 3**; mặc dù cả hai câu đều chứa từ khóa "Database" và cùng thuộc domain dữ liệu, nhưng điểm tương đồng thực tế lại khá thấp (0.32). Điều này minh chứng rằng Embeddings không chỉ hoạt động dựa trên việc so khớp từ khóa (keyword matching) mà thực sự biểu diễn **ý nghĩa ngữ nghĩa**. Ngoài ra, việc cặp số 4 có điểm cao hơn cặp số 3 cho thấy mô hình đánh giá cao sự liên kết về mặt kiến trúc hệ thống hơn là sự trùng lặp từ vựng đơn thuần.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | "Core benefits of Information Systems?" | transformation, strategic alignment, efficiency. |
| 2 | "Governance in IT environments?" | Urbanization, management, and regulatory compliance. |
| 3 | "Explain alignment?" | Convergence between business goals and IT infrastructure. |
| 4 | "Role of a Series Editor?" | Oversight, selection of academic content, quality control. |
| 5 | "Who is Jean-Charles Pomerol?" | Series Editor and expert mentioned in the book's metadata. |
### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Core benefits of Information Systems |INFORMATION SYSTEMS, WEB AND PERVASIVE COMPUTING S... |0.134 | Yes |The core benefits of Information Systems include governance, urbanization, and alignment. |
| 2 | Governance in IT environments? |INFORMATION SYSTEMS, WEB AND PERVASIVE COMPUTING S... |0.043 | No | The context provided does not contain enough information to answer the question about governance in IT environments.|
| 3 | Explain alignment? |INFORMATION SYSTEMS, WEB AND PERVASIVE COMPUTING S... |0.149| No | The context does not provide enough information to explain alignment.|
| 4 | Role of a Series Editor? | INFORMATION SYSTEMS, WEB AND PERVASIVE COMPUTING S... |0.149 | Yes | The role of a Series Editor is to oversee and manage a specific series of publications within a particular subject area.|
| 5 | Who is Jean-Charles Pomerol? | INFORMATION SYSTEMS, WEB AND PERVASIVE COMPUTING S... |0.111 | Yes | Jean-Charles Pomerol is the series editor of the Information Systems Management series. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 3 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Em đã học được cách triển khai **Semantic Chunking** từ Hưng và **Parent-Child Chunking** từ Xuân Hải. Semantic Chunking thực sự ấn tượng vì khả năng tự động xác định ranh giới chunk dựa trên sự thay đổi ngữ nghĩa, điều này đôi khi ổn định hơn cách tiếp cận Agentic của em. Ngoài ra, mô hình Parent-Child là một giải pháp thông minh để cân bằng giữa độ chính xác khi tìm kiếm (child nhỏ) và độ đầy đủ của thông tin khi trả lời (parent lớn).

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Thông qua buổi demo, em thấy một số nhóm đã áp dụng **Hybrid Search** (kết hợp vector search và keyword search - BM25) cùng với bước **Re-ranking**. Điều này giúp hệ thống của họ xử lý cực tốt các query chứa từ khóa đặc thù như tên riêng (ví dụ: Jean-Charles Pomerol) - vốn là điểm yếu của các bộ embedding thông thường khi chúng đôi khi bị "lạc" trong các thuật ngữ kỹ thuật chung.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Em sẽ tập trung nhiều hơn vào bước **Data Cleaning** để loại bỏ các thành phần gây nhiễu như header/footer của file PDF, vì chúng thường làm gãy mạch ngữ nghĩa của các chunk. Bên cạnh đó, em sẽ bổ sung thêm metadata về "Section Heading" và "Summary" cho mỗi chunk để giúp retriever định vị thông tin nhanh hơn đối với các câu hỏi mang tính tổng quan.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5/ 5 |
| Document selection | Nhóm | 9/ 10 |
| Chunking strategy | Nhóm | 12/ 15 |
| My approach | Cá nhân | 8/ 10 |
| Similarity predictions | Cá nhân | 3/ 5 |
| Results | Cá nhân | 7/ 10 |
| Core implementation (tests) | Cá nhân | 22/ 30 |
| Demo | Nhóm | 4/ 5 |
| **Tổng** | | **70/ 100** |
