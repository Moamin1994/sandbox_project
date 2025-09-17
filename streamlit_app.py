import os
import sys
import time
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

st.set_page_config(page_title="💕 Love & Relationship AI Advisor", page_icon="💕", layout="centered")

st.title("💕 Love & Relationship AI Advisor")
st.markdown("*Your personal AI companion for matters of the heart* 💖")

# Configuration from .env file
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("MODEL_NAME")
model_deployment = os.getenv("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

api_key = subscription_key

if not endpoint or not api_key:
    st.error("Endpoint or API key missing. Please check configuration.")
    st.stop()

# Initialize client (lazy)
@st.cache_resource
def get_client(ep: str, key: str, version: str):
    return AzureOpenAI(api_version=version, azure_endpoint=ep, api_key=key)

client = get_client(endpoint, api_key, api_version)

# Session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add a warm welcome message
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hello beautiful soul! 💕 I'm here to help you with all matters of love and relationships. Whether you need advice about dating, communication, or just want to talk about your feelings, I'm here for you. What's on your heart today? 💖"
    })

# Display chat history
st.markdown("### 💬 Chat")
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="💌"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar="💕"):
                st.markdown(message["content"])

# User input section
st.markdown("---")
user_input = st.text_area(
    "💖 Share what's on your heart:",
    placeholder="Tell me about your love life, relationship concerns, dating questions, or anything about matters of the heart...",
    height=100
)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    send_button = st.button("💕 Send Message", type="primary", use_container_width=True)

# Process user input
if send_button and user_input.strip():
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Prepare messages for API with love-focused system prompt
    api_messages = [
        {
            "role": "system",
            "content": "You are a warm, empathetic, and wise AI relationship advisor. You specialize in love, dating, relationships, and emotional support. Always respond with kindness, understanding, and helpful advice. Use gentle, loving language and include relevant emojis to make your responses feel warm and supportive. Focus on healthy relationships, communication, self-love, and emotional well-being."
        }
    ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    
    try:
        with st.spinner("💭 Thinking with love..."):
            response = client.chat.completions.create(
                model=model_deployment,
                messages=api_messages,
                temperature=float(os.getenv("TEMPERATURE", "1.0")),
                max_tokens=int(os.getenv("MAX_TOKENS", "1000")),
                top_p=float(os.getenv("TOP_P", "1.0"))
            )
            
        ai_response = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        # Rerun to show new messages
        st.rerun()
        
    except Exception as e:
        st.error(f"💔 Sorry, I encountered an issue: {e}")

# Sidebar with love-themed features
with st.sidebar:
    st.markdown("## 💖 Love Helper")
    
    if st.button("🌸 New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello beautiful soul! 💕 I'm here to help you with all matters of love and relationships. Whether you need advice about dating, communication, or just want to talk about your feelings, I'm here for you. What's on your heart today? 💖"
        })
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💫 Quick Topics")
    
    if st.button("💑 Dating Advice", use_container_width=True):
        prompt = "I'd like some dating advice"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("💕 Relationship Tips", use_container_width=True):
        prompt = "Can you give me some relationship tips?"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("💌 Communication Help", use_container_width=True):
        prompt = "How can I communicate better in my relationship?"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🌹 Self-Love Guidance", use_container_width=True):
        prompt = "Help me with self-love and confidence"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("This AI advisor is here to support you with:")
    st.markdown("- 💕 Relationship advice")
    st.markdown("- 💑 Dating guidance") 
    st.markdown("- 💌 Communication tips")
    st.markdown("- 🌸 Self-love & confidence")
    st.markdown("- 💖 Emotional support")

st.markdown("---")
st.markdown("*Made with 💕 for matters of the heart*")
