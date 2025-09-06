from pathlib import Path
import streamlit as st
import requests
from io import BytesIO
import os
from functions import chunks_from_doc, embed_index_chunks_hybrid,delete_mcqs, delete_embeddings

PAGES_DIR = Path(__file__).parent / "pages"
RESULTS_PAGE = PAGES_DIR / "2_Results.py"
BACKEND_URL = "http://localhost:8000"
st.title("Let's Learn with AI")
st.subheader("Enter either PDF/YouTube URL to")

def show_processing_results(result_data, content_type):
    """Display results and offer next steps"""
    st.divider()
    st.subheader(f"Your {content_type} content is ready!")
    
    
    # Add your custom result display here
    if content_type == "PDF":
        st.write("PDF text extraction complete")
    else:
        st.write("YouTube processing complete")
    
    # Example action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Analyze Content"):
            st.session_state.current_action = "analyze"
            st.rerun()
    
    with col2:
        if st.button("Start Over"):
            st.session_state.current_action = None
            st.rerun()

# Track processing state
if 'current_action' not in st.session_state:
    st.session_state.current_action = None
if 'processing_result' not in st.session_state:
    st.session_state.processing_result = None


def initialize_session():
    """Initialize or get existing session"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/get-session/",
            cookies=st.session_state.get("cookies", {})
        )
        
        if response.status_code == 200:
            st.session_state.cookies = response.cookies.get_dict()
            return response.json()
        else:
            response = requests.get(
                f"{BACKEND_URL}/get-session/",
                allow_redirects=False
            )
            if response.status_code == 200:
                st.session_state.cookies = response.cookies.get_dict()
                st.rerun()
    except requests.ConnectionError:
        st.error("Backend connection failed. Please ensure the FastAPI server is running.")
        return None
    return None

# Initialize session
if "cookies" not in st.session_state or "session_id" not in st.session_state.get("cookies", {}):
    session_data = initialize_session()
else:
    session_data = {"status": "already initialized"}  # You can customize this
    session_id = st.session_state["cookies"]["session_id"]

session_id = st.session_state.get("cookies", {}).get("session_id")

if session_id:
    st.write(f"Session ID: `{session_id}`")
else:
    st.warning("No active session")

# PDF Upload and Processing Section
st.divider()

def handle_pdf_processing():
    if st.session_state.get('current_action'):
        return
        
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Process Files", type="primary"):
        with st.spinner("Processing PDFs..."):
            try:
                # Prepare files for upload
                files_to_send = [
                    ("files", (file.name, file.getvalue(), "application/pdf"))
                    for file in uploaded_files
                ]
                
                # Send to backend
                response = requests.post(
                    f"{BACKEND_URL}/process-pdfs/",
                    files=files_to_send,
                    cookies=st.session_state.get("cookies", {}),
                    timeout=30
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    
                    # Process the documents
                    try:
                        delete_embeddings(session_id)
                        delete_mcqs()
                        
                        # Get chunks directly from response
                        chunks = chunks_from_doc(results)
                        if not chunks:
                            raise ValueError("No chunks were generated from the documents")
                            
                        # Create embeddings
                        embed_index_chunks_hybrid(chunks, session_id)
                        
                        # Store minimal processing result
                        st.session_state.processing_result = {
                            "type": "pdf",
                            "status": "processed",
                            "file_count": len(uploaded_files)
                        }
                        
                        # Navigate to results page
                        st.switch_page("pages/2_Results.py")
                        
                    except Exception as processing_error:
                        st.error(f"Failed to process documents: {str(processing_error)}")
                        st.write("Debug - Problematic response:", results)
                
                else:
                    st.error(f"Backend error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
    
    elif not uploaded_files:
        st.info("Please upload PDF files to enable processing")

def upload_youtube_url():
    if st.session_state.get('current_action'):
        return
        
    youtube_url = st.text_input("Enter YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")
    
    if st.button("Process YouTube URL"):
        if not youtube_url:
            st.warning("Please enter a YouTube URL")
            return
        
        try:
            with st.spinner("Processing YouTube URL..."):
                response = requests.post(
                    f"{BACKEND_URL}/process-youtube/",
                    json={"url": youtube_url},
                    cookies=st.session_state.get("cookies", {}),
                    timeout=30  # Added timeout
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # Process the content
                    delete_embeddings(session_id)
                    delete_mcqs()
                    chunks = chunks_from_doc(results)
                    embed_index_chunks_hybrid(chunks, session_id)
                    
                    # PROPERLY set processing_result with status
                    st.session_state.processing_result = {
                        "type": "youtube",
                        "status": "processed",  # This is required
                        "data": results,       # Optional: store actual data if needed
                        "source": youtube_url  # Optional: for reference
                    }
                    
                    st.switch_page("pages/2_Results.py")
                else:
                    st.error(f"Processing failed: {response.text}")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
# Main flow control
if not st.session_state.current_action:
    upload_youtube_url()
    st.divider()
    handle_pdf_processing()
else:
    # Main flow control - REPLACE your current version with this:
    if not st.session_state.get('current_action'):

        upload_youtube_url()
        st.divider()
        handle_pdf_processing()
    else:
    # If coming back from results page, reset the action
        if st.session_state.current_action == "from_results_page":
            st.session_state.current_action = None
            st.rerun()

