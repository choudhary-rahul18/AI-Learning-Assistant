from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import uuid
import asyncio
from datetime import datetime
import logging
import tempfile
import shutil
from functions import Video_Transcript, load_pdfs_from_folder, chunks_from_doc, embed_index_chunks_hybrid
from MCQs_with_LLM import *
from Ask_with_llm import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "user_session")
# Initialize FastAPI app FIRST
app = FastAPI(
    title="Educational Chatbot Platform",
    description="AI-powered learning assistant with quiz generation and Q&A chat",
    version="1.0.0"
)

# In fastapi_backend.py
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Global variables to store processed content
processed_content = {}
current_session_id = None
generated_quiz_cache = {} 

# Pydantic models for request/response
class YouTubeRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class QuizRequest(BaseModel):
    num_questions: int = 5
    session_id: Optional[str] = None

class QuizResponse(BaseModel):
    questions: List[dict]
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

class ProcessResponse(BaseModel):
    success: bool
    message: str
    session_id: str

class EvaluationRequest(BaseModel):
    session_id: str
    user_answers: List[str]

# Serve static files (your HTML frontend)
import os
STATIC_DIR = os.path.join(BASE_DIR, "static")
# Remove the existing static mount and add this:
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/process_youtube", response_model=ProcessResponse)
async def process_youtube_endpoint(request: YouTubeRequest):
    """Process YouTube URL and extract transcript"""
    try:
        global current_session_id, processed_content
        
        # Generate session ID
        session_id = f"session_{str(uuid.uuid4())}"
        current_session_id = session_id
        
        logger.info(f"Processing YouTube URL: {request.url}")
        
        # TODO: Replace with your actual YouTube processing function
        transcript = Video_Transcript(request.url)
        
        
        # TODO: Replace with your actual chunk creation and embedding storage
        chunks = chunks_from_doc(transcript)
        embed_index_chunks_hybrid(chunks, session_id)
        
        # Store processed content
        processed_content[session_id] = {
            "type": "youtube",
            "url": request.url,
            "content": transcript,
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"Successfully processed YouTube content for session: {session_id}")
        
        return ProcessResponse(
            success=True,
            message="YouTube content processed successfully!",
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error processing YouTube URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing YouTube URL: {str(e)}")

@app.post("/process_pdfs", response_model=ProcessResponse)
async def process_pdfs_endpoint(files: List[UploadFile] = File(...)):
    """Process uploaded PDF files"""
    try:
        global current_session_id, processed_content
        
        # Generate session ID
        session_id = f"session_{str(uuid.uuid4())}"
        current_session_id = session_id
        
        logger.info(f"Processing {len(files)} PDF files")
        
        # Create temporary directory for uploaded files
        temp_dir = tempfile.mkdtemp()
        uploaded_files = []
        
        try:
            # Save uploaded files
            for file in files:
                if not file.filename.endswith('.pdf'):
                    raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
                
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                uploaded_files.append(file_path)
            
            # TODO: Replace with your actual PDF processing function
            extracted_text = load_pdfs_from_folder(uploaded_files)
            
            
            # TODO: Replace with your actual chunk creation and embedding storage
            chunks = chunks_from_doc(extracted_text)
            embed_index_chunks_hybrid(chunks, session_id)
            
            # Store processed content
            processed_content[session_id] = {
                "type": "pdf",
                "files": [f.filename for f in files],
                "content": extracted_text,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully processed PDF files for session: {session_id}")
            
            return ProcessResponse(
                success=True,
                message=f"Successfully processed {len(files)} PDF files!",
                session_id=session_id
            )
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        logger.error(f"Error processing PDF files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF files: {str(e)}")



@app.post("/generate_quiz", response_model=List[dict])
async def generate_quiz_endpoint(request: QuizRequest):
    """Generate MCQ quiz questions based on processed content"""
    try:
        session_id = request.session_id or current_session_id

        if not session_id or session_id not in processed_content:
            raise HTTPException(status_code=400, detail="No processed content found. Please upload content first.")

        logger.info(f"Generating quiz with {request.num_questions} questions for session: {session_id}")

        # Step 1: Generate raw MCQs from LLM
        raw_mcqs = generate_mcqs_text_llm()

        # Step 2: Convert MCQs into JSON using LLM
        mcq_json_text = convert_mcqs_in_json_llm(MCQs=raw_mcqs)

        # Step 3: Extract clean JSON
        mcqs = extract_clean_json(mcq_json_text)

        # Step 4: Optional filtering/validation
        if len(mcqs) < request.num_questions:
            logger.warning("Not enough questions returned by LLM. Returning all available questions.")

        # Step 5: Add timestamp metadata
        final_questions = []
        for q in mcqs[:request.num_questions]:
            q["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            final_questions.append(q)

        # Step 6: Save only new questions to in-memory cache for evaluation
        generated_quiz_cache[session_id] = final_questions

        # Step 7: Append questions to persistent file for reference
        session_folder = os.path.join(BASE_DIR, "user_session", session_id)
        os.makedirs(session_folder, exist_ok=True)
        file_path = os.path.join(session_folder, "mcqs.json")

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        updated_data = existing_data + final_questions

        with open(file_path, "w") as f:
            json.dump(updated_data, f, indent=2)

        logger.info(f"Appended {len(final_questions)} questions and saved to {file_path}")

        return final_questions

    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz questions.")

@app.get("/get_quiz", response_model=List[dict])
async def get_quiz(session_id: str):
    """Retrieve the latest generated MCQs for the session"""
    try:
        if session_id not in generated_quiz_cache:
            raise HTTPException(status_code=404, detail="No quiz generated recently for this session")

        return generated_quiz_cache[session_id]

    except Exception as e:
        logger.error(f"Error retrieving quiz: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quiz questions.")

@app.post("/evaluate_quiz")
async def evaluate_quiz(request: EvaluationRequest):
    """Evaluate user's answers against the latest generated quiz"""
    try:
        if request.session_id not in generated_quiz_cache:
            raise HTTPException(status_code=404, detail="No quiz found to evaluate. Please generate quiz first.")

        latest_questions = generated_quiz_cache[request.session_id]
        correct_answers = [q["answer"] for q in latest_questions[:len(request.user_answers)]]
        score = sum(1 for user_ans, correct in zip(request.user_answers, correct_answers) if user_ans == correct)

        return {"score": score, "total": len(correct_answers)}

    except Exception as e:
        logger.error(f"Error evaluating quiz: {e}")
        raise HTTPException(status_code=500, detail="Failed to evaluate quiz.")

@app.get("/test-connection")
async def test_connection():
    return {
        "status": "success",
        "message": "Backend is running",
        "endpoints": [
            "/process_youtube",
            "/process_pdfs",
            "/generate_quiz",
            "/chat",
            "/health"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/download_mcqs")
async def download_mcqs(session_id: str):
    """Download the MCQ file for a session"""
    try:
        file_path = os.path.join(BASE_DIR, "user_session", session_id, "mcqs.json")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(file_path, media_type="application/json", filename="mcqs.json")

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file.")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat messages and provide responses"""
    try:
        session_id = request.session_id or current_session_id

        if not session_id or session_id not in processed_content:
            raise HTTPException(status_code=400, detail="No processed content found. Please upload content first.")

        logger.info(f"Processing chat message for session: {session_id}")

        # Use the actual RAG-based LLM function
        response = ask_llm(request.message, session_id)

        logger.info(f"Generated response for session: {session_id}")

        return ChatResponse(
            response=response,
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a specific session"""
    if session_id not in processed_content:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "content_info": processed_content[session_id],
        "status": "active"
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its processed content"""
    if session_id not in processed_content:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del processed_content[session_id]
    
    return {"message": f"Session {session_id} deleted successfully"}

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": list(processed_content.keys()),
        "total": len(processed_content)
    }


# Additional utility endpoints
@app.post("/upload_multiple_files")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Handle multiple file uploads (PDFs, docs, etc.)"""
    try:
        # Filter and validate files
        pdf_files = [f for f in files if f.filename.endswith('.pdf')]
        
        if not pdf_files:
            raise HTTPException(status_code=400, detail="No PDF files found in upload")
        
        # Process PDF files
        return await process_pdfs_endpoint(pdf_files)
        
    except Exception as e:
        logger.error(f"Error uploading multiple files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)
    # Run the server
    uvicorn.run(
        "fastapi_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
