import os
import sys
import time
import requests
import streamlit as st
import base64
from PIL import Image
import io
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

st.set_page_config(page_title="🏗️ ArchitectAI Studio", page_icon="🏗️", layout="centered")

# Custom CSS for professional architectural theme
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
    /* Professional color scheme */
    .stButton > button {
        background-color: #2E8B57;
        color: white;
        border: none;
        border-radius: 5px;
    }
    .stButton > button:hover {
        background-color: #1F5F3F;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏗️ ArchitectAI Studio")
st.markdown("*Your Professional Architectural Design Assistant* 📐")
st.markdown("🏛️ *Where blueprints come to life with AI* 🏛️")

# Configuration from .env file or Streamlit secrets
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or st.secrets.get("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("MODEL_NAME") or st.secrets.get("MODEL_NAME")
model_deployment = os.getenv("DEPLOYMENT_NAME") or st.secrets.get("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY") or st.secrets.get("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION") or st.secrets.get("AZURE_OPENAI_API_VERSION")

# DALL-E specific configuration
dalle_deployment = "dall-e-3"
dalle_api_key = os.getenv("DALLE_API_KEY") or st.secrets.get("DALLE_API_KEY")

api_key = subscription_key

if not endpoint or not api_key or not dalle_api_key:
    st.error("🔑 Configuration Missing!")
    st.markdown("""
    **For local development:** Make sure your `.env` file contains:
    ```
    AZURE_OPENAI_ENDPOINT=your_endpoint
    AZURE_OPENAI_API_KEY=your_key
    DEPLOYMENT_NAME=your_deployment
    MODEL_NAME=your_model
    AZURE_OPENAI_API_VERSION=your_version
    DALLE_API_KEY=your_dalle_api_key
    ```
    
    **For Streamlit Cloud:** Add these as secrets in your app settings.
    """)
    st.stop()

# Initialize clients
@st.cache_resource
def get_client(ep: str, key: str, version: str):
    return AzureOpenAI(api_version=version, azure_endpoint=ep, api_key=key)

@st.cache_resource
def get_dalle_client(ep: str, key: str, version: str):
    return AzureOpenAI(api_version=version, azure_endpoint=ep, api_key=key)

client = get_client(endpoint, api_key, api_version)
dalle_client = get_dalle_client(endpoint, dalle_api_key, api_version)

# Image generation function
def generate_architectural_image(prompt):
    """Generate architectural images using DALL-E 3"""
    try:
        response = dalle_client.images.generate(
            model=dalle_deployment,
            prompt=f"Professional architectural visualization: {prompt}. High-quality, detailed, realistic architectural rendering style.",
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        image_url = response.data[0].url
        
        # Download the image
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            return img_response.content
        else:
            st.error(f"Failed to download generated image: {img_response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None

# Session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Welcome to ArchitectAI Studio! 🏗️ I'm your professional architectural design assistant. I can help you with design consultations, analyze architectural drawings, and generate stunning visualizations. What project are you working on today? 📐✨"
    })

# Mode selection
mode = st.selectbox(
    "🎯 Choose Your Mode:",
    ["💬 Design Consultation", "🎨 Image Generation"],
    index=0
)

# Display chat history
st.markdown("### 💬 Design Consultation")
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar="🏗️"):
                st.markdown(message["content"])
                # Display generated image if present
                if "generated_image" in message:
                    img = Image.open(io.BytesIO(message["generated_image"]))
                    st.image(img, caption="Generated Architectural Visualization", use_column_width=True)

# Input section based on mode
st.markdown("---")

if mode == "🎨 Image Generation":
    st.markdown("### 🎨 Architectural Visualization Generator")
    
    col1, col2 = st.columns(2)
    with col1:
        style_preset = st.selectbox(
            "🏛️ Architectural Style:",
            ["Modern", "Contemporary", "Classical", "Minimalist", "Sustainable/Green", "Industrial", "Custom (use description)"],
            index=0
        )
    
    with col2:
        view_type = st.selectbox(
            "📐 View Type:",
            ["Exterior perspective", "Interior view", "Floor plan", "Cross-section", "Aerial view", "Detail view"],
            index=0
        )
    
    user_input = st.text_area(
        "🏗️ Describe your architectural vision:",
        placeholder="Describe the building, space, or architectural element you want to visualize...",
        height=100
    )
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        generate_button = st.button("🎨 Generate Visualization", type="primary", use_container_width=True)

else:
    user_input = st.text_area(
        "🏗️ Share your architectural question or project:",
        placeholder="Ask about design principles, building codes, sustainable practices, or describe your project...",
        height=100
    )
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        send_button = st.button("💬 Send Message", type="primary", use_container_width=True)

# Process design consultation
if mode == "💬 Design Consultation" and 'send_button' in locals() and send_button and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    api_messages = [
        {
            "role": "system",
            "content": "You are a professional architectural design assistant with expertise in building design, construction, sustainability, and architectural principles. Provide helpful, detailed, and practical advice for architectural projects. Use architectural terminology appropriately and consider building codes, sustainability, and design best practices."
        }
    ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    
    try:
        with st.spinner("🏗️ Analyzing your architectural needs..."):
            response = client.chat.completions.create(
                model=model_deployment,
                messages=api_messages,
                temperature=0.7,
                max_tokens=1000
            )
            
        ai_response = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.rerun()
        
    except Exception as e:
        st.error(f"🔧 Sorry, I encountered a technical issue: {e}")

# Process image generation
elif mode == "🎨 Image Generation" and 'generate_button' in locals() and generate_button and user_input.strip():
    enhanced_prompt = user_input
    
    if style_preset != "Custom (use description)":
        enhanced_prompt += f" Architectural style: {style_preset}."
    
    enhanced_prompt += f" View type: {view_type}."
    
    user_message = {
        "role": "user", 
        "content": f"Generate architectural image: {user_input}",
        "image_request": enhanced_prompt
    }
    st.session_state.messages.append(user_message)
    
    try:
        with st.spinner("🎨 Generating architectural visualization..."):
            generated_image_data = generate_architectural_image(enhanced_prompt)
            
        if generated_image_data:
            generated_image = Image.open(io.BytesIO(generated_image_data))
            
            ai_response = f"I've generated an architectural visualization based on your description: '{user_input}'\n\nStyle: {style_preset}\nView: {view_type}\n\nThe image shows a professional architectural rendering that matches your specifications. 🏗️✨"
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": ai_response,
                "generated_image": generated_image_data
            })
            
            st.image(generated_image, caption="Generated Architectural Visualization", use_column_width=True)
            st.rerun()
        else:
            st.error("Failed to generate image. Please try again.")
            
    except Exception as e:
        st.error(f"🔧 Sorry, I encountered an issue generating the image: {e}")
        st.error("Please check your DALL-E deployment and API configuration.")

# Sidebar
with st.sidebar:
    st.markdown("## 🏗️ Architectural Tools")
    st.markdown("*Your design companion* 📐")
    
    if st.button("🌸 New Project", use_container_width=True):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Welcome to ArchitectAI Studio! 🏗️ I'm your professional architectural design assistant. I can help you with design consultations, analyze architectural drawings, and generate stunning visualizations. What project are you working on today? 📐✨"
        })
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎯 Quick Design Tools")
    
    if st.button("🏠 Residential Design", use_container_width=True):
        prompt = "Help me design a modern residential building with sustainable features"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🏢 Commercial Space", use_container_width=True):
        prompt = "Design ideas for a contemporary commercial office building"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🌆 Urban Planning", use_container_width=True):
        prompt = "Urban planning concepts for mixed-use development"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🌱 Sustainable Design", use_container_width=True):
        prompt = "Eco-friendly architectural design strategies and green building concepts"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About ArchitectAI")
    st.markdown("This AI assistant specializes in:")
    st.markdown("- 🏗️ Architectural design consultation")
    st.markdown("- 📐 Technical drawing analysis") 
    st.markdown("- 🎨 Design visualization generation")
    st.markdown("- 🌱 Sustainable building practices")
    st.markdown("- 📋 Project planning & guidance")

st.markdown("---")
st.markdown("*Built with 🏗️ for architectural excellence* 📐")
