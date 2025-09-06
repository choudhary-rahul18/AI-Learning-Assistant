# AI-Powered Learning Assistant

A smart and interactive platform that transforms PDFs and YouTube videos into personalized study companions.
This project combines **Retrieval-Augmented Generation (RAG)**, semantic search, and quiz generation to create an engaging learning experience.

With this tool, you can:

* Upload PDFs or paste a YouTube link
* Ask questions directly about the content
* Generate practice quizzes with auto-created **MCQs**
* Use a web-based UI for interaction
* Access everything through a **FastAPI backend + Streamlit frontend**

---

## Key Features

 **Content Ingestion** – Upload PDF documents or extract transcripts from YouTube videos.
 **Hybrid Search** – Combines **semantic search (FAISS/ChromaDB)** with **keyword search (BM25)** for accurate retrieval.
 **Interactive Q\&A Chatbot** – Ask context-based questions; chatbot answers only from your uploaded material.
 **Automated MCQ Generation** – Create practice quizzes with configurable question counts.
 **Web UI with Streamlit** – Clean and intuitive interface for learners.
 **RESTful API with FastAPI** – Handles ingestion, embedding, retrieval, and LLM logic.

---

##  Getting Started

### Prerequisites

* Python **3.8+**
* An LLM service (e.g., **Ollama** running locally, or OpenAI/Anthropic if using API keys)

---

### 1. Installation

Clone the repository:

```bash
git clone [https://github.com/your-username/ai-learning-assistant.git](https://github.com/choudhary-rahul18/AI-Learning-Assistant/tree/main)
cd ai-learning-assistant
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 2. Environment Setup

Copy the sample configuration file and update values if needed:

```bash
cp env_config.txt .env
```

By default, the app works with **local models (Ollama)**.
If you want to use **cloud-based models** (OpenAI, Anthropic, etc.), add your API keys in `.env`.

---

### 3. Running the Application

Run the **backend (FastAPI)**:

```bash
uvicorn fastapi_backend:app --reload
```

The API will be available at:
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

Run the **frontend (Streamlit)**:

```bash
streamlit run app.py
```

The web app will be available at:
👉 [http://localhost:8501](http://localhost:8501)

---

##  How It Works

1. Open the Streamlit app in your browser.
2. Upload PDFs or enter a YouTube link.
3. The backend **chunks text**, creates embeddings, and stores them in the vector database.
4. Choose your workflow:

   * **Chat Mode** → Ask questions (uses `Ask_with_llm.py`)
   * **Practice Mode** → Generate MCQs (uses `MCQs_with_LLM.py`)
5. Results are retrieved only from your uploaded content.

---

##  Configuration

You can customize behavior via `.env`:

* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
* **LLM Model:** `gpt-3.5-turbo` (can be swapped for local/Ollama models)
* **Vector DB Options:** `chromadb`, `faiss`, `pinecone`
* **Quiz Settings:** default 5 questions, max 20
* **Chunking:** size = 1000, overlap = 200

---

## Project Structure

```
ai-learning-assistant/
│── app.py                # Streamlit frontend
│── fastapi_backend.py    # FastAPI backend
│── functions.py          # Core logic (ingestion, embeddings, retrieval)
│── Ask_with_llm.py       # Q&A chatbot logic
│── MCQs_with_LLM.py      # Quiz/MCQ generator
│── env_config.txt        # Sample environment config
│── requirements.txt      # Dependencies
│── uploads/              # Uploaded PDFs/videos
│── vector_db/            # Local vector storage
```

---

##  Roadmap

* [ ] Support for more file formats (PPT, DOCX)
* [ ] Adaptive quizzes (progress-based difficulty)
* [ ] Multi-user authentication & dashboards
* [ ] Analytics (quiz scores, learning insights)

---

##  Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

##  License

This project is licensed under the **MIT License**.

---

Do you want me to make this **minimal and beginner-friendly** (shortened, like a student project README), or keep it **detailed and professional** (like above, for GitHub portfolio)?
