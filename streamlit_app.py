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
import asyncio
from datetime import datetime

# Load environment variables first before any other setup
load_dotenv()

# Setup OpenTelemetry tracing for Azure AI Foundry dashboard
try:
    from setup_tracing import setup_azure_tracing
    setup_azure_tracing()
except Exception as e:
    print(f"⚠️ Could not setup OpenTelemetry tracing: {e}")

# Multi-Agent Architecture imports (old local agents - removed)
MULTI_AGENT_AVAILABLE = False
MULTI_AGENT_TYPE = "removed"
print("Local multi-agent system removed - using Azure AI Foundry agents only")

# Azure AI Foundry Agents imports
try:
    from intelligent_orchestrator import IntelligentOrchestrator
    AZURE_FOUNDRY_AVAILABLE = True
    print("✅ Using Intelligent Azure OpenAI agents with collaboration (GPT-4o for agents, GPT-5 for output)")
except ImportError as e:
    AZURE_FOUNDRY_AVAILABLE = False
    print(f"❌ Could not import fixed Azure agents: {e}")

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

# FLUX.1-Kontext-pro specific configuration (separate resource)
flux_deployment = "FLUX.1-Kontext-pro"
flux_api_key = os.getenv("FLUX_API_KEY") or st.secrets.get("FLUX_API_KEY")
flux_endpoint = os.getenv("FLUX_ENDPOINT") or st.secrets.get("FLUX_ENDPOINT")

# Fallback configuration if environment variables aren't loaded
if not flux_endpoint:
    flux_endpoint = "https://chatproject100.cognitiveservices.azure.com/openai/deployments/FLUX.1-Kontext-pro/images/generations?api-version=2024-12-01-preview"
if not flux_api_key:
    flux_api_key = None  # Must be provided via environment or secrets

api_key = subscription_key

if not endpoint or not api_key or not flux_api_key or not flux_endpoint:
    st.error("🔑 Configuration Missing!")
    st.markdown("""
    **For local development:** Make sure your `.env` file contains:
    ```
    # Chat Configuration
    AZURE_OPENAI_ENDPOINT=your_chat_endpoint
    AZURE_OPENAI_API_KEY=your_chat_key
    DEPLOYMENT_NAME=your_deployment
    MODEL_NAME=your_model
    AZURE_OPENAI_API_VERSION=your_version
    
    # FLUX Configuration (separate resource)
    FLUX_API_KEY=your_flux_key
    FLUX_ENDPOINT=your_flux_endpoint
    ```
    
    **For Streamlit Cloud:** Add these as secrets in your app settings.
    """)
    st.stop()

# Initialize clients
@st.cache_resource
def get_client(ep: str, key: str, version: str):
    if ep and key and version:
        return AzureOpenAI(api_version=version, azure_endpoint=ep, api_key=key)
    return None

@st.cache_resource
def get_flux_client(ep: str, key: str, version: str):
    if ep and key and version:
        return AzureOpenAI(api_version=version, azure_endpoint=ep, api_key=key)
    return None

# Initialize Multi-Agent Orchestrator
@st.cache_resource
def get_orchestrator(agent_type="azure"):
    """Get orchestrator based on agent type selection"""
    if agent_type == "azure" and AZURE_FOUNDRY_AVAILABLE:
        try:
            return IntelligentOrchestrator()
        except Exception as e:
            st.warning(f"⚠️ Intelligent Azure agents initialization failed: {e}")
            return None
    elif agent_type == "local":
        st.warning("⚠️ Local multi-agent system has been removed. Please use Azure agents.")
        return None
    return None

# Initialize with Fixed Azure orchestrator by default
orchestrator = None
if AZURE_FOUNDRY_AVAILABLE:
    try:
        orchestrator = IntelligentOrchestrator()
    except Exception as e:
        print(f"Failed to initialize Intelligent Azure orchestrator: {e}")
        orchestrator = None

# Debug: Print configuration values (remove these lines once everything works)
# st.write(f"🔧 Debug - Azure OpenAI Endpoint: {endpoint}")
# st.write(f"🔧 Debug - API Key exists: {bool(api_key)}")
# st.write(f"🔧 Debug - API Version: {api_version}")

# Only create client if we have valid configuration
client = None
if endpoint and api_key and api_version:
    client = get_client(endpoint, api_key, api_version)
else:
    st.warning("⚠️ Azure OpenAI configuration incomplete - GPT-4 Vision features will be disabled")

# Note: We now use direct HTTP requests to FLUX API instead of OpenAI client

# Image analysis function using GPT-4 Vision
def analyze_image_with_gpt4_vision(image_file):
    """Analyze uploaded image using GPT-4 Vision to understand its content"""
    try:
        # Check if we have a valid client for GPT-4 Vision
        if not client:
            st.warning("GPT-4 Vision analysis not available - using image without analysis")
            return None
            
        # Convert uploaded file to base64
        image = Image.open(image_file)
        
        # Resize if too large for better processing
        max_size = 1024
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to base64
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Use GPT-4 Vision to analyze the image
        response = client.chat.completions.create(
            model=model_deployment,  # Make sure this is a vision-capable model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this architectural image in detail. Describe:
1. Type of space (interior/exterior, room type, building type)
2. Architectural style and design elements
3. Materials, colors, and textures visible
4. Layout, proportions, and spatial organization
5. Lighting conditions and atmosphere
6. Key architectural features and details

Provide a comprehensive description that could be used to generate a similar architectural visualization."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"Error analyzing image: {e}")
        return None

# Multi-Agent Processing Function
async def process_with_multi_agents(user_text, uploaded_files=None, architectural_style=None, view_type=None, agent_type="local"):
    """Process request using the multi-agent system (local or Azure AI Foundry)"""
    
    # Get the appropriate orchestrator
    current_orchestrator = get_orchestrator(agent_type)
    
    if not current_orchestrator:
        return None
    
    # Convert uploaded files to bytes if present
    image_bytes_list = None
    if uploaded_files is not None and len(uploaded_files) > 0:
        image_bytes_list = []
        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.read()
            image_bytes_list.append(file_bytes)
            uploaded_file.seek(0)  # Reset file pointer
    
    # Initialize Azure AI Foundry agents if needed
    if agent_type == "azure" and hasattr(current_orchestrator, 'initialize_agents'):
        init_success = await current_orchestrator.initialize_agents()
        if not init_success:
            st.error("❌ Failed to initialize Azure AI Foundry agents")
            return None
    
    # Build conversation context for caching (Azure AI Foundry)
    conversation_context = ""
    if agent_type == "azure":
        # Add previous conversation history for context-aware caching
        if 'messages' in st.session_state and len(st.session_state.messages) > 1:
            recent_messages = st.session_state.messages[-3:]  # Last 3 messages
            for msg in recent_messages:
                if msg.get('role') == 'user':
                    conversation_context += f"User: {msg.get('content', '')[:100]}... "
                elif msg.get('role') == 'assistant':
                    conversation_context += f"Assistant: {msg.get('content', '')[:100]}... "
    
    # Process with multi-agent system
    if agent_type == "azure":
        # Intelligent Azure orchestrator with dynamic routing and agent collaboration
        session_id = f"session_{int(time.time())}"  # Create unique session ID
        if conversation_context:
            enhanced_user_text = f"[CONVERSATION_CONTEXT: {conversation_context}]\n\nCURRENT_REQUEST: {user_text}"
        else:
            enhanced_user_text = user_text
        
        result = await current_orchestrator.process_request(
            user_message=enhanced_user_text,
            user_images=image_bytes_list,
            session_id=session_id
        )
    else:
        # Local orchestrator - keep existing single image support for now
        first_image = image_bytes_list[0] if image_bytes_list and len(image_bytes_list) > 0 else None
        result = await current_orchestrator.process_request(
            user_text=user_text,
            user_image=first_image,
            architectural_style=architectural_style,
            view_type=view_type
        )
    
    return result

def display_workflow_results(result, agent_type="local"):
    """Display multi-agent workflow results (local or Azure AI Foundry)"""
    if not result:
        return
    
    if agent_type == "azure":
        # Intelligent Azure AI orchestrator results format
        final_output = result.get('final_output', {})
        if final_output.get('agent_collaboration'):
            st.success("✅ Intelligent Multi-Agent Processing with Collaboration Completed!")
            
            # Show intelligent routing performance
            if final_output.get('intelligent_routing'):
                st.info("🧠 **Intelligent Routing**: Dynamic workflow with agent collaboration and handoffs")
            
            # Workflow summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                workflow_tasks = final_output.get('workflow_executed', [])
                st.metric("Tasks Executed", len(workflow_tasks))
            with col2:
                confidence = final_output.get('confidence_score', 0)
                st.metric("Confidence", f"{confidence:.2f}")
            with col3:
                st.metric("Collaboration", "✅ Active" if final_output.get('agent_collaboration') else "❌ None")
            with col4:
                st.metric("Routing", "🤖 Intelligent" if final_output.get('intelligent_routing') else "📋 Fixed")
            
            # Intelligent orchestrator agent responses
            with st.expander("🤖 Intelligent Agent Collaboration Results", expanded=True):
                all_results = result.get('all_results', {})
                
                # Display results in execution order
                task_order = {
                    'VISION_ANALYSIS': 1,
                    'ARCHITECTURAL_CONSULTATION': 2, 
                    'STYLE_ANALYSIS': 3,
                    'TECHNICAL_REVIEW': 4,
                    'PROMPT_ENGINEERING': 5,
                    'QUALITY_ASSURANCE': 6
                }
                
                sorted_results = sorted(all_results.items(), 
                                      key=lambda x: task_order.get(x[0].name, 99))
                
                for task_type, content in sorted_results:
                    agent_name = task_type.name.replace('_', ' ').title()
                    
                    st.markdown(f"**{agent_name} Agent:**")
                    if content:
                        # Try to parse JSON format first
                        try:
                            import json
                            if content.strip().startswith('{'):
                                parsed = json.loads(content)
                                for key, value in parsed.items():
                                    if isinstance(value, list):
                                        st.markdown(f"- **{key.title()}**: {', '.join(map(str, value))}")
                                    else:
                                        st.markdown(f"- **{key.title()}**: {value}")
                            else:
                                st.markdown(content)
                        except:
                            # Fallback to plain text
                            st.markdown(content)
                    st.markdown("---")
                
                # Final extracted results
                st.markdown("### 📋 Final Consultation Results")
                
                if final_output.get('architectural_analysis'):
                    st.markdown("**🔍 Vision Analysis:**")
                    st.text_area("", final_output['architectural_analysis'], height=100, key="azure_vision")
                
                if final_output.get('expert_consultation'):
                    st.markdown("**🏗️ Expert Consultation:**")
                    st.text_area("", final_output['expert_consultation'], height=100, key="azure_arch")
                
                if final_output.get('style_analysis'):
                    st.markdown("**🎨 Style Analysis:**")
                    st.text_area("", final_output['style_analysis'], height=100, key="azure_style")
                
                if final_output.get('technical_review'):
                    st.markdown("**⚙️ Technical Review:**")
                    st.text_area("", final_output['technical_review'], height=100, key="azure_tech")
                
                if final_output.get('optimized_prompt'):
                    st.markdown("**✨ Optimized FLUX Prompt:**")
                    st.text_area("", final_output['optimized_prompt'], height=100, key="azure_prompt")
                    
                    # Copy button for the optimized prompt
                    if st.button("📋 Copy Optimized Prompt", key="copy_azure_prompt"):
                        st.code(final_output['optimized_prompt'])
                        st.success("✅ Prompt displayed above - you can now copy it!")
                
                if final_output.get('quality_review'):
                    st.markdown("**✅ Quality Assurance:**")
                    st.text_area("", final_output['quality_review'], height=100, key="azure_qa")
        else:
            st.error(f"❌ Intelligent Azure orchestrator processing failed: {result.get('error', 'Unknown error')}")
    
    else:
        # Local agent results format
        if result and result.get('success'):
            st.success("✅ Local Multi-Agent Processing Completed!")
            
            # Workflow summary
            summary = result.get('processing_summary', {})
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Agents", summary.get('total_agents', 0))
            with col2:
                st.metric("Confidence", f"{summary.get('average_confidence', 0):.2f}")
            with col3:
                st.metric("Time", f"{summary.get('execution_time', 0):.1f}s")
            with col4:
                ready = result.get('final_output', {}).get('ready_for_image_generation', False)
                st.metric("Ready", "✅" if ready else "❌")
            
            # Local agent responses in expander
            with st.expander("🤖 Agent Responses", expanded=True):
                agent_responses = result.get('agent_responses', {})
                
                for agent_name, response in agent_responses.items():
                    st.markdown(f"**{agent_name}:**")
                    st.info(response.get('content', 'No response content'))
                    st.caption(f"Confidence: {response.get('confidence', 0):.2f} | "
                             f"Processing Time: {response.get('processing_time', 0):.2f}s")
                    st.markdown("---")
                
                # Final output
                final_output = result.get('final_output', {})
                if final_output:
                    st.markdown("### 📋 Final Output")
                    
                    if final_output.get('optimized_prompt'):
                        st.markdown("**✨ Optimized Prompt for Image Generation:**")
                        st.text_area("", final_output['optimized_prompt'], height=100, key="local_prompt")
                        
                        if st.button("📋 Copy Optimized Prompt", key="copy_local_prompt"):
                            st.code(final_output['optimized_prompt'])
                            st.success("✅ Prompt displayed above - you can now copy it!")
                    
                    if final_output.get('architectural_analysis'):
                        st.markdown("**🏗️ Architectural Analysis:**")
                        st.text_area("", final_output['architectural_analysis'], height=100, key="local_analysis")
        else:
            st.error(f"❌ Local multi-agent processing failed: {result.get('error', 'Unknown error') if result else 'No result returned'}")
        with st.expander("🤖 Agent Analysis Details"):
            for i, response in enumerate(result.get('agent_responses', [])):
                agent_name = response.get('agent_type', '').replace('_', ' ').title()
                st.markdown(f"**{i+1}. {agent_name}**")
                st.write(response.get('content', ''))
                st.caption(f"Confidence: {response.get('confidence', 0):.2f}")
                st.markdown("---")
        
        # Return optimized prompt
        final_output = result.get('final_output', {})
        return final_output.get('optimized_prompt', '')
    
    return None

# Image generation function
def generate_architectural_image(prompt, reference_image=None):
    """Generate architectural images using FLUX.1-Kontext-pro via direct API calls"""
    try:
        if reference_image is not None:
            # First, analyze the uploaded image with GPT-4 Vision
            with st.spinner("🔍 Analyzing your reference image..."):
                image_analysis = analyze_image_with_gpt4_vision(reference_image)
            
            if image_analysis:
                # Create enhanced prompt based on image analysis + user modifications
                enhanced_prompt = f"""Professional architectural visualization based on this analysis:

IMAGE ANALYSIS: {image_analysis}

USER MODIFICATIONS: {prompt}

Create a new architectural visualization that maintains the spatial type, style, and key characteristics described in the analysis, while incorporating the user's requested modifications. Ensure high-quality, detailed, realistic architectural rendering style."""
                
                st.info(f"🔍 **Image Analysis:** {image_analysis[:200]}..." if len(image_analysis) > 200 else f"🔍 **Image Analysis:** {image_analysis}")
            else:
                # Fallback if image analysis fails
                enhanced_prompt = f"""Professional architectural visualization with these specifications: {prompt}. 
                Style: Create a detailed architectural rendering that incorporates modern design principles.
                Quality: High-resolution, photorealistic architectural visualization."""
            
            # Use direct HTTP request to FLUX API (direct URL approach)
            flux_url = flux_endpoint
            
            # Debug: Print all the values being used (remove these lines once everything works)
            # st.write(f"🔧 Debug - FLUX URL: {flux_url}")
            # st.write(f"🔧 Debug - FLUX API Key exists: {bool(flux_api_key)}")
            # st.write(f"🔧 Debug - Type of flux_url: {type(flux_url)}")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {flux_api_key}"
            }
            data = {
                "prompt": enhanced_prompt,
                "size": "1024x1024",
                "n": 1,
                "model": "flux.1-kontext-pro"
            }
            
            # More detailed debugging (remove these lines once everything works)
            # st.write(f"🔧 Debug - About to call requests.post with URL: {repr(flux_url)}")
            # st.write(f"🔧 Debug - Headers: {headers}")
            # st.write(f"🔧 Debug - Data keys: {list(data.keys())}")
            
            try:
                response = requests.post(
                    flux_url,
                    headers=headers,
                    json=data
                )
                # st.write(f"🔧 Debug - Request successful, status: {response.status_code}")
            except Exception as e:
                st.error(f"Error calling FLUX API: {e}")
                raise e
        else:
            # Standard text-to-image generation
            enhanced_prompt = f"Professional architectural visualization: {prompt}. High-quality, detailed, realistic architectural rendering style."
            
            # Use direct HTTP request to FLUX API (direct URL approach)
            flux_url = flux_endpoint
            
            # Debug: Print all the values being used (remove these lines once everything works)
            # st.write(f"🔧 Debug - FLUX URL: {flux_url}")
            # st.write(f"🔧 Debug - FLUX API Key exists: {bool(flux_api_key)}")
            # st.write(f"🔧 Debug - Type of flux_url: {type(flux_url)}")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {flux_api_key}"
            }
            data = {
                "prompt": enhanced_prompt,
                "size": "1024x1024",
                "n": 1,
                "model": "flux.1-kontext-pro"
            }
            
            # More detailed debugging (remove these lines once everything works)
            # st.write(f"🔧 Debug - About to call requests.post with URL: {repr(flux_url)}")
            # st.write(f"🔧 Debug - Headers: {headers}")
            # st.write(f"🔧 Debug - Data keys: {list(data.keys())}")
            
            try:
                response = requests.post(
                    flux_url,
                    headers=headers,
                    json=data
                )
                # st.write(f"🔧 Debug - Request successful, status: {response.status_code}")
            except Exception as e:
                st.error(f"Error calling FLUX API: {e}")
                raise e
        
        if response.status_code == 200:
            result = response.json()
            
            # Debug: Show the actual response structure (remove these lines once everything works)
            # st.write(f"🔧 Debug - Full API Response: {result}")
            # st.write(f"🔧 Debug - Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Handle both URL and base64 response formats
            if "data" in result and len(result["data"]) > 0:
                data_item = result["data"][0]
                # st.write(f"🔧 Debug - Data item keys: {list(data_item.keys()) if isinstance(data_item, dict) else 'Not a dict'}")
                # st.write(f"🔧 Debug - Data item content: {data_item}")
                
                if "url" in data_item:
                    # URL format - download the image
                    image_url = data_item["url"]
                    # st.write(f"🔧 Debug - Image URL from response: {repr(image_url)}")
                    
                    if image_url:
                        img_response = requests.get(image_url)
                        if img_response.status_code == 200:
                            return img_response.content
                        else:
                            st.error(f"Failed to download generated image: {img_response.status_code}")
                            return None
                    # else:
                        # st.warning("URL field is None, checking for base64 data...")
                
                # Check for base64 format (which FLUX is actually using)
                if "b64_json" in data_item:
                    b64_data = data_item["b64_json"]
                    # st.write(f"🔧 Debug - Found base64 data, length: {len(b64_data) if b64_data else 0}")
                    
                    if b64_data:
                        try:
                            # Decode base64 to get image bytes
                            image_bytes = base64.b64decode(b64_data)
                            # st.success("✅ Successfully decoded base64 image data!")
                            return image_bytes
                        except Exception as e:
                            st.error(f"Failed to decode base64 image: {e}")
                            return None
                    else:
                        st.error("Base64 data is None or empty")
                        return None
                else:
                    st.error("No 'url' or 'b64_json' field found in response")
                    return None
            else:
                st.error("No image data in FLUX API response")
                st.error(f"Response: {result}")
                return None
        else:
            st.error(f"FLUX API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            st.error("🔑 **FLUX Authentication Error:**")
            st.error("Your Azure OpenAI resource may not have FLUX.1-Kontext-pro deployed, or the API key is incorrect.")
            st.info("""
            **To fix this:**
            1. Go to Azure Portal → Your Azure OpenAI Resource
            2. Go to 'Model deployments' section
            3. Deploy FLUX.1-Kontext-pro model if not already deployed
            4. Verify the API key and endpoint are correct
            """)
        elif "404" in error_msg:
            st.error("🚫 **FLUX Model Not Found:**")
            st.error("FLUX.1-Kontext-pro model is not deployed in your Azure OpenAI resource.")
        elif "content_policy_violation" in error_msg or "safety system" in error_msg:
            st.error("🛡️ **Content Safety Filter Triggered:**")
            st.error("Your request was filtered by Azure's safety system.")
            st.info("""
            **Try these suggestions:**
            - Use more general, descriptive language
            - Focus on architectural terms like "modern building", "residential design", "commercial space"
            - Avoid detailed descriptions that might trigger safety filters
            - Try shorter, simpler prompts
            """)
            st.warning("💡 **Tip:** In image-to-image mode, try describing what you want to create rather than referencing the uploaded image directly.")
        else:
            st.error(f"❌ **Error generating image:** {error_msg}")
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
                    st.image(img, caption="Generated Architectural Visualization", use_container_width=True)

# Input section based on mode
st.markdown("---")

if mode == "🎨 Image Generation":
    st.markdown("### 🎨 Architectural Visualization Generator")
    
    # Multi-Agent selection if available
    agent_systems_available = []
    if AZURE_FOUNDRY_AVAILABLE:
        agent_systems_available.append("Azure AI Foundry Agents")
    
    use_multi_agent = False
    agent_type = "azure"  # Default to Azure AI Foundry
    
    if agent_systems_available:
        use_multi_agent = st.toggle(
            "🤖 Use Multi-Agent Intelligence", 
            value=True,
            help="Enable sophisticated multi-agent processing for superior results"
        )
        
        if use_multi_agent:
            if len(agent_systems_available) > 1:
                agent_system = st.radio(
                    "🤖 Agent System:",
                    agent_systems_available,
                    horizontal=True,
                    help="Choose between local Python agents or deployed Azure AI Foundry agents"
                )
                agent_type = "azure" if agent_system == "Azure AI Foundry Agents" else "local"
            elif "Azure AI Foundry Agents" in agent_systems_available:
                agent_type = "azure"
                st.info("🤖 **Azure AI Foundry Mode**: Using deployed Azure AI Foundry agents")
            else:
                agent_type = "local"
                st.info("🤖 **Local Multi-Agent Mode**: Using local Python agents")
            
            if agent_type == "azure":
                st.info("☁️ **Azure AI Foundry Agents**: Your request will be processed by deployed Azure AI Foundry agents with native Azure tracing, monitoring, and intelligent prompt caching for improved performance.")
            else:
                st.info("🏠 **Local Multi-Agent Mode**: Your request will be processed by local specialized AI agents for vision analysis, architectural expertise, prompt optimization, and quality assurance.")
    else:
        use_multi_agent = False
        st.info("💡 **Standard Mode**: Multi-agent systems not available. Using traditional processing.")
    
    # Generation mode selection
    generation_mode = st.radio(
        "🎨 Generation Mode:",
        ["📝 Text to Image", "🖼️ Image to Image"],
        horizontal=True
    )
    
    if generation_mode == "🖼️ Image to Image":
        st.markdown("#### 📤 Upload Reference Images")
        uploaded_files = st.file_uploader(
            "Upload architectural images to modify or get inspired by:",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload photos, sketches, or existing architectural images that you want to modify or use as inspiration. You can upload multiple images for comprehensive analysis."
        )
        
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} image(s) uploaded:**")
            # Display images in a grid layout
            cols = st.columns(min(3, len(uploaded_files)))  # Max 3 columns
            for idx, uploaded_file in enumerate(uploaded_files):
                with cols[idx % 3]:
                    st.image(uploaded_file, caption=f"Reference Image {idx + 1}", use_container_width=True)
            
        st.info("💡 **Image-to-Image Generation:** Upload architectural images (interior, exterior, detail). GPT-4 Vision will analyze each image and understand the spaces, styles, and features. When multiple images are provided, the analysis will combine insights from all images. FLUX will then generate a new image based on this comprehensive analysis combined with your modifications, creating architecturally consistent results.")
    
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
    
    if generation_mode == "🖼️ Image to Image":
        user_input = st.text_area(
            "🔄 Describe modifications to apply to this space:",
            placeholder="Example: 'Make this bathroom more modern with marble finishes' or 'Add more natural lighting' or 'Change to a minimalist style'...",
            height=100
        )
    else:
        user_input = st.text_area(
            "🏗️ Describe your architectural vision:",
            placeholder="Describe the building, space, or architectural element you want to visualize...",
            height=100
        )
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        if generation_mode == "🖼️ Image to Image":
            generate_button = st.button("🔄 Transform Image", type="primary", use_container_width=True)
        else:
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
    # Check if we need a reference image for image-to-image generation
    if generation_mode == "🖼️ Image to Image" and 'uploaded_file' not in locals():
        st.error("📤 Please upload a reference image for image-to-image generation.")
    elif generation_mode == "🖼️ Image to Image" and uploaded_file is None:
        st.error("📤 Please upload a reference image for image-to-image generation.")
    else:
        enhanced_prompt = user_input
        
        if style_preset != "Custom (use description)":
            enhanced_prompt += f" Architectural style: {style_preset}."
        
        enhanced_prompt += f" View type: {view_type}."
        
        # Prepare the reference image if in image-to-image mode
        reference_imgs = uploaded_files if generation_mode == "🖼️ Image to Image" else None
        
        user_message = {
            "role": "user", 
            "content": f"{'Transform' if generation_mode == '🖼️ Image to Image' else 'Generate'} architectural image: {user_input}",
            "image_request": enhanced_prompt,
            "generation_mode": generation_mode
        }
        st.session_state.messages.append(user_message)
        
        # Use multi-agent processing if enabled
        if 'use_multi_agent' in locals() and use_multi_agent:
            try:
                agent_type_to_use = agent_type if 'agent_type' in locals() else "local"
                
                with st.spinner(f"🤖 {'Azure AI Foundry' if agent_type_to_use == 'azure' else 'Local Multi-Agent'} System Processing..."):
                    # Process with multi-agent system
                    workflow_result = asyncio.run(process_with_multi_agents(
                        user_text=user_input,
                        uploaded_files=reference_imgs,
                        architectural_style=style_preset if style_preset != "Custom (use description)" else None,
                        view_type=view_type,
                        agent_type=agent_type_to_use
                    ))
                    
                    if workflow_result:
                        # Display workflow results
                        display_workflow_results(workflow_result, agent_type_to_use)
                        
                        # Extract optimized prompt based on agent type
                        optimized_prompt = None
                        if agent_type_to_use == "azure":
                            optimized_prompt = workflow_result.get('final_result', {}).get('optimized_prompt')
                        else:
                            optimized_prompt = workflow_result.get('final_output', {}).get('optimized_prompt')
                        
                        if optimized_prompt:
                            st.markdown("### 🎯 Optimized Prompt")
                            st.text_area("Generated by Multi-Agent System:", optimized_prompt, height=100, disabled=True)
                            
                            # Use optimized prompt for generation
                            enhanced_prompt = optimized_prompt
                        
                        # Store workflow result in session state
                        st.session_state.last_workflow = workflow_result
                    else:
                        st.warning("⚠️ Multi-agent processing failed, falling back to standard mode")
                        
            except Exception as e:
                st.error(f"🤖 Multi-agent processing error: {e}")
                st.info("Falling back to standard processing...")
        
        try:
            spinner_text = "🔄 Transforming architectural image..." if generation_mode == "🖼️ Image to Image" else "🎨 Generating architectural visualization..."
            with st.spinner(spinner_text):
                # Use first image for image generation (FLUX currently supports single image input)
                first_reference_img = reference_imgs[0] if reference_imgs and len(reference_imgs) > 0 else None
                generated_image_data = generate_architectural_image(enhanced_prompt, first_reference_img)
                
            if generated_image_data:
                generated_image = Image.open(io.BytesIO(generated_image_data))
                
                if generation_mode == "🖼️ Image to Image":
                    ai_response = f"I've transformed your reference image based on your description: '{user_input}'\n\nStyle: {style_preset}\nView: {view_type}\n\nThe new image shows an architectural interpretation that incorporates your requested modifications while maintaining professional rendering quality. 🔄✨"
                else:
                    ai_response = f"I've generated an architectural visualization based on your description: '{user_input}'\n\nStyle: {style_preset}\nView: {view_type}\n\nThe image shows a professional architectural rendering that matches your specifications. 🏗️✨"
                
                # Add multi-agent enhancement note if used
                if 'use_multi_agent' in locals() and use_multi_agent and 'optimized_prompt' in locals() and optimized_prompt:
                    ai_response += "\n\n🤖 **Enhanced with Multi-Agent Intelligence**: This image was generated using an optimized prompt created by our specialized AI agents for superior architectural accuracy and quality."
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": ai_response,
                    "generated_image": generated_image_data
                })
                
                st.image(generated_image, caption="Generated Architectural Visualization", use_container_width=True)
                st.rerun()
            else:
                st.error("Failed to generate image. Please try again.")
                
        except Exception as e:
            st.error(f"🔧 Sorry, I encountered an issue generating the image: {e}")
            st.error("Please check your FLUX deployment and API configuration.")

