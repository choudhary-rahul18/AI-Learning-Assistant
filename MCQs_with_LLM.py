from functions import *
import requests
import json
import os
import time
from datetime import datetime
import random
import logging
import ast
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "user_session")

def prompt_for_mcq_generation(session_id, session_dir=SESSION_DIR):
    session_path = os.path.join(session_dir, session_id)
    # Load and data
    with open(os.path.join(session_path, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)

    # Handle cases with fewer than 20 chunks
    if len(chunks) <= 10:
        selected_chunks = chunks
    else:
        # Generate random start index with safe boundaries
        max_start = len(chunks) - 10
        start_index = random.randint(0, max_start)
        selected_chunks = chunks[start_index:start_index + 10]

    return f"""
    You are an expert MCQ generator. Create 5 multiple-choice questions all different from each other from the given context.

⚠️ Rules:
- Use only the context—no outside info.
- Each question must be 1 line (~20 words), with 4 believable options (A–D).
- Do not repeat options.
- Never write questions like:
  "What is the main theme of the passage?" or
  "According to the passage,...?"
- At the end, list the correct options only (e.g., Q1: A, Q2: D, ...).

📄 Context:
{selected_chunks[10:80] if len(selected_chunks) > 80 else selected_chunks}

📤 Output Format:
Q1. ...
A. ...
B. ...
C. ...
D. ...

✅ Answers:
Q1: B  
Q2: D  
Q3: A  
Q4: C  
Q5: B
"""

def get_extracted_topics(session_id):
    session_path = os.path.join(SESSION_DIR, session_id)
    chunk_path = os.path.join(session_path, "chunks.pkl")

    with open(chunk_path, "rb") as f:
        chunks = pickle.load(f)

    full_content = "\n\n".join(chunks)[:4000]  # Limit for small models

    prompt = f"""
    You must return only a Python list of 5 key topic titles from the content below.

    ---CONTENT---
    {full_content}
    ---END---

    ❌ Do NOT say anything else — no introductions, no formatting, no numbers.
    ✅ Just return a plain list like: ["Topic A", "Topic B", "Topic C", "Topic D", "Topic E"]
    """

    messages = [
        {{"role": "system", "content": "You are a strict extractor. Never explain or greet. Output must always be just a list of 5 strings in Python syntax."}},
         {{"role": "user", "content": prompt}}
    ]

    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3-14b-custom",
        "prompt": prompt,
        "stream": False,
        "temperature": 0.3,
        "top_p": 0.9
    })
    if response.status_code == 200:
        return response.json()["response"]
    else:
        print("Error:", response.status_code, response.text)
        return "Something went wrong!"

    return f"""
You are a JSON formatting machine. Your ONLY output must be pure JSON.

🚫 STRICT INSTRUCTIONS:
1. Output EXCLUSIVELY as JSON array with EXACTLY 5 objects
2. Each object MUST have these keys in order:
   - "question" (string)
   - "options" (object with keys "A", "B", "C", "D")
   - "answer" (one letter: "A", "B", "C", or "D")
3. FORBIDDEN in output:
   - Any text outside JSON array
   - Markdown code blocks (```json)
   - Explanations, comments, or notes
   - Missing fields or placeholder values
   - Single quotes (only double quotes allowed)
   - Trailing commas
   - Inconsistent indentation

💀 FAILURE CONDITIONS:
✖ Missing "answer" field
✖ Options without 4 choices (A-D)
✖ Answer not matching options
✖ Extra text before/after JSON

✅ REQUIRED FORMAT (JSON Schema):
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "minItems": 5,
  "maxItems": 5,
  "items": {{
    "type": "object",
    "properties": {{
      "question": {{"type": "string"}},
      "options": {{
        "type": "object",
        "properties": {{
          "A": {{"type": "string"}},
          "B": {{"type": "string"}},
          "C": {{"type": "string"}},
          "D": {{"type": "string"}}
        }},
        "required": ["A","B","C","D"],
        "additionalProperties": false
      }},
      "answer": {{"type": "string", "enum": ["A","B","C","D"]}}
    }},
    "required": ["question","options","answer"],
    "additionalProperties": false
  }}
}}

📝 INPUT QUESTIONS TO CONVERT:
{MCQs}

🖨️ OUTPUT (Pure JSON only - NO OTHER TEXT):
[
  {{
    "question": "Full question text here",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }},
    "answer": "X"
  }},
  // REPEAT FOR 5 TOTAL OBJECTS
]
"""


def generate_mcqs_text_llm(session_id, session_dir=SESSION_DIR):
    prompt = prompt_for_mcq_generation(session_id, session_dir)
    messages = [
        {"role": "system", "content": "You are an exam MCQ generator for teachers."},
        {"role": "user", "content": prompt}
    ]
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "lama3-14b-custom",
        "prompt": prompt,
        "stream": False,
        "temperature": 0.3,
        "top_p": 0.9

    })

    if response.status_code == 200:
        return response.json()["response"]
    else:
        print("Error:", response.status_code, response.text)
        return "Something went wrong!"

