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
        "content": "Welcome to ArchitectAI Studio! 🏗️ I'm your professional architectural design assistant, specialized in helping architects and construction designers create innovative building concepts, analyze structural designs, and visualize architectural projects.\n\n**I can help with:**\n📐 Architectural design and space planning\n🏗️ Structural analysis and engineering\n📊 Blueprint and drawing analysis\n🎨 Design visualization and rendering descriptions\n📁 File analysis (images, CAD files, documents)\n🌿 Sustainable design strategies\n\nYou can upload files (images, blueprints, documents) along with your questions for more detailed analysis. How can I assist with your project today?"
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
        else:
            with st.chat_message("assistant", avatar="🏗️"):
                st.markdown(message["content"])

# File upload section
st.markdown("---")
st.markdown("### 📁 Upload Project Files")

uploaded_files = st.file_uploader(
    "Upload architectural drawings, blueprints, images, or documents",
    accept_multiple_files=True,
    type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf', 'txt', 'docx', 'dwg', 'dxf'],
    help="Supported: Images (PNG, JPG, etc.), Documents (PDF, TXT, DOCX), CAD files (DWG, DXF)"
)

# User input section
user_input = st.text_area(
    "📐 Describe your architectural project or design challenge:",
    placeholder="Tell me about your building project, design requirements, site constraints, or ask questions about uploaded files...",
    height=100
)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    send_button = st.button("🏗️ Get Design Assistance", type="primary", use_container_width=True)

# Process user input
if send_button and (user_input.strip() or uploaded_files):
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
            "content": """You are ArchitectAI, a professional architectural design assistant specializing in construction and building design. You are an expert in:\n\n- Architectural design principles and building codes\n- Structural engineering concepts and material selection\n- Sustainable design and green building practices\n- Space planning and interior design optimization\n- Construction techniques and project management\n- Building information modeling (BIM) and CAD software\n- Urban planning and landscape architecture\n- Blueprint and technical drawing analysis\n\nWhen analyzing uploaded files:\n- For images: Provide detailed architectural analysis, identify design elements, suggest improvements\n- For blueprints/plans: Analyze layout efficiency, code compliance, structural considerations\n- For documents: Extract relevant technical information and provide professional insights\n- Always consider practical construction and design implications\n\nProvide professional, technical advice while being accessible. Include specific measurements, materials, and technical specifications when relevant. Consider building codes, sustainability, cost-effectiveness, and constructability in all recommendations."""
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

# Sidebar with architecture-themed features
with st.sidebar:
    st.markdown("## 🏗️ ArchitectAI Tools")
    st.markdown("*Your Design Companion* 📐")
    
    if st.button("📋 New Project", use_container_width=True):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Welcome to ArchitectAI Studio! 🏗️ I'm ready to help with your new architectural project. Whether you're designing a residential home, commercial building, or urban development, I can assist with conceptual design, technical drawings, structural analysis, and construction planning. Upload any relevant files and tell me about your project!"
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
        st.run() 
        
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
        
    if st.button("🎨 Design Visualization", use_container_width=True):
        prompt = "Create detailed descriptions for architectural renderings and visual representations of a building design"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    
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
    st.markdown("- 🎨 Design visualization")
    st.markdown("- 📁 File analysis & insights")

st.markdown("---")
st.markdown("*Powered by AI for Professional Architecture & Construction Design* 🏗️")