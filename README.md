# AI-Learning-Assistant
AI-Powered Learning Assistant
This project is a comprehensive platform that transforms educational content from PDFs and YouTube videos into an interactive learning experience. It leverages a Retrieval-Augmented Generation (RAG) architecture to provide a smart Q&A chatbot and an automated Multiple-Choice Question (MCQ) generator.

This is a smart chatbot and MCQ generator that uses Retrieval-Augmented Generation (RAG) to help you study. You can upload PDF files or give it a YouTube link, and it will let you ask questions or create practice quizzes based on that specific content.

Key Features
Content Ingestion: Process learning materials from both PDF files and YouTube video URLs.

Hybrid Search: Utilizes a combination of semantic (FAISS) and keyword-based (BM25) search for highly relevant context retrieval.

Interactive Q&A Chat: A conversational chatbot that answers questions based only on the provided content, complete with chat history memory.

Automated MCQ Generation: Dynamically creates practice quizzes from the source material to test user comprehension.

Web-Based UI: An intuitive and user-friendly interface built with Streamlit.

RESTful API: A robust backend powered by FastAPI to handle all processing and AI logic.

Getting Started
Prerequisites

Python 3.8+

An LLM service running (e.g., Ollama with the required models accessible at http://localhost:11434)

Installation

Clone the repository:

git clone [https://github.com/your-username/ai-learning-assistant.git](https://github.com/your-username/ai-learning-assistant.git)
cd ai-learning-assistant


Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`


Install the dependencies:

pip install -r requirements.txt


Set up environment variables:

This project does not require environment variables by default if you are using a local LLM like Ollama. If you switch to a cloud-based model, you can create a .env file from the .env.example template.

Running the Application

You need to run the backend and frontend in two separate terminals from the root directory.

Start the Backend API:

uvicorn fastapi_backend:app --reload


The API will be available at http://127.0.0.1:8000.

Run the Frontend App:

streamlit run app.py


The web application will be accessible at http://localhost:8501.

How It Works
Open the Streamlit application in your browser.

Upload one or more PDF files or enter a YouTube URL and click "Process".

The backend (fastapi_backend.py) receives the content. The logic in functions.py chunks the text and creates vector embeddings, which are saved locally in a user_session folder.

You are redirected to the Results page.

From here, you can either:

Go to Practice, which uses MCQs_with_LLM.py to generate and display a quiz.

Go to Chat, which uses Ask_with_llm.py to answer your questions based on the content.


