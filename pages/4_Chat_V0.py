import streamlit as st
from streamlit_chat import message
from pathlib import Path
import os
from Ask_with_llm import ask_llm  # Directly use your existing ask_llm function

# Set page config
st.set_page_config(page_title="AI Learning Chat", layout="wide")

# Custom CSS for the chat interface
st.markdown("""
<style>
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
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
        "content": """Hello! I'm your AI teaching assistant. Ask me anything about the content you uploaded!
"""
    }
    st.session_state.chat_history.append(welcome_message)

# Header
st.title("🤖 AI Learning Chat")
st.write("Chat with the AI about your uploaded content")

# Display chat messages
for i, chat in enumerate(st.session_state.chat_history):
    if chat["role"] == "user":
        message(chat["content"], is_user=True, key=f"user_{i}")
    elif chat["role"] == "assistant":
        message(chat["content"], key=f"assistant_{i}")
    elif chat["role"] == "latency":
        st.markdown(f"<div class='response-rules'>{chat['content']}</div>", unsafe_allow_html=True)


# Chat input area
col1, col2 = st.columns([5, 1])
with col1:
    user_input = st.text_input(
        "Type your question here...", 
        key="user_input",
        placeholder="Ask me anything about the content...",
        label_visibility="collapsed"
    )
with col2:
    send_button = st.button("Send", type="primary")

# Handle user input
if send_button and user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Get session ID from cookies
    session_id = st.session_state.get("cookies", {}).get("session_id")
    
    if not session_id:
        st.error("Session ID not found. Please restart the application.")
        st.stop()
    
   # Get AI response with conversation history
    with st.spinner("Thinking..."):
        try:
            # Send last 3 messages as history (excluding current prompt)
            conversation_history = st.session_state.chat_history[-3:-1] if len(st.session_state.chat_history) > 1 else []
            
            response, latency = ask_llm(
                query=user_input,
                session_id=session_id,
                chat_history=conversation_history
            )
            
            # Add assistant message
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })

            # Add latency as a separate light-styled message
            st.session_state.chat_history.append({
                "role": "latency",
                "content": f"⏱️ Answered in {latency:.2f} seconds"
            })
            
            # Rerun to update the chat display
            st.rerun()
            
        except Exception as e:
            st.error(f"Error getting response: {str(e)}")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Sorry, I encountered an error processing your request."
            })
            st.rerun()

# Navigation buttons
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("Back to Results"):
        st.switch_page("pages/2_Results.py")
with col2:
    if st.button("Back to Main Page"):
        st.switch_page("app.py")

# ------------------------


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
st.set_page_config(page_title="AI Learning Chat", layout="wide", page_icon="🤖")

# Modern CSS with glassmorphism and animated elements
st.markdown("""
<style>
    /* Base styles */
    body {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        margin-bottom: 140px;
    }
    
    /* Chat bubbles */
    .user-message {
        background: linear-gradient(135deg, #4a6bff 0%, #2d4dff 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 22px 22px 0 22px;
        margin: 15px 0 15px auto;
        max-width: 80%;
        box-shadow: 0 4px 15px rgba(74, 107, 255, 0.25);
        position: relative;
        animation: slideInRight 0.3s ease-out;
    }
    
    .user-message::after {
        content: '';
        position: absolute;
        bottom: 0;
        right: -10px;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-top-color: #2d4dff;
        border-bottom: 0;
        border-right: 0;
        margin-bottom: -10px;
    }
    
    .bot-message {
        background: white;
        color: #333;
        padding: 15px 20px;
        border-radius: 22px 22px 22px 0;
        margin: 15px 0;
        max-width: 80%;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        position: relative;
        animation: slideInLeft 0.3s ease-out;
    }
    
    .bot-message::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: -10px;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-top-color: white;
        border-bottom: 0;
        border-left: 0;
        margin-bottom: -10px;
    }
    
    /* Animations */
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Input area */
    .stTextInput>div>div>input {
        border-radius: 25px;
        padding: 14px 20px;
        font-size: 16px;
        border: 1px solid #e0e7ff;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #4a6bff;
        box-shadow: 0 0 0 3px rgba(74, 107, 255, 0.2);
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 25px;
        padding: 12px 28px;
        background: linear-gradient(135deg, #4a6bff 0%, #2d4dff 100%);
        color: white;
        border: none;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(74, 107, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(74, 107, 255, 0.4);
    }
    
    /* Fixed input container */
    .fixed-form-input {
        position: fixed;
        bottom: 80px;
        left: 20px;
        right: 20px;
        background: rgba(255, 255, 255, 0.92);
        padding: 15px;
        z-index: 1001;
        border-radius: 25px;
        box-shadow: 0 -5px 30px rgba(0, 0, 0, 0.08);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(224, 231, 255, 0.5);
        margin: 0 auto;
        max-width: 800px;
    }
    
    /* Fixed bottom navigation */
    .fixed-bottom {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(255, 255, 255, 0.95);
        padding: 15px 20px;
        z-index: 1000;
        box-shadow: 0 -5px 20px rgba(0, 0, 0, 0.05);
        backdrop-filter: blur(10px);
        border-top: 1px solid rgba(224, 231, 255, 0.8);
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 15px 20px;
        background: white;
        border-radius: 22px;
        margin: 15px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        max-width: 80%;
        animation: slideInLeft 0.3s ease-out;
    }
    
    .typing-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #4a6bff;
        margin: 0 4px;
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
    
    .typing-text {
        margin-left: 12px;
        color: #666;
        font-size: 0.95rem;
    }
    
    /* Export section */
    .export-section {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 18px;
        padding: 20px;
        margin: 25px 0;
        border: 1px solid rgba(224, 231, 255, 0.8);
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
    }
    
    .export-button {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(224, 231, 255, 0.8) !important;
        color: #4a6bff !important;
        margin: 8px 5px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Header styling */
    .header-container {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #4a6bff 0%, #2d4dff 100%);
        border-radius: 20px;
        color: white;
        box-shadow: 0 10px 30px rgba(74, 107, 255, 0.3);
    }
    
    /* Response rules */
    .response-rules {
        font-size: 0.9rem;
        color: #666;
        background: rgba(255, 255, 255, 0.9);
        padding: 12px 18px;
        border-radius: 18px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #4a6bff;
    }
    
    /* Layout adjustments */
    .main-content {
        padding-bottom: 140px;
    }
    
    .main .block-container .stChatInput {
        display: none !important;
    }
    
    /* Gradient background */
    .gradient-bg {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 300px;
        background: linear-gradient(135deg, #4a6bff 0%, #2d4dff 100%);
        z-index: -1;
        border-bottom-left-radius: 30%;
        border-bottom-right-radius: 30%;
    }
</style>
""", unsafe_allow_html=True)

# Background element
st.markdown('<div class="gradient-bg"></div>', unsafe_allow_html=True)

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
        <span class="typing-text">AI is generating response...</span>
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
    
    # Modern header
    st.markdown("""
    <div class="header-container">
        <h1 style="color:white; margin:0;">🤖 AI Learning Chat</h1>
        <p style="color:rgba(255,255,255,0.85); margin-top:8px;">Chat with the AI about your uploaded content</p>
    </div>
    """, unsafe_allow_html=True)

    # Display chat messages with new design
    for i, chat in enumerate(st.session_state.chat_history):
        if chat["role"] == "user":
            st.markdown(f'<div class="user-message">{chat["content"]}</div>', unsafe_allow_html=True)
        elif chat["role"] == "assistant":
            st.markdown(f'<div class="bot-message">{chat["content"]}</div>', unsafe_allow_html=True)
        elif chat["role"] == "latency":
            st.markdown(f'<div class="response-rules">{chat["content"]}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# SINGLE FIXED INPUT SECTION
with st.form("chat_form", clear_on_submit=True):
    with st.container():
        
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Message", 
                placeholder="Ask me anything about the content...", 
                label_visibility="collapsed",
                key="chat_input"
            )
        with col2:
            submit = st.form_submit_button("Send", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
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
                typing_placeholder = st.empty()
                with typing_placeholder:
                    show_typing_indicator()
                
                conversation_history = st.session_state.chat_history[-4:-1] if len(st.session_state.chat_history) > 1 else []
                query = prompt_for_QnA(query=prompt, session_id=session_id, chat_history=conversation_history)
                
                start = time.time()
                
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3-14b-custom",
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
                    "content": f"⏱️ Answered in {latency:.2f} seconds"
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

# EXPORT CHAT HISTORY SECTION
if len(st.session_state.chat_history) > 1:  # More than just welcome message
    with st.expander("📤 Export Chat History", expanded=False):
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download TXT", key="export_txt", help="Export as readable text file", use_container_width=True):
                chat_text = export_chat_history()
                st.download_button(
                    label="Download Text File",
                    data=chat_text,
                    file_name=f"chat_export_{int(time.time())}.txt",
                    mime="text/plain",
                    key="download_txt"
                )
        
        with col2:
            if st.button("📋 Copy to Clipboard", key="copy_chat", help="View formatted text to copy", use_container_width=True):
                st.text_area(
                    "Chat History (Copy this text):",
                    export_chat_history(),
                    height=200,
                    key="copy_area"
                )
        
        with col3:
            if st.button("📊 Download JSON", key="export_json", help="Export as structured JSON file", use_container_width=True):
                chat_json = export_chat_as_json()
                st.download_button(
                    label="Download JSON File",
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

# Navigation buttons at the bottom
col1, col2 = st.columns(2)
with col1:
    if st.button("⬅️ Back to Results", key="back_results", use_container_width=True):
        st.switch_page("pages/2_Results.py")
with col2:
    if st.button("🏠 Back to Main Page", key="back_main", use_container_width=True):
        st.switch_page("app.py")
st.markdown('</div>', unsafe_allow_html=True)