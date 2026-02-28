import json
import torch
from generate import build_prompt, generate_answer
from process import CustomHybridRetriever
from transformers import AutoTokenizer, AutoModelForCausalLM

ANDREW_ID = "justinl5"
INPUT_FILE = "test_set.txt"
OUTPUT_FILE = "output/test_set_answers_1.json"
MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"

def main():

    retriever = CustomHybridRetriever(dense_model_name='all-MiniLM-L6-v2')
    retriever.load_index("rag_index")

    model_id = MODEL_ID
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )

    with open(INPUT_FILE, "r") as f:
        questions = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(questions)} queries from {INPUT_FILE}")

    results = {"andrewid": ANDREW_ID}

    for i, question in enumerate(questions):
        qid = str(i + 1)
        print(f"\n[{i+1}/{len(questions)}] Processing query {qid}: {question}")
        answer = generate_answer(question, retriever, tokenizer, model)
        results[qid] = answer
        
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
