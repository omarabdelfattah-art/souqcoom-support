import streamlit as st
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
from dotenv import load_dotenv
import requests
import sys

# Print debug information
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")

# Load environment variables
load_dotenv()

# Initialize Mistral AI client
client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

# Get API key and print debug info (without showing the full key)
api_key = os.getenv("MISTRAL_API_KEY")
if api_key:
    print(f"API key found (starts with: {api_key[:4]}...)")
else:
    print("No API key found!")
    st.error("No API key found in .env file!")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="Souqcoom Support",
    page_icon="💬",
    layout="centered"
)

# Add custom CSS with animations
st.markdown("""
<style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-100%); }
        to { transform: translateX(0); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }
    
    .stChat {
        border-radius: 10px;
        padding: 20px;
        animation: fadeIn 0.5s ease-out;
    }
    
    .stTextInput {
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .stTextInput:focus {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        border-radius: 5px;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .support-header {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
        animation: slideIn 0.8s ease-out;
    }
    
    .support-description {
        background: linear-gradient(120deg, #f0f2f6, #e6e9ef, #f0f2f6);
        background-size: 200% 200%;
        animation: gradient 15s ease infinite;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .support-description:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .animate-typing {
        overflow: hidden;
        white-space: nowrap;
        animation: typing 3s steps(40, end);
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        animation: fadeIn 0.5s ease-out;
        transition: all 0.3s ease;
    }
    
    .chat-message:hover {
        transform: translateX(5px);
    }
    
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    
    .support-icon {
        font-size: 2.5rem;
        animation: pulse 2s infinite;
    }
    
    .sidebar-content {
        animation: fadeIn 1s ease-out;
    }
    
    .topic-item {
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .topic-item:hover {
        background-color: #f0f2f6;
        transform: translateX(10px);
    }
</style>

<script>
    // Add smooth scrolling to new messages
    const chatContainer = document.querySelector('.stChat');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
</script>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display header with animated icon
st.markdown('<div class="support-header">', unsafe_allow_html=True)
st.markdown('<span class="support-icon">💬</span>', unsafe_allow_html=True)
st.title("Souqcoom Support")
st.markdown("</div>", unsafe_allow_html=True)

# Display animated description
st.markdown('<div class="support-description">', unsafe_allow_html=True)
st.markdown("""
<div class="animate-typing">
Welcome to Souqcoom Support! I'm here to help you with:
</div>
<div class="topic-list">
<div class="topic-item">📋 Partnership Program Requirements</div>
<div class="topic-item">💰 Payment & Commission Information</div>
<div class="topic-item">🎯 Marketing Guidelines</div>
<div class="topic-item">🔒 Data Protection Policies</div>
<div class="topic-item">📦 Shipping & Returns</div>
</div>

<div class="animate-typing" style="margin-top: 1rem;">
Ask your question in English or Arabic (اسأل باللغة العربية أو الإنجليزية)
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Display chat messages with animation
for message in st.session_state.messages:
    message_class = "user-message" if message["role"] == "user" else "assistant-message"
    with st.chat_message(message["role"]):
        st.markdown(f'<div class="chat-message {message_class}">{message["content"]}</div>', unsafe_allow_html=True)

# Get user input with animated feedback
if prompt := st.chat_input("How can I help you with Souqcoom's services?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="chat-message user-message">{prompt}</div>', unsafe_allow_html=True)

    # Get AI response with animated loading
    with st.chat_message("assistant"):
        with st.spinner("✨ Finding the best answer for you..."):
            messages = [
                ChatMessage(role=m["role"], content=m["content"])
                for m in st.session_state.messages
            ]
            response = client.chat(
                model="mistral-small-latest",
                messages=messages,
                temperature=0.7,
            )
            response_content = response.choices[0].message.content
            st.markdown(f'<div class="chat-message assistant-message">{response_content}</div>', unsafe_allow_html=True)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_content})

# Add an animated sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.title("About Souqcoom Support")
    st.markdown("""
    ### 🕒 Hours of Operation
    <div class="topic-item">Our AI support assistant is available 24/7</div>
    
    ### 📚 Topics Covered
    <div class="topic-item">• Partnership Program</div>
    <div class="topic-item">• Account Management</div>
    <div class="topic-item">• Payments & Commissions</div>
    <div class="topic-item">• Marketing Guidelines</div>
    <div class="topic-item">• Technical Support</div>
    <div class="topic-item">• Data Protection</div>
    <div class="topic-item">• Shipping & Returns</div>
    
    ### 🌐 Languages Supported
    <div class="topic-item">• English (English)</div>
    <div class="topic-item">• Arabic (العربية)</div>
    
    ### 👥 Need Human Support?
    <div class="topic-item">📧 Email: support@souqcoom.com</div>
    <div class="topic-item">⏰ Response Time: Within 24 hours</div>
    
    ### 🔗 Quick Links
    <div class="topic-item">[Partnership Program](https://souqcoom.com/partners)</div>
    <div class="topic-item">[Terms & Conditions](https://souqcoom.com/terms)</div>
    <div class="topic-item">[Privacy Policy](https://souqcoom.com/privacy)</div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown('<div class="topic-item">*Powered by Mistral AI*</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