def create_mcqs_text_file(llm_response, session_id):
    """Save MCQ text to file, appending with separator if file exists"""
    try:
        # Ensure session directory exists
        os.makedirs(session_id, exist_ok=True)
        file_path = os.path.join(session_id, "MCQs.txt")

        # Prepare content with timestamp separator
        timestamp = datetime.now().strftime("\n\n[Generated on %Y-%m-%d at %H:%M:%S]\n")
        content = f"{timestamp}\n{llm_response.strip()}\n"

        # Append to existing file or create new file
        mode = 'a' if os.path.exists(file_path) else 'w'

        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)

        action = "Appended to" if mode == 'a' else "Created new"
        print(f"✅ {action} MCQ file at {file_path}")
        print(f"📝 Content length: {len(content)} characters")

        return True

    except Exception as e:
        print(f"❌ Error saving MCQ text: {e}")
        # Save raw response for debugging
        debug_path = os.path.join(session_id, "mcq_error.log")
        with open(debug_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n[{datetime.now()}] ERROR:\n{llm_response}")
        print(f"📝 Raw response saved to {debug_path}")
        return False

def preprocess_llm_output(text):
    """Remove any non-question text from LLM output"""
    # Find the first question marker
    start_index = text.find("**Question 1**")
    if start_index == -1:
        start_index = text.find("**Question1**")
    if start_index == -1:
        start_index = 0
    
    return text[start_index:]


def parse_output(text):
    """Ultra-robust parser that handles all variations of your LLM's MCQ format"""
    questions = []
    answers = []

    # Remove all **bold markers**
    text = text.replace("**", "")

    # Find all question blocks using multiple possible patterns
    question_blocks = re.findall(
        r'(?:Question \d+\.?|Q\d+:|\d+\.)\s*(.*?)(?=(?:Question \d+\.?|Q\d+:|\d+\.|\Z))',
        text,
        re.DOTALL
    )

    # Find all answers using multiple possible patterns
    answer_matches = re.findall(
        r'Answer[:]*\s*([A-D])\)?|\bCorrect(?: Answer)?:?\s*([A-D])\)?',
        text,
        re.IGNORECASE
    )

    # Extract answers from matches
    answers = [a[0] or a[1] for a in answer_matches][:5]

    # Process each question block
    for block in question_blocks[:5]:
        clean_block = block.strip()

        # Remove any answer remnants
        clean_block = re.sub(r'Answer:.*$', '', clean_block, flags=re.IGNORECASE)
        clean_block = re.sub(r'Correct Answer:.*$', '', clean_block, flags=re.IGNORECASE)

        # Standardize option formatting
        clean_block = re.sub(r'([A-D])[.)]\s*', r'\1) ', clean_block)

        # Remove any remaining asterisks (if any)
        clean_block = clean_block.replace("*", "")

        questions.append(clean_block)

    # Pad to 5 questions if needed
    while len(questions) < 5:
        questions.append("ERROR: Missing question")

    # Pad answers to 5 if needed
    while len(answers) < 5:
        answers.append("A")

    return questions[:5], answers[:5]

def MCQ_wrokflow(session_id, session_dir=SESSION_DIR):
    start = time.time()
    llm_response = generate_mcqs_text_llm(session_id, session_dir)
    latency = time.time()-start
    clean_text = preprocess_llm_output(llm_response)
    questions, answers = parse_output(clean_text)
    
    return questions, answers, latency, llm_response

def prompt_for_json_mcq_generation(session_id, session_dir=SESSION_DIR):
    session_path = os.path.join(session_dir, session_id)
    # Load and data
    with open(os.path.join(session_path, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)

    # Handle cases with fewer than 20 chunks
    if len(chunks) <= 10:
        selected_chunks = chunks
    else:
        # Generate random start index with safe boundaries
        max_start = len(chunks) - 10
        start_index = random.randint(0, max_start)
        selected_chunks = chunks[start_index:start_index + 10]

    return f"""
You are an expert MCQ generator. Create 5 multiple-choice questions from the given context.

⚠️ Rules:
- Use ONLY the provided context - no outside knowledge
- Each question must be 1 line (~20 words)
- Provide 4 plausible options (A-D) per question
- Never repeat questions or options
- Avoid question phrases like "What is the main theme..." or "According to the passage..."
- Output MUST be valid JSON format
- Include the correct answer key with each question

📄 Context:
{selected_chunks[10:80] if len(selected_chunks) > 80 else selected_chunks}

📤 Output Format:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Your first question?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "answer": "B"
    }},
    {{
      "id": 2,
      "question": "Your second question?",
      "options": {{
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      }},
      "answer": "A"
    }},
    // ... for 5 questions
}}
"""



# # Your workflow
# raw_text = generate_mcqs_text_llm(session_id='test_session')  # The generated text
# # clean_text = preprocess_llm_output(raw_text)
# # questions, answers = parse_output(clean_text)
# parsed_data = json.loads(raw_text) 
# json_text = clean_json(parsed_data)

# print(json_text)

# # print("--- Parsed Questions ---")
# # for i, q in enumerate(questions):
# #     print(f"Q{i+1}: {q}\n")
    
# # print("--- Answers ---")
# # for i in range(len(answers)):
    # print(f"Q{i+1}: {answers[i]}")