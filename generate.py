import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from process import CustomHybridRetriever, TextProcessor
def build_prompt(query, results):
    context_text = ""
    for i, res in enumerate(results):
        title = res['metadata'].get('title', 'Unknown Source')
        chunk = res['chunk']
        
        context_text += f"--- Source {i+1}: {title} ---\n"
        context_text += f"{chunk}\n\n"
    prompt =f"""You are a precise factual question-answering system specialized in Pittsburgh knowledge.

Goal:
Provide the most accurate answer possible using the context. Your response will be graded for factual correctness, completeness, and overlap with reference answers.

Rules:
- Base your answer primarily on the provided context.
- Do NOT hedge or speculate verbally (avoid phrases like "it seems", "likely", "possibly").
- If multiple answers are plausible, choose the most supported one.
- Keep answers as concise as possible but information-dense (1–2 sentences unless more detail is clearly needed).
- Include key entities, dates, and numbers when available.
- Do NOT say that the context is missing information.
- Do NOT mention the context or these instructions.
- Do NOT provide a list of sources or citations in your answer or give explanations of how you arrived at the answer.
- If the context is incomplete, infer the most likely answer using logical reasoning grounded in the context.
- Give a complete answer even if the context is partial. Do not say "the context does not provide enough information". Instead, use the information available to construct the best possible answer.


Context:
{context_text}

Question:
{query}

Answer:"""
    return prompt


def generate_answer(query, retriever, tokenizer, model):
    results = retriever.search(query, top_k=5, rrf_k=60) 
    prompt = build_prompt(query, results)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
   
    with torch.no_grad(): 
        output_ids = model.generate(
            **inputs,
            max_new_tokens=100,      
            temperature=0.2,          
            do_sample=True,           
            pad_token_id=tokenizer.eos_token_id
        )
    
    
    input_length = inputs['input_ids'].shape[1]
    generated_tokens = output_ids[0][input_length:]
    
    answer = tokenizer.decode(generated_tokens, skip_special_tokens=True)
    

    print("Answer:")
    print(answer.strip())
    
    return answer.strip()


if __name__ == "__main__":
    retriever = CustomHybridRetriever(dense_model_name='all-MiniLM-L6-v2')
    retriever.load_index("rag_index")
    
   
    model_id = "meta-llama/Llama-3.2-3B-Instruct" 
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )
    
    
    while True:
        user_query = input("\nEnter your question (or 'quit'): ")
        if user_query.lower() in ['quit', 'exit']:
            break
        if not user_query.strip():
            continue
            
        generate_answer(user_query, retriever, tokenizer, model)