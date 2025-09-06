import streamlit as st
from MCQs_with_LLM import MCQ_wrokflow

# Page config
st.set_page_config(
    page_title="Practice Questions",
    page_icon="📚",
    layout="wide"
)

# ✅ Reset navigation flag if returning to this page
if 'navigating' in st.session_state:
    del st.session_state['navigating']

# Header
st.title("📚 Practice Questions")
st.markdown("---")

# Ensure the user came from main page
if 'processing_result' not in st.session_state:
    st.error("No content found. Please start from the main page.")
    if st.button("Back to Main Page"):
        st.switch_page("app.py")
    st.stop()

# ----------------------------- #
# Function to generate and display questions
# ----------------------------- #
def generate_and_display_questions():
    with st.spinner("Generating practice questions..."):
        try:
            session_id = st.session_state.get("cookies", {}).get("session_id")
            st.session_state.questions, st.session_state.answers, st.session_state.latency, st.session_state.llm_response = MCQ_wrokflow(session_id)
        except Exception as e:
            st.error(f"Failed to generate questions: {str(e)}")
            st.stop()

# ----------------------------- #
# Generate MCQs Button"

if st.button("🎯 Generate MCQs"):
    st.session_state.questions = []
    st.session_state.answers = []
    generate_and_display_questions()

# ----------------------------- #
# Display Questions/Answers (if available)
# ----------------------------- #
if 'questions' in st.session_state and st.session_state.questions:
    st.subheader("Practice Questions")
    print(st.session_state.llm_response)
    print(st.session_state.questions)
    for i, question in enumerate(st.session_state.questions):
        print(f"Que-{i+1}:- {question}")
        st.markdown(f"""
        <div style='background-color:#f5f5f5; padding:15px; border-radius:10px; margin-bottom:15px'>
            <h4>Q{i+1}: {question}</h4>
        </div>
        """, unsafe_allow_html=True)
    # Show latency info
    if 'latency' in st.session_state:
        st.markdown(f"""
    <div style='text-align:right; font-size:14px; color:gray; margin-top: -10px;'>
        🕒 <em>Response generated in {st.session_state.latency:.3f} seconds</em>
    </div>
    """, unsafe_allow_html=True)

if 'answers' in st.session_state and st.session_state.answers:
    with st.expander("Show All Answers", expanded=False):
        for i, answer in enumerate(st.session_state.answers):
            st.markdown(f"""
            <div style='background-color:#e8f5e9; padding:10px; border-radius:8px; margin:5px 0'>
                <strong>Q{i+1}:</strong> {answer}
            </div>
            """, unsafe_allow_html=True)

# ----------------------------- #
# Navigation Buttons
# ----------------------------- #
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    with st.container():
        cols = st.columns(2)
        with cols[0]:
            if st.button("← Back to Results", use_container_width=True):
                st.session_state.navigating = True
                st.switch_page("pages/2_Results.py")
        with cols[1]:
            if st.button("Let's Chat →", use_container_width=True):
                st.session_state.navigating = True
                st.switch_page("pages/4_Chat.py")

# ----------------------------- #
# Styling
# ----------------------------- #
st.markdown("""
<style>
    div[data-testid="column"]:nth-of-type(1) button {
        background-color: #f5f5f5;
        color: #333;
        border: 1px solid #ddd;
    }
    div[data-testid="column"]:nth-of-type(1) button:hover {
        background-color: #e0e0e0;
    }
    div[data-testid="column"]:nth-of-type(2) button {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        color: white;
        border: none;
    }
    div[data-testid="column"]:nth-of-type(2) button:hover {
        background: linear-gradient(135deg, #3e9bed, #00e1ed);
    }
    div.stButton > button {
        height: 3em;
        font-weight: bold;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)