# Sidebar
with st.sidebar:
    st.markdown("## 🏗️ Architectural Tools")
    st.markdown("*Your design companion* 📐")
    
    # Multi-Agent Status
    if AZURE_FOUNDRY_AVAILABLE and orchestrator:
        st.success("🤖 Multi-Agent System: Active")
        if st.button("🔍 Open Tracing Dashboard", use_container_width=True):
            st.success("🔍 Tracing dashboard opened!")
            st.info("View workflow traces in Azure AI Foundry dashboard")
        
        # Intelligent Orchestrator Information
        try:
            st.markdown("### � Intelligent Agent System")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Agent Types", "6 Specialists")
                st.metric("Routing", "Dynamic & Intelligent")
            with col2:
                st.metric("Model Strategy", "GPT-4o + GPT-5")
                if hasattr(orchestrator, 'conversation_memory'):
                    memory_sessions = len(orchestrator.conversation_memory)
                    st.metric("Active Sessions", memory_sessions)
                else:
                    st.metric("Collaboration", "✅ Active")
        except Exception as e:
            st.warning(f"Orchestrator info unavailable: {str(e)}")
        
        # Display last workflow metrics if available
        if 'last_workflow' in st.session_state:
            workflow = st.session_state.last_workflow
            summary = workflow.get('processing_summary', {})
            st.markdown("### 📊 Last Workflow")
            st.metric("Confidence", f"{summary.get('average_confidence', 0):.2f}")
            st.metric("Processing Time", f"{summary.get('execution_time', 0):.1f}s")
    else:
        st.info("🤖 Multi-Agent System: Unavailable")
    
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
if AZURE_FOUNDRY_AVAILABLE and orchestrator:
    st.markdown("*🤖 Enhanced with Azure AI Foundry Agents | 🔍 Monitored with Azure Tracing | 🎨 Generated with FLUX.1-Kontext-pro* 📐")
else:
    st.markdown("*Built with 🏗️ for architectural excellence* 📐")
