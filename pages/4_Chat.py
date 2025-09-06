import streamlit as st
from streamlit_chat import message
from pathlib import Path
import os
import time
import json
from Ask_with_llm import prompt_for_QnA
import requests
import io

# Set page config
st.set_page_config(page_title="AI Learning Chat", layout="wide")

# Custom CSS with truly fixed input section + new features
st.markdown("""
<style>
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
        margin-bottom: 140px; /* Space for fixed input and buttons */
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 10px 15px;
        border-radius: 18px;
        margin: 5px 0;
        max-width: 70%;
        margin-left: auto;
    }
    .bot-message {
        background-color: #f1f1f1;
        padding: 10px 15px;
        border-radius: 18px;
        margin: 5px 0;
        max-width: 70%;
    }
    .stTextInput>div>div>input {
        border-radius: 20px;
        padding: 10px 15px;
    }
    .stButton>button {
        border-radius: 20px;
        padding: 10px 25px;
        background-color: #4CAF50;
        color: white;
        border: none;
    }
    .response-rules {
        font-size: 0.9rem;
        color: #666;
        border-left: 3px solid #4CAF50;
        padding-left: 10px;
        margin: 10px 0;
    }
    
    /* Add bottom padding to main content */
    .main-content {
        padding-bottom: 140px;
    }
    
    /* Hide the default chat input that moves */
    .main .block-container .stChatInput {
        display: none !important;
    }
    
    /* Fixed input container styling for the form */
    .fixed-form-input {
        position: fixed;
        bottom: 80px;
        left: 20px;
        right: 20px;
        background: white;
        padding: 15px;
        border-top: 1px solid #ddd;
        z-index: 1001;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        border-radius: 10px 10px 0 0;
    }
    
    .fixed-form-input > div {
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Enhanced input styling */
    .stTextInput > div > div > input {
        border-radius: 25px !important;
        padding: 12px 20px !important;
        border: 2px solid #ddd !important;
        font-size: 16px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4CAF50 !important;
        box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
    }
    
    /* Fixed bottom navigation */
    .fixed-bottom {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: white;
        padding: 15px 20px;
        border-top: 1px solid #ddd;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    
    /* TYPING INDICATOR ANIMATION */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 15px 20px;
        background: rgba(0,0,0,0.05);
        border-radius: 20px;
        margin: 10px 0;
        animation: fadeIn 0.3s ease-in;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #4CAF50;
        margin: 0 3px;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }
    
    @keyframes typing {
        0%, 80%, 100% { 
            transform: scale(0.8); 
            opacity: 0.5; 
        }
        40% { 
            transform: scale(1.2); 
            opacity: 1; 
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .typing-text {
        margin-left: 10px;
        color: #666;
        font-style: italic;
        font-size: 0.9rem;
    }
    
    /* EXPORT SECTION STYLING */
    .export-section {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 20px 0;
        border: 1px solid #e9ecef;
    }
    
    .export-button {
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Check session state and processing status
if 'processing_result' not in st.session_state or st.session_state.processing_result.get('status') != "processed":
    st.error("❌ No processed content found. Please start from the main page.")
    if st.button("Back to Main Page"):
        st.switch_page("app.py")
    st.stop()

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    welcome_message = {
        "role": "assistant", 
        "content": """Hello! I'm your AI teaching assistant. Ask me anything about the content you uploaded!"""
    }
    st.session_state.chat_history.append(welcome_message)

# TYPING INDICATOR FUNCTION
def show_typing_indicator():
    """Display typing indicator animation"""
    typing_html = """
    <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>
    """
    return st.markdown(typing_html, unsafe_allow_html=True)

# EXPORT CHAT HISTORY FUNCTION
def export_chat_history():
    """Generate exportable chat history"""
    if not st.session_state.chat_history:
        return "No chat history to export."
    
    export_text = f"AI Learning Chat Export\n"
    export_text += f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    export_text += "=" * 50 + "\n\n"
    
    for i, msg in enumerate(st.session_state.chat_history, 1):
        if msg["role"] != "latency":
            timestamp = time.strftime('%H:%M:%S', time.localtime())
            role_label = "👤 USER" if msg["role"] == "user" else "🤖 ASSISTANT"
            export_text += f"{i}. {role_label} [{timestamp}]:\n"
            export_text += f"{msg['content']}\n\n"
    
    export_text += "=" * 50 + "\n"
    export_text += f"Total messages: {len([m for m in st.session_state.chat_history if m['role'] != 'latency'])}\n"
    
    return export_text

