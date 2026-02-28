import json
import torch
from generate import build_prompt, generate_answer
from process import CustomHybridRetriever
from transformers import AutoTokenizer, AutoModelForCausalLM
ANDREW_ID = "justinl5"
INPUT_FILE = "leaderboard_queries.json"
OUTPUT_FILE = "output/leaderboard_answers.json"
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"

def main():
    retriever = CustomHybridRetriever(dense_model_name='all-MiniLM-L6-v2')
    retriever.load_index("rag_index")
    
    model_id = "mistralai/Mistral-7B-Instruct-v0.3" 
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )
    with open(INPUT_FILE, "r") as f:
        queries = json.load(f)

    print(f"Loaded {len(queries)} queries from {INPUT_FILE}")

    results = {"andrewid": ANDREW_ID}

    for i, item in enumerate(queries):
        qid = item["id"]
        question = item["question"]
        print(f"\n[{i+1}/{len(queries)}] Processing query {qid}: {question}")
        answer = generate_answer(question, retriever, tokenizer, model)
        results[qid] = answer
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
