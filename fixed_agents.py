"""
Fixed Azure Agents using direct Azure OpenAI client
"""
import os
import base64
import io
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class SimpleAzureAgent:
    """Simple Azure OpenAI agent that works with your endpoint"""
    
    def __init__(self, 
                 name: str, 
                 instructions: str,
                 model_deployment: str = "gpt-4o"):
        self.name = name
        self.instructions = instructions
        self.model_deployment = model_deployment
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        )
    
    def process_request(self, 
                       user_message: str, 
                       images: Optional[List[bytes]] = None,
                       context: Optional[str] = None) -> str:
        """Process a request with optional images"""
        try:
            # Prepare the messages
            messages = [
                {"role": "system", "content": self.instructions}
            ]
            
            if context:
                messages.append({"role": "system", "content": f"Context: {context}"})
            
            # Prepare user message with images if provided
            user_content = []
            user_content.append({"type": "text", "text": user_message})
            
            if images:
                for image_bytes in images[:3]:  # Limit to 3 images
                    # Convert bytes to base64
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    })
            
            messages.append({"role": "user", "content": user_content})
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=self.model_deployment,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error in {self.name}: {str(e)}"


class FixedAzureOrchestrator:
    """Fixed orchestrator using direct Azure OpenAI calls"""
    
    def __init__(self):
        # Initialize agents with GPT-4o for cost-effective agent work
        self.vision_analyst = SimpleAzureAgent(
            name="Vision Analyst",
            instructions="""You are an expert architectural vision analyst. Analyze uploaded images and provide detailed insights about:
            - Architectural style and design elements
            - Spatial composition and layout
            - Materials, colors, and textures
            - Lighting and environmental context
            - Design principles and aesthetic qualities
            
            Provide clear, professional analysis that will help generate architectural visualizations.""",
            model_deployment="gpt-4o"
        )
        
        self.architectural_expert = SimpleAzureAgent(
            name="Architectural Expert",
            instructions="""You are a senior architectural consultant. Based on image analysis and user requirements, provide:
            - Professional architectural recommendations
            - Design strategy and conceptual direction  
            - Technical considerations and best practices
            - Space planning and functional analysis
            - Style guidance and design principles
            
            Deliver expert architectural consultation to guide design decisions.""",
            model_deployment="gpt-4o"
        )
        
        self.prompt_engineer = SimpleAzureAgent(
            name="Prompt Engineer",
            instructions="""You are a FLUX image generation prompt specialist. Create optimized prompts for architectural visualization:
            - Translate architectural concepts into detailed FLUX prompts
            - Include specific architectural terminology and styles
            - Optimize for photorealistic architectural rendering
            - Incorporate lighting, materials, and composition details
            - Ensure prompts generate professional architectural imagery
            
            Return only the optimized FLUX prompt, nothing else.""",
            model_deployment="gpt-4o"
        )
        
        # Quality assurance uses GPT-5 for premium final output
        self.quality_assurance = SimpleAzureAgent(
            name="Quality Assurance",
            instructions="""You are a quality assurance specialist for architectural AI systems. Review and enhance all outputs:
            - Ensure architectural accuracy and professionalism
            - Verify completeness and clarity of recommendations
            - Enhance language for professional presentation
            - Identify any gaps or improvements needed
            - Provide final polished architectural consultation
            
            Deliver the highest quality final output for professional use.""",
            model_deployment="gpt-5-model"  # Use GPT-5 for final quality output
        )
    
    async def process_request(self, 
                            user_message: str, 
                            user_images: Optional[List[bytes]] = None) -> Dict[str, Any]:
        """Process multi-agent workflow"""
        
        results = {}
        context = ""
        
        try:
            # Step 1: Vision Analysis (if images provided)
            if user_images:
                print("🔍 Running Vision Analysis...")
                vision_result = self.vision_analyst.process_request(
                    f"Analyze these architectural images and provide detailed insights: {user_message}",
                    images=user_images
                )
                results['vision_analysis'] = vision_result
                context += f"Vision Analysis: {vision_result}\n\n"
            
            # Step 2: Architectural Consultation
            print("🏗️ Running Architectural Consultation...")
            arch_result = self.architectural_expert.process_request(
                user_message,
                context=context
            )
            results['architectural_consultation'] = arch_result
            context += f"Architectural Expert: {arch_result}\n\n"
            
            # Step 3: Prompt Engineering for FLUX
            print("🎨 Generating FLUX Prompt...")
            prompt_result = self.prompt_engineer.process_request(
                f"Create an optimized FLUX prompt for: {user_message}",
                context=context
            )
            results['flux_prompt'] = prompt_result
            context += f"FLUX Prompt: {prompt_result}\n\n"
            
            # Step 4: Quality Assurance (using GPT-5 for premium final output)
            print("✅ Quality Assurance Review...")
            qa_result = self.quality_assurance.process_request(
                f"Review and enhance this architectural consultation: {user_message}",
                context=context
            )
            results['final_output'] = {
                'architectural_analysis': results.get('vision_analysis', ''),
                'expert_consultation': arch_result,
                'optimized_prompt': prompt_result,
                'quality_review': qa_result,
                'confidence_score': 0.9
            }
            
            return results
            
        except Exception as e:
            print(f"❌ Error in orchestrator: {e}")
            return {
                'error': str(e),
                'final_output': {
                    'architectural_analysis': 'Error occurred during processing',
                    'expert_consultation': 'Error occurred during processing', 
                    'optimized_prompt': user_message,
                    'quality_review': 'Error occurred during processing',
                    'confidence_score': 0.0
                }
            }