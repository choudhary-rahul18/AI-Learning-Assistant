from functions import *
import requests
import time
import subprocess, sys
from llama_cpp import Llama
import gc
Model_path="/Users/rahulchoudhary/llama.cpp/models/phi3/Phi-3-mini-128k-instruct.Q4_K_M.gguf"
# Global variable declaration
llm_instance = None

def load_llm_silently(ctx_size, model_path=Model_path):
    global llm_instance
    devnull = open(os.devnull, "w")
    old_stderr = sys.stderr
    sys.stderr = devnull

    try:
        llm_instance = Llama(
            model_path=model_path,
            n_ctx=ctx_size,
            n_gpu_layers=-1,  # Critical: -1 = offload ALL layers to Metal
            n_threads=8,       # Optimal for M4 (4 performance + 4 efficiency cores)
            verbose=False,
            use_mlock=True     # Keep model in memory
        )
        return llm_instance
    finally:
        sys.stderr = old_stderr
        devnull.close()



def ask_llm(query: str, session_id: str, chat_history: list = None) -> str:
    prompt = prompt_for_QnA(query, session_id, chat_history)
    start = time.time()
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3-14b-custom",
        "prompt": prompt,
        "stream": False,
        "temperature": 0.3,
        "top_p": 0.5
    })
    latency = time.time() - start
    if response.status_code == 200:
        return response.json()["response"], latency
    else:
        print("Error:", response.status_code, response.text)
        return "Something went wrong!"


# Config
MODEL_PATH = "../models/phi3/Phi-3-mini-128k-instruct.Q4_K_M.gguf"
LLAMA_CLI_PATH = "./bin/llama-cli"
LLAMA_CWD = "/Users/rahulchoudhary/llama.cpp/build"

def ask_phi3(query: str, session_id: str) -> str:
    prompt = prompt_for_QnA2(query, session_id)
    
    try:
        # Use the already loaded llm instance
        output = llm.create_completion(
            prompt,
            max_tokens=150,
            echo=False  # don't include the prompt in the output
        )
        return output["choices"][0]["text"].strip()
    except Exception as e:
        print("Error:", str(e))
        return "Something went wrong!"

# The llm instance is already loaded globally
def prompt_for_QnA(query: str, session_id: str, chat_history: list = None) -> str:
    """Generate prompt with context and chat history"""
    retrieved = retrieve_top_chunks_hybrid(query, 5, session_id)
    
    # Format chat history if provided
    history_context = ""
    history_context = "\n\n---CONVERSATION HISTORY---\n"
    for i, msg in enumerate(chat_history):  # Only take last 3 messages
        speaker = "USER" if msg["role"] == "user" else "ASSISTANT"
        history_context += f"{speaker}: {msg['content']}\n"
    
    prompt = f"""
You are a helpful and concise teaching assistant with conversation memory.

Your job is to answer ONLY using the context below and the conversation history. 
If unsure, say 'Not found in the materials'.

---CONTENT START---
{retrieved}
---CONTENT END---
{history_context}

Current Question: {query}

RESPONSE RULES:
1. First check if this question relates to previous conversation topics
2. For subject questions (Science/Social Science etc.):
   - Start with definition/core concept if found
   - Otherwise give 30-40 word explanation
3. Include 2-3 key bullet points (50-60 words total)
4. Keep response under 150 words
5. Maintain natural conversation flow using history context
5. NEVER:
   -Say "Hello" or introduce yourself unless asked
   - Use general knowledge 
   - Reference chat history
   - Say "as mentioned before" or similar phrases

FORMATTING:
- Use Markdown for clarity
- Bold important terms
- Use bullet points for key takeaways
- Keep paragraphs short
"""
    return prompt

def prompt_for_QnA1(query):
    retrieved = retrieve_top_chunks_hybrid(query,5)
    prompt = f"""
You are a helpful and concise teaching assistant.

Your job is to Answer ONLY using the context below. If unsure, say 'Not found'..

---CONTENT START---
{retrieved}
---CONTENT END---

Question: {query}

🧠 RESPONSE RULES:
1. If the question belongs to a **subject like Science or Social Science**, and a **definition** or **core concept** is found in the content, show that first.
2. If no definition is found, give a **30–40 word explanation** using the provided content.
3. Then, present **key takeaways or facts** as 2–3 bullet points (total 50–60 words).
4. Keep the total response under **150 words**.
5. Do not repeat content or add fluff.
6. Never answer using general knowledge — only use what's in the content block.

Format your response in a clean and structured way.
"""
    return prompt

    
def prompt_for_QnA2(query: str, session_id: str) -> str:
    """Generate prompt with context and chat history"""
    retrieved = retrieve_top_chunks_hybrid(query, 5, session_id)
    
    prompt = f"""
<|system|>
You are a concise teaching assistant specialized in Social Science and History. 
Answer using ONLY the provided context - never use general knowledge.

# CONTEXT
{retrieved}

# RESPONSE STRUCTURE
1. First: Briefly connect to previous topics (1 sentence)
2. Second: State core concept in bold (max 15 words)
3. Third: Provide 30-40 word explanation
4. Fourth: 2-3 bullet points of key insights
5. Use Markdown formatting

# FORMAT RULES
- Do NOT use section headers like "Relation" or "Core Concept"
- Do NOT mention "Key Insights" - just present bullet points
- Never include ending markers like "---END CONTENT---"
- Keep total response 120-150 words
- Maintain natural flow between sections

<|user|>
{query}
<|end|>
<|assistant|>
"""
    return prompt
    




# import time
# query = "Who was Mughals?"
session_id = "test_session"
# start_time = time.time()
# response = ask_phi3(query, session_id)
# end_time = time.time()
# latency = end_time - start_time
# print("Response:", response)
# print(f"Response time: {latency:.4f} seconds")

# Then loop or serve API
def get_llm_answer(user_input, session_id):
    prompt = prompt_for_QnA2(user_input, session_id)
    start = time.time()
    response = llm_instance(prompt, stop=["<|user|>", "<|end|>"], temperature=0.3, max_tokens=512)
    return response["choices"][0]["text"], time.time()-start

def unload_llm_Phi_3():
    """Release LLM resources and clean up memory"""
    global llm_instance
    
    if llm_instance is not None:
        print("Unloading LLM and releasing resources...")
        
        # 1. Explicitly delete the model instance
        del llm_instance
        
        # 2. Release GPU resources if possible
        try:
            if hasattr(Llama, 'free_gpu_resources'):
                Llama.free_gpu_resources()
                print("GPU resources released")
        except Exception as e:
            print(f"Error releasing GPU resources: {e}")
        
        # 3. Force garbage collection
        gc.collect()
        
        # 4. Reset global reference
        llm_instance = None
        print("LLM unloaded successfully")
    else:
        print("No LLM instance to unload")

def cleanup_resources():
    unload_llm_Phi_3()
# user_input = input("You: ")
# answer, latency1 = get_llm_answer(user_input, session_id)
# print("AI:", answer)
# print(f"Latency to get response from get_llm_anser; {latency1}")
# Verify Metal is active
# Safe way to check for Metal support
# 5. MAIN EXECUTION
# if __name__ == "__main__":
#     session_id = "test_session"
#     try:
#         llm = load_llm_silently(4096)
#         while True:
#             query = input("User:- ")
#             if query.lower() in ["exit", "quit"]:
#                 break
                
#             response, latency = get_llm_answer(query, session_id)
#             print(f"AI: {response}")
#             print(f"Latency: {latency:.2f} seconds\n")
#     finally:
#         cleanup_resources()  

