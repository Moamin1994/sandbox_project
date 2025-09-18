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
    /* Image generation button styling */
    .stButton.image-gen > button {
        background-color: #FF6B35;
        color: white;
        border: none;
        border-radius: 5px;
    }
    .stButton.image-gen > button:hover {
        background-color: #E55A2B;
    }
    /* File upload styling */
    .uploadedFile {
        border: 2px dashed #2E8B57;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
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
dalle_deployment = os.getenv("DALLE_DEPLOYMENT_NAME") or st.secrets.get("DALLE_DEPLOYMENT_NAME", "dall-e-3")

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
    DALLE_DEPLOYMENT_NAME=your_dalle_deployment
    ```
    
    **For Streamlit Cloud:** Add these as secrets in your app settings.
    """)
    st.stop()

# Initialize client (lazy)
@st.cache_resource
def get_client(ep: str, key: str, version: str):
    return AzureOpenAI(api_version=version, azure_endpoint=ep, api_key=key)

client = get_client(endpoint, api_key, api_version)

# Image generation function
def generate_architectural_image(prompt):
    """Generate architectural images using DALL-E 3"""
    try:
        response = client.images.generate(
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

# File processing functions
def encode_image_to_base64(image_file):
    """Convert uploaded image to base64 string"""
    try:
        image = Image.open(image_file)
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large (max 2048x2048 for GPT-4V)
        max_size = 2048
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_base64}"
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def process_text_file(file):
    """Process uploaded text files"""
    try:
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        return content
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

# Session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add a professional welcome message
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Welcome to ArchitectAI Studio! 🏗️ I'm your professional architectural design assistant, specialized in helping architects and construction designers create innovative buildings and visualizations. I can help you with design consultations, analyze your files, and generate architectural images using DALL-E 3. How can I assist you today?"
    })

# Display chat history
st.markdown("### 💬 Design Consultation")
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👷"):
                # Display text content
                if "content" in message and isinstance(message["content"], str):
                    st.markdown(message["content"])
                # Display uploaded files info
                if "files" in message:
                    for file_info in message["files"]:
                        st.info(f"📎 Uploaded: {file_info['name']} ({file_info['type']})")
                # Display image generation request
                if "image_request" in message:
                    st.info(f"🎨 Image Generation Request: {message['image_request']}")
        else:
            with st.chat_message("assistant", avatar="🏗️"):
                st.markdown(message["content"])
                # Display generated images
                if "generated_image" in message:
                    st.image(message["generated_image"], caption="Generated Architectural Visualization", use_column_width=True)

# Mode selection
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    mode = st.radio(
        "🎯 Choose Mode:",
        ["💬 Chat & Analysis", "🎨 Image Generation"],
        horizontal=True
    )

# File upload section (only for chat mode)
if mode == "💬 Chat & Analysis":
    st.markdown("### 📁 Upload Project Files")
    uploaded_files = st.file_uploader(
        "Upload architectural drawings, blueprints, images, or documents",
        accept_multiple_files=True,
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf', 'txt', 'docx', 'dwg', 'dxf'],
        help="Supported: Images (PNG, JPG, etc.), Documents (PDF, TXT, DOCX), CAD files (DWG, DXF)"
    )

# User input section
if mode == "💬 Chat & Analysis":
    user_input = st.text_area(
        "📐 Describe your architectural project or design challenge:",
        placeholder="Tell me about your building project, design requirements, site constraints, or ask questions about uploaded files...",
        height=100
    )
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        send_button = st.button("🏗️ Get Design Assistance", type="primary", use_container_width=True)
        
else:  # Image Generation mode
    user_input = st.text_area(
        "🎨 Describe the architectural visualization you want to generate:",
        placeholder="Describe the building, architectural style, environment, materials, lighting, perspective, etc. Be as detailed as possible for better results...",
        height=120
    )
    
    # Image generation options
    col1, col2 = st.columns(2)
    with col1:
        style_preset = st.selectbox(
            "🏛️ Architectural Style:",
            ["Modern Contemporary", "Classical", "Art Deco", "Brutalist", "Minimalist", "Sustainable/Green", "Industrial", "Traditional", "Futuristic", "Custom (use description)"]
        )
    
    with col2:
        view_type = st.selectbox(
            "📐 View Type:",
            ["Exterior Perspective", "Interior View", "Aerial View", "Cross-Section", "Floor Plan Visualization", "Detail View", "Landscape Integration"]
        )
    
    # Generate image button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        generate_button = st.button("🎨 Generate Architectural Image", type="primary", use_container_width=True, key="generate_img")

# Process user input for chat mode
if mode == "💬 Chat & Analysis" and send_button and (user_input.strip() or uploaded_files):
    if not user_input.strip() and uploaded_files:
        user_input = "Please analyze the uploaded files and provide architectural insights."
    
    # Process uploaded files
    processed_files = []
    file_contents = []
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_info = {
                "name": uploaded_file.name,
                "type": uploaded_file.type,
                "size": uploaded_file.size
            }
            
            # Process images
            if uploaded_file.type.startswith('image/'):
                base64_image = encode_image_to_base64(uploaded_file)
                if base64_image:
                    file_contents.append({
                        "type": "image_url",
                        "image_url": {"url": base64_image}
                    })
                    file_info["processed"] = True
                    st.success(f"✅ Image processed: {uploaded_file.name}")
            
            # Process text files
            elif uploaded_file.type in ['text/plain', 'application/pdf'] or uploaded_file.name.endswith(('.txt', '.md')):
                text_content = process_text_file(uploaded_file)
                if text_content:
                    user_input += f"\n\n**Content from {uploaded_file.name}:**\n{text_content[:2000]}{'...' if len(text_content) > 2000 else ''}"
                    file_info["processed"] = True
                    st.success(f"✅ Text file processed: {uploaded_file.name}")
            
            # For other file types, just acknowledge upload
            else:
                file_info["processed"] = False
                st.info(f"📎 File uploaded: {uploaded_file.name} (file type noted for context)")
            
            processed_files.append(file_info)
    
    # Add user message with file info
    user_message = {"role": "user", "content": user_input}
    if processed_files:
        user_message["files"] = processed_files
    
    st.session_state.messages.append(user_message)
    
    # Prepare messages for API
    api_messages = [
        {
            "role": "system",
            "content": """You are ArchitectAI, a professional architectural design assistant specializing in construction and building design. You are an expert in:

- Architectural design principles and theory
- Building codes and regulations
- Structural engineering fundamentals
- Sustainable and green building practices
- Material selection and construction methods
- Site planning and urban design
- Interior design and space planning
- Project management and construction processes
- CAD software and technical drawings
- Building systems (HVAC, electrical, plumbing)
- Accessibility and universal design
- Historical and contemporary architectural styles

Provide detailed, professional advice with practical solutions. When analyzing uploaded files, focus on architectural elements, design principles, and construction feasibility. Always consider safety, building codes, sustainability, and cost-effectiveness in your recommendations."""
        }
    ]
    
    # Add conversation history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            # Create message content
            content = [{"type": "text", "text": msg["content"]}]
            
            # Add file contents if any images were processed
            if file_contents:
                content.extend(file_contents)
            
            api_messages.append({
                "role": "user",
                "content": content if len(content) > 1 else msg["content"]
            })
        else:
            api_messages.append({"role": "assistant", "content": msg["content"]})
    
    try:
        with st.spinner("🏗️ Analyzing your project and files..."):
            # Use different model endpoint if images are present
            if file_contents:
                # For vision capabilities, you might need GPT-4V
                response = client.chat.completions.create(
                    model=model_deployment,  # Ensure this supports vision if using images
                    messages=api_messages,
                    temperature=float(os.getenv("TEMPERATURE", "0.7")),
                    max_tokens=int(os.getenv("MAX_TOKENS", "1500"))
                )
            else:
                response = client.chat.completions.create(
                    model=model_deployment,
                    messages=api_messages,
                    temperature=float(os.getenv("TEMPERATURE", "0.7")),
                    max_tokens=int(os.getenv("MAX_TOKENS", "1500")),
                    top_p=float(os.getenv("TOP_P", "0.9"))
                )
            
        ai_response = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        # Clear file contents for next interaction
        file_contents = []
        
        # Rerun to show new messages
        st.rerun()
        
    except Exception as e:
        st.error(f"🔧 Sorry, I encountered a technical issue: {e}")
        st.error("Please check your model deployment supports the requested features (especially vision for images)")

# Process image generation
elif mode == "🎨 Image Generation" and generate_button and user_input.strip():
    # Enhance prompt with style and view information
    enhanced_prompt = user_input
    
    if style_preset != "Custom (use description)":
        enhanced_prompt += f" Architectural style: {style_preset}."
    
    enhanced_prompt += f" View type: {view_type}."
    
    # Add user message for image generation
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
            # Convert to PIL Image for display
            generated_image = Image.open(io.BytesIO(generated_image_data))
            
            # Add AI response with generated image
            ai_response = f"I've generated an architectural visualization based on your description: '{user_input}'\n\nStyle: {style_preset}\nView: {view_type}\n\nThe image shows a professional architectural rendering with attention to design details, materials, and spatial relationships."
            
            ai_message = {
                "role": "assistant", 
                "content": ai_response,
                "generated_image": generated_image
            }
            st.session_state.messages.append(ai_message)
            
            st.success("✅ Image generated successfully!")
            st.rerun()
        else:
            st.error("❌ Failed to generate image. Please try again with a different description.")
            
    except Exception as e:
        st.error(f"🔧 Sorry, I encountered an issue generating the image: {e}")
        st.error("Please check your DALL-E 3 deployment configuration.")

# Sidebar with architecture-themed features
with st.sidebar:
    st.markdown("## 🏗️ ArchitectAI Tools")
    st.markdown("*Your Design Companion* 📐")
    
    if st.button("📋 New Project", use_container_width=True):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Welcome to ArchitectAI Studio! 🏗️ I'm ready to help with your new architectural project. Whether you're designing a residential home, commercial building, or urban development, I can assist with consultations and generate visualizations. How can I help you today?"
        })
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏛️ Quick Design Tools")
    
    if st.button("🏠 Residential Design", use_container_width=True):
        prompt = "Help me design a modern residential house with sustainable features and optimal space planning"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🏢 Commercial Building", use_container_width=True):
        prompt = "Create a concept for a modern office building with efficient layout and green building features"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("📐 Floor Plan Analysis", use_container_width=True):
        prompt = "Analyze and optimize a floor plan for better flow, functionality, and space utilization"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🌿 Sustainable Design", use_container_width=True):
        prompt = "Suggest sustainable design strategies and green building techniques for an eco-friendly project"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🔧 Structural Analysis", use_container_width=True):
        prompt = "Provide structural engineering guidance and material recommendations for a building project"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
    if st.button("🎨 Generate Visualization", use_container_width=True):
        prompt = "A modern glass office building with sustainable features, surrounded by green landscaping, during golden hour"
        user_message = {
            "role": "user", 
            "content": "Generate architectural image: " + prompt,
            "image_request": prompt
        }
        st.session_state.messages.append(user_message)
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎨 Image Generation Features")
    st.markdown("**Styles:** Modern, Classical, Art Deco, Brutalist")
    st.markdown("**Views:** Exterior, Interior, Aerial, Cross-Section")
    st.markdown("**Quality:** HD 1024x1024 resolution")
    st.markdown("*Powered by DALL-E 3 for photorealistic renders*")
    
    st.markdown("---")
    st.markdown("### 📁 Supported File Types")
    st.markdown("**Images:** PNG, JPG, GIF, TIFF, BMP")
    st.markdown("**Documents:** PDF, TXT, DOCX")
    st.markdown("**CAD Files:** DWG, DXF")
    st.markdown("*Upload blueprints, site plans, sketches, or reference images*")
    
    st.markdown("---")
    st.markdown("### ℹ️ About ArchitectAI")
    st.markdown("This AI specializes in:")
    st.markdown("- 🏗️ Architectural design & planning")
    st.markdown("- 📐 Technical drawings & blueprints") 
    st.markdown("- 🌿 Sustainable construction")
    st.markdown("- 🔧 Structural engineering")
    st.markdown("- 🎨 AI-powered visualization")
    st.markdown("- 📁 File analysis & insights")

st.markdown("---")
st.markdown("*Powered by AI for Professional Architecture & Construction Design* 🏗️")