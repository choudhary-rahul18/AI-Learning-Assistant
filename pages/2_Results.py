import streamlit as st
from streamlit.components.v1 import html

# Set page config first
st.set_page_config(page_title="Processing Results", layout="wide")

# More robust check at the top of 2_Results.py
processing_result = st.session_state.get('processing_result', {})
# Only check for the minimal processing status
if not processing_result or processing_result.get('status') != "processed":
    st.error("❌ Processing not completed. Please start from the main page.")
    if st.button("Back to Main Page"):
        st.switch_page("app.py")
    st.stop()

# Now safely access the results
content_type = processing_result.get('type', 'content').upper()
# Safely get content type
content_type = st.session_state.processing_result.get('type', 'content').upper()


# Custom CSS for the buttons
st.markdown("""
<style>
    .big-button {
        height: 100px;
        width: 200px;
        font-size: 1.2rem;
        margin: 10px;
        border-radius: 15px;
        transition: all 0.3s ease;
    }
    .big-button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .center-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 30px;
    }
    .practice-btn {
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        color: white;
        border: none;
    }
    .chat-btn {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.subheader("So, You want to Practice or explore more about your topics.")

# Big centered buttons
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.markdown('<div class="center-container">', unsafe_allow_html=True)

    # Practice
    practice_clicked = st.button("🎯 Practice", key="practice_btn")
    if practice_clicked:
        st.session_state.current_action = "practice"
        st.switch_page("pages/3_Practice.py")

    # Chat
    chat_clicked = st.button("💬 Let's Chat", key="chat_btn")
    if chat_clicked:
        st.session_state.current_action = "chat"
        st.switch_page("pages/4_Chat.py")

    st.markdown('</div>', unsafe_allow_html=True)

# CSS for styling buttons
st.markdown("""
<style>
    .stButton > button {
        padding: 20px 40px;
        font-size: 1.2rem;
        font-weight: 600;
        border-radius: 15px;
        margin: 10px;
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        color: white;
        border: none;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        background: linear-gradient(135deg, #5d7de8, #9666d8);
        box-shadow: 0 12px 25px rgba(0,0,0,0.25);
    }
</style>
""", unsafe_allow_html=True)


# Existing analysis section
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("Analyze Content", type="primary"):
        st.session_state.current_action = "analyze"
        st.rerun()

with col2:
    if st.button("Back to Main Page"):
        st.session_state.current_action = "from_results_page"
        st.switch_page("app.py")

# Analysis content
if st.session_state.get('current_action') == "analyze":
    st.divider()
    st.subheader("Advanced Analysis")
    st.write("This is where you'd put analysis visualizations")
    
    if st.button("← Back to Results"):
        st.session_state.current_action = None
        st.rerun()