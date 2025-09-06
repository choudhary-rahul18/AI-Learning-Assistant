from fastapi import FastAPI, Request, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime
from fastapi.responses import JSONResponse
from langchain.schema import Document
from io import BytesIO
import fitz  # PyMuPDF
from pydantic import BaseModel
from functions import Video_Transcript
# from functions import process_pdf_content
import io


app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage
sessions = {}

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session_id = request.cookies.get("session_id")
    
    # Create new session only for specific endpoints
    if request.url.path == "/get-session/" and not session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "upload_count": 0
        }
        response = JSONResponse({
            "session_id": session_id,
            "status": "new_session_created"
        })
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=3600*24*7,
            samesite="lax"
        )
        return response
    
    # For existing sessions
    if session_id in sessions:
        sessions[session_id]["last_accessed"] = datetime.now()
    
    return await call_next(request)

@app.get("/get-session/")
async def get_session(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return JSONResponse(
            {"error": "Session not found"}, 
            status_code=404
        )
    
    return {
        "session_id": session_id,
        "created_at": sessions[session_id]["created_at"],
        "last_accessed": sessions[session_id]["last_accessed"],
        "upload_count": sessions[session_id]["upload_count"]
    }

@app.post("/process-pdfs/")
async def process_pdfs_endpoint(request: Request, files: list[UploadFile] = File(...)):
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            return JSONResponse(
                {"error": "Session ID missing"},
                status_code=401
            )
        
        # Pass the list of files directly with await
        result = await process_pdf_content(files, session_id)
        
        return JSONResponse({
            "status": "success",
            "message": result
        })
    
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )
    
# Updated PDF processing functions
async def process_pdf_content(uploaded_files: list, session_id: str) -> str:
    """
    Process multiple in-memory PDF files asynchronously
    
    Args:
        uploaded_files: List of uploaded file objects
        session_id: Current session identifier
    
    Returns:
        Success message or raises error
    """
    documents = await process_pdf_files_updated(uploaded_files)
    
    if not documents:
        raise ValueError("No valid PDF files were processed.")
    else:
        # chunks = chunks_from_doc(documents)
        # embed = embed_index_chunks_hybrid(chunks, session_id)
        return f"{documents} PDF files processed successfully."

async def process_pdf_files_updated(uploaded_files: list) -> list:
    
    documents = []
    
    for file in uploaded_files:
        # Skip non-PDF files
        if not file.filename.lower().endswith('.pdf'):
            continue
            
        try:
            # Read file content asynchronously
            file_content = await file.read()
            
            # Create in-memory PDF stream
            with BytesIO(file_content) as pdf_stream:
                # Open PDF from memory
                with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
                    content = ""
                    # Extract text from each page
                    for page in doc:
                        content += page.get_text()
                    
                    # Create document with metadata
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={"source": file.filename}
                        )
                    )
        except Exception as e:
            print(f"Failed to process {file.filename}: {e}")
    
    return documents

from pydantic import BaseModel

class YouTubeRequest(BaseModel):
    url: str
    # Optional fields with default values
    quality: str = "high"
    duration_limit: int = 3600  # in seconds (1 hour default)
@app.post("/process-youtube/")
async def process_youtube(request: Request, data: YouTubeRequest):
    try:
        session_id = request.cookies.get("session_id") or data.session_id
        if not session_id:
            return JSONResponse(
                {"error": "Session ID missing"},
                status_code=401
            )
        
        text = Video_Transcript(video_url=data.url,Language='English')
        return text
        
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )            
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)