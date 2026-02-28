# Script Descriptions

## webscraper.py

Web scraper for building the RAG knowledge base. Uses **Playwright** (headless Chromium) to render JavaScript-heavy pages and **BeautifulSoup** to parse HTML.

- Maintains a large dictionary of seed URLs covering Pittsburgh/CMU topics (government, sports, culture, museums, events, universities, etc.).
- Recursively discovers subpage links up to a configurable depth and scrapes them concurrently with a thread pool.
- Filters out low-quality pages (404s, login walls, boilerplate-heavy content) via heuristics.
- Supports incremental scraping by loading previously scraped documents and skipping already-visited URLs.
- Outputs scraped documents as JSON to the `output/` directory.

**Usage:**
```bash
python webscraper.py
```
Edit the `__main__` block to configure which URL set, depth, and output file to use.

---

## generate.py

Core RAG generation module. Builds prompts from retrieved context and generates answers using a HuggingFace causal LM.

- `build_prompt(query, results)` — Constructs a structured prompt that injects retrieved document chunks as context and instructs the model to answer concisely and factually.
- `generate_answer(query, retriever, tokenizer, model)` — Runs hybrid retrieval (top-5 results, RRF fusion), builds the prompt, and generates an answer with constrained decoding (`max_new_tokens=100`, `temperature=0.2`).

When run directly, it starts an interactive REPL where you can ask questions.

**Usage:**
```bash
python generate.py
```

---

## run_leaderboard.py

Batch inference script for the **leaderboard** evaluation. Reads queries from `leaderboard_queries.json`, generates answers using the RAG pipeline, and writes results to `output/leaderboard_answers.json`.

- Model: `mistralai/Mistral-7B-Instruct-v0.3`
- Retriever: `CustomHybridRetriever` with `all-MiniLM-L6-v2` embeddings
- Output format: JSON with `andrewid` and `{query_id: answer}` pairs.

**Usage:**
```bash
python run_leaderboard.py
```

---

## run_test_set.py

Batch inference script for the **test set** evaluation. Reads questions line-by-line from `test_set.txt`, generates answers using the RAG pipeline, and writes results to `output/test_set_answers_1.json`.

- Model: `meta-llama/Llama-3.2-3B-Instruct`
- Retriever: `CustomHybridRetriever` with `all-MiniLM-L6-v2` embeddings
- Output format: JSON with `andrewid` and `{question_number: answer}` pairs.

**Usage:**
```bash
python run_test_set.py
```