def export_chat_as_json():
    """Export chat as structured JSON"""
    export_data = {
        "export_timestamp": time.time(),
        "export_date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "total_messages": len([m for m in st.session_state.chat_history if m['role'] != 'latency']),
        "chat_history": [msg for msg in st.session_state.chat_history if msg['role'] != 'latency']
    }
    return json.dumps(export_data, indent=2)

# Function to process streaming response
def process_streaming_response(response):
    """Process streaming response from Ollama API"""
    if response.status_code == 200:
        for line in response.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode('utf-8'))
                if chunk.get("done", False):
                    break
                token = chunk.get("response", "")
                if token:
                    yield token
            except json.JSONDecodeError:
                continue
    else:
        yield f"Error: {response.status_code} - {response.text}"

# Main content container
with st.container():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Header
    st.title("🤖 AI Learning Chat")
    st.write("Chat with the AI about your uploaded content")

    # Display chat messages
    for i, chat in enumerate(st.session_state.chat_history):
        if chat["role"] == "user":
            with st.chat_message("user"):
                st.markdown(chat["content"])
        elif chat["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(chat["content"])
        elif chat["role"] == "latency":
            st.markdown(f"<div class='response-rules'>{chat['content']}</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# SINGLE FIXED INPUT SECTION (Form-based - the working one)
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Message", 
            placeholder="Ask me anything about the content...", 
            label_visibility="collapsed",
            key="chat_input"
        )
    with col2:
        submit = st.form_submit_button("Send", type="primary")
    
    if submit and user_input.strip():
        prompt = user_input.strip()
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Get session ID from cookies
        session_id = st.session_state.get("cookies", {}).get("session_id")
        
        if not session_id:
            st.error("Session ID not found. Please restart the application.")
        else:
            # Process the message with typing indicator
            try:
                # Show typing indicator
                with st.chat_message("assistant"):
                    typing_placeholder = st.empty()
                    with typing_placeholder:
                        show_typing_indicator()
                    
                    conversation_history = st.session_state.chat_history[-4:-1] if len(st.session_state.chat_history) > 1 else []
                    retrieval_start = time.time()
                    query = prompt_for_QnA(query=prompt, session_id=session_id, chat_history=conversation_history)
                    retrieval_time = time.time() - retrieval_start
                    start = time.time()
                    
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "phi4-q4",      #llama3-14b-custom #phi4-q4
                            "prompt": query,
                            "stream": True,
                            "temperature": 0.3,
                            "top_p": 0.5
                        },
                        stream=True
                    )
                    
                    # Clear typing indicator and show response
                    typing_placeholder.empty()
                    full_response = st.write_stream(process_streaming_response(response))
                
                latency = time.time() - start
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": full_response
                })

                st.session_state.chat_history.append({
                    "role": "latency",
                    "content": f"⏱️ Context: {retrieval_time:.2f}s, Generation: {latency:.2f}s"
                })
                
                st.rerun()
                
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_message)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_message
                })
                st.rerun()

# EXPORT CHAT HISTORY SECTION (MOVED TO BOTTOM)
if len(st.session_state.chat_history) > 1:  # More than just welcome message
    with st.expander(" **Export Chat History**"):
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(" Download TXT", key="export_txt", help="Export as readable text file"):
                chat_text = export_chat_history()
                st.download_button(
                    label="Download Text File",
                    data=chat_text,
                    file_name=f"chat_export_{int(time.time())}.txt",
                    mime="text/plain",
                    key="download_txt"
                )
        
        with col2:
            if st.button(" Copy to Clipboard", key="copy_chat", help="View formatted text to copy"):
                st.text_area(
                    "Chat History (Copy this text):",
                    export_chat_history(),
                    height=200,
                    key="copy_area"
                )
        
        with col3:
            if st.button(" Download JSON", key="export_json", help="Export as structured JSON file"):
                chat_json = export_chat_as_json()
                st.download_button(
                    label=" Download JSON File",
                    data=chat_json,
                    file_name=f"chat_export_{int(time.time())}.json",
                    mime="application/json",
                    key="download_json"
                )
        
        # Show chat statistics
        message_count = len([m for m in st.session_state.chat_history if m['role'] != 'latency'])
        user_messages = len([m for m in st.session_state.chat_history if m['role'] == 'user'])
        bot_messages = len([m for m in st.session_state.chat_history if m['role'] == 'assistant'])
        
        st.info(f"**Chat Statistics:** {message_count} total messages ({user_messages} from you, {bot_messages} from AI)")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Navigation buttons at the very bottom
col1, col2 = st.columns(2)
with col1:
    if st.button("Back to Results", key="back_results"):
        st.switch_page("pages/2_Results.py")
with col2:
    if st.button("Back to Main Page", key="back_main"):
        st.switch_page("app.py")
