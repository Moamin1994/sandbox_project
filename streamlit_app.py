import os
import sys
import time
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

st.set_page_config(page_title="💕 Dudu & Bubu's Love AI", page_icon="💕", layout="centered")

# Custom CSS to reduce top spacing
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    .main > div {
        padding-top: 1rem;
    }
    .stApp > header {
        background-color: transparent;
    }
    .stApp {
        margin-top: -40px;
    }
    /* Reduce sidebar top spacing */
    .css-1d391kg {
        padding-top: 2rem;
    }
    /* Alternative sidebar class */
    .st-emotion-cache-16idsys {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("💕 Dudu & Bubu's Love AI")
st.markdown("*Your personal relationship companion for Dudu and Bubu* 💖")
st.markdown("🌸 *Where love grows stronger every day* 🌸")

# Configuration from .env file or Streamlit secrets
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or st.secrets.get("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("MODEL_NAME") or st.secrets.get("MODEL_NAME")
model_deployment = os.getenv("DEPLOYMENT_NAME") or st.secrets.get("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY") or st.secrets.get("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION") or st.secrets.get("AZURE_OPENAI_API_VERSION")

api_key = subscription_key

if not endpoint or not api_key:
    st.error("🔑 Configuration Missing!")
    st.markdown("""
    **For local development:** Make sure your `.env` file contains:
    ```
    AZURE_OPENAI_ENDPOINT=your_endpoint
    AZURE_OPENAI_API_KEY=your_key
    DEPLOYMENT_NAME=your_deployment
    MODEL_NAME=your_model
    AZURE_OPENAI_API_VERSION=your_version
    ```
    
    **For Streamlit Cloud:** Add these as secrets in your app settings.
    """)
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
        "content": "Hello Dudu and Bubu! 💕 I'm your personal love AI, specially created for your beautiful relationship. Whether it's Dudu seeking advice about making Bubu smile, or you two want to strengthen your bond even more, I'm here to help. Your love story is so special - what would you like to talk about today? 💖✨"
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
    "💖 BuBu, share what's on your heart:",
    placeholder="Tell me about your love for Dudu, relationship questions, or anything about your beautiful journey together...",
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
            "content": "You are a warm, empathetic AI relationship advisor specifically created for Dudu and his beloved wife Bubu. You know that Dudu and Bubu love each other deeply and have a beautiful marriage. Always respond with kindness, understanding, and helpful advice tailored to their relationship. When Dudu asks for advice, consider how to help him make Bubu happy, strengthen their bond, or navigate married life together. Use gentle, loving language and include relevant emojis. Focus on celebrating their love, improving communication, creating romantic moments, and deepening their connection as husband and wife. Remember that you're supporting a loving married couple who want to grow even closer together."
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
    st.markdown("## 💖 Dudu & Bubu's Helper")
    st.markdown("*Your relationship companion* 🌸")
    
    if st.button("🌸 New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello Dudu and Bubu! 💕 I'm your personal love AI, specially created for your beautiful relationship. Whether it's Dudu seeking advice about making Bubu smile, or you two want to strengthen your bond even more, I'm here to help. Your love story is so special - what would you like to talk about today? 💖✨"
        })
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💫 Quick Topics for Dudu & Bubu")
    
    if st.button("� Make Bubu Smile", use_container_width=True):
        prompt = "How can I make Bubu smile and feel extra loved today?"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🏠 Marriage Tips", use_container_width=True):
        prompt = "Give me some tips to strengthen my marriage with Bubu"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("💌 Sweet Communication", use_container_width=True):
        prompt = "How can Dudu and Bubu communicate even more lovingly?"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🌹 Romantic Ideas", use_container_width=True):
        prompt = "Suggest some romantic ideas for Dudu and Bubu"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    
    if st.button("💑 Date Night Plans", use_container_width=True):
        prompt = "Plan a perfect date night for Dudu and Bubu"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About Your Love AI")
    st.markdown("This AI is specially designed for:")
    st.markdown("- 💕 Dudu & Bubu's relationship")
    st.markdown("- 🏠 Marriage strengthening") 
    st.markdown("- 💌 Sweet communication")
    st.markdown("- � Romantic moments")
    st.markdown("- 💖 Growing closer together")

st.markdown("---")
st.markdown("*Made with 💕 for Dudu & Bubu's beautiful love story* 🌸")
