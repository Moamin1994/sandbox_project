"""
Model Deployment Configuration for Azure AI Foundry
GPT-5 for premium output, FLUX.1-Kontext-pro for images, Azure Computer Vision for analysis
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class ModelType(str, Enum):
    """Types of models in the AI orchestrator"""
    AGENT_MODEL = "agent"        # GPT-4o for agents
    OUTPUT_MODEL = "output"      # GPT-5 for final output
    IMAGE_GEN_MODEL = "image_gen"    # FLUX for generation
    VISION_MODEL = "vision"      # Azure Computer Vision for analysis

@dataclass
class ModelDeploymentConfig:
    """Configuration for model deployment"""
    name: str
    model_type: ModelType
    model_id: str
    model_version: str
    endpoint_url: str
    api_version: str
    deployment_name: str
    sku: str
    capacity: int
    max_tokens: int
    temperature: float
    description: str
    capabilities: List[str]
    authentication: Dict[str, str]
    performance_tier: str
    
# GPT-4o Configuration for Agents
GPT4O_AGENT_CONFIG = ModelDeploymentConfig(
    name="GPT-4o Agents",
    model_type=ModelType.AGENT_MODEL,
    model_id="gpt-4o",
    model_version="2024-11-20",
    endpoint_url="https://your-aoai-resource.openai.azure.com/",
    api_version="2024-10-21",
    deployment_name="gpt-4o-agents",
    sku="Standard",
    capacity=100,  # High capacity for multiple agents
    max_tokens=4000,
    temperature=0.7,
    description="GPT-4o optimized for intelligent agent workflows and collaboration",
    capabilities=[
        "Advanced reasoning and analysis",
        "Multi-turn conversation",
        "Code generation and review",
        "Technical writing and documentation",
        "Cross-domain knowledge synthesis",
        "Collaborative problem solving"
    ],
    authentication={
        "type": "azure_ad",
        "managed_identity": "system_assigned"
    },
    performance_tier="high"
)

# GPT-5 Configuration for Premium Output
GPT5_OUTPUT_CONFIG = ModelDeploymentConfig(
    name="GPT-5 Premium Output",
    model_type=ModelType.OUTPUT_MODEL,
    model_id="gpt-5",
    model_version="preview",
    endpoint_url="https://your-gpt5-endpoint.openai.azure.com/",
    api_version="2024-12-01-preview",
    deployment_name="gpt-5-premium",
    sku="Premium",
    capacity=50,  # Lower capacity, higher quality
    max_tokens=8000,
    temperature=0.3,  # Lower for consistency in final output
    description="GPT-5 for premium quality final output synthesis and user presentation",
    capabilities=[
        "Superior text generation quality",
        "Advanced reasoning and synthesis",
        "Multi-modal understanding",
        "Complex document generation",
        "High-quality technical writing",
        "Creative and analytical content"
    ],
    authentication={
        "type": "azure_ad",
        "managed_identity": "system_assigned"
    },
    performance_tier="premium"
)

# FLUX.1-Kontext-pro Configuration for Image Generation
FLUX_IMAGE_CONFIG = ModelDeploymentConfig(
    name="FLUX.1-Kontext-pro",
    model_type=ModelType.IMAGE_GEN_MODEL,
    model_id="FLUX.1-Kontext-pro",
    model_version="latest",
    endpoint_url="https://models.inference.ai.azure.com",
    api_version="2024-04-01-preview",
    deployment_name="flux-architectural",
    sku="Standard",
    capacity=20,
    max_tokens=100,  # For prompt processing
    temperature=0.8,  # Higher for creative image generation
    description="State-of-the-art image generation for architectural visualization and design",
    capabilities=[
        "High-quality architectural visualization",
        "Photorealistic rendering",
        "Design concept illustration",
        "Technical diagram generation",
        "Material and texture visualization",
        "Environmental and contextual imagery"
    ],
    authentication={
        "type": "api_key",
        "key_vault_secret": "flux-api-key"
    },
    performance_tier="specialized"
)

# Azure Computer Vision Configuration for Image Analysis
AZURE_VISION_CONFIG = ModelDeploymentConfig(
    name="Azure Computer Vision",
    model_type=ModelType.VISION_MODEL,
    model_id="computer-vision",
    model_version="2024-02-01",
    endpoint_url="https://your-cv-resource.cognitiveservices.azure.com/",
    api_version="2024-02-01",
    deployment_name="cv-analysis",
    sku="S1",
    capacity=10,
    max_tokens=0,  # Not applicable for vision
    temperature=0.0,  # Not applicable for vision
    description="Advanced computer vision for architectural image analysis and understanding",
    capabilities=[
        "Image content analysis",
        "Object and structure detection",
        "Spatial relationship understanding",
        "Text extraction (OCR)",
        "Design element recognition",
        "Quality and compliance assessment"
    ],
    authentication={
        "type": "azure_ad",
        "managed_identity": "system_assigned"
    },
    performance_tier="high"
)

# Model Registry
MODEL_REGISTRY: Dict[ModelType, ModelDeploymentConfig] = {
    ModelType.AGENT_MODEL: GPT4O_AGENT_CONFIG,
    ModelType.OUTPUT_MODEL: GPT5_OUTPUT_CONFIG,
    ModelType.IMAGE_GEN_MODEL: FLUX_IMAGE_CONFIG,
    ModelType.VISION_MODEL: AZURE_VISION_CONFIG
}

class ModelManager:
    """Manages model deployments and configurations"""
    
    def __init__(self):
        self.models = MODEL_REGISTRY
    
    def get_model_config(self, model_type: ModelType) -> ModelDeploymentConfig:
        """Get model configuration by type"""
        return self.models[model_type]
    
    def get_all_models(self) -> List[ModelDeploymentConfig]:
        """Get all model configurations"""
        return list(self.models.values())
    
    def get_deployment_script(self) -> str:
        """Generate Azure CLI deployment script for all models"""
        script_lines = [
            "#!/bin/bash",
            "# Azure AI Model Deployment Script",
            "# Deploy GPT-4o, GPT-5, FLUX, and Computer Vision",
            "",
            "set -e",
            "",
            "echo '🤖 Starting Azure AI Model Deployments...'",
            ""
        ]
        
        for model in self.models.values():
            if model.model_type == ModelType.AGENT_MODEL:
                script_lines.extend(self._generate_openai_deployment(model))
            elif model.model_type == ModelType.OUTPUT_MODEL:
                script_lines.extend(self._generate_gpt5_deployment(model))
            elif model.model_type == ModelType.IMAGE_GEN_MODEL:
                script_lines.extend(self._generate_flux_deployment(model))
            elif model.model_type == ModelType.VISION_MODEL:
                script_lines.extend(self._generate_vision_deployment(model))
        
        script_lines.extend([
            "",
            "echo '✅ All model deployments completed!'",
            "echo '📋 Next: Configure Function App environment variables'"
        ])
        
        return "\n".join(script_lines)
    
    def _generate_openai_deployment(self, model: ModelDeploymentConfig) -> List[str]:
        """Generate Azure OpenAI deployment commands"""
        return [
            f"# Deploy {model.name}",
            f"echo '📦 Deploying {model.name}...'",
            f"az cognitiveservices account deployment create \\",
            f"  --resource-group $AZURE_RESOURCE_GROUP \\",
            f"  --account-name $AZURE_OPENAI_ACCOUNT \\",
            f"  --deployment-name {model.deployment_name} \\",
            f"  --model-name {model.model_id} \\",
            f"  --model-version {model.model_version} \\",
            f"  --model-format OpenAI \\",
            f"  --sku-capacity {model.capacity} \\",
            f"  --sku-name {model.sku}",
            ""
        ]
    
    def _generate_gpt5_deployment(self, model: ModelDeploymentConfig) -> List[str]:
        """Generate GPT-5 deployment commands"""
        return [
            f"# Deploy {model.name} (Preview)",
            f"echo '🚀 Deploying {model.name}...'",
            f"# Note: GPT-5 deployment requires preview access",
            f"az cognitiveservices account deployment create \\",
            f"  --resource-group $AZURE_RESOURCE_GROUP \\",
            f"  --account-name $AZURE_OPENAI_ACCOUNT \\",
            f"  --deployment-name {model.deployment_name} \\",
            f"  --model-name {model.model_id} \\",
            f"  --model-version {model.model_version} \\",
            f"  --model-format OpenAI \\",
            f"  --sku-capacity {model.capacity} \\",
            f"  --sku-name {model.sku}",
            ""
        ]
    
    def _generate_flux_deployment(self, model: ModelDeploymentConfig) -> List[str]:
        """Generate FLUX deployment configuration"""
        return [
            f"# Configure {model.name}",
            f"echo '🎨 Configuring {model.name}...'",
            f"# FLUX uses GitHub Models endpoint - no deployment needed",
            f"# Store API key in Key Vault",
            f"az keyvault secret set \\",
            f"  --vault-name $KEY_VAULT_NAME \\",
            f"  --name flux-api-key \\",
            f"  --value $FLUX_API_KEY",
            ""
        ]
    
    def _generate_vision_deployment(self, model: ModelDeploymentConfig) -> List[str]:
        """Generate Computer Vision deployment"""
        return [
            f"# {model.name} already deployed via Bicep",
            f"echo '👁️ Computer Vision service ready'",
            ""
        ]
    
    def save_deployment_configs(self, output_dir: str = "deployment_configs"):
        """Save all deployment configurations to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save individual model configs
        for model in self.models.values():
            config_file = f"{output_dir}/{model.deployment_name}.json"
            with open(config_file, 'w') as f:
                json.dump(asdict(model), f, indent=2)
        
        # Save combined config
        combined_config = {
            "deployment_strategy": {
                "agents": "gpt-4o",
                "output": "gpt-5",
                "images": "FLUX.1-Kontext-pro",
                "vision": "Azure Computer Vision"
            },
            "models": {model_type.value: asdict(config) 
                      for model_type, config in self.models.items()},
            "integration_notes": {
                "authentication": "All models use Azure AD Managed Identity except FLUX (API key)",
                "scaling": "GPT-4o has highest capacity for agent workloads",
                "quality": "GPT-5 optimized for premium user-facing output",
                "specialization": "FLUX for architectural visualization, CV for analysis"
            }
        }
        
        with open(f"{output_dir}/complete_model_config.json", 'w') as f:
            json.dump(combined_config, f, indent=2)
        
        # Save deployment script
        with open(f"{output_dir}/deploy_models.sh", 'w') as f:
            f.write(self.get_deployment_script())
        
        # Make script executable
        os.chmod(f"{output_dir}/deploy_models.sh", 0o755)

def create_environment_variables() -> Dict[str, str]:
    """Create environment variables for Function App"""
    return {
        # GPT-4o Agent Configuration
        "GPT4O_ENDPOINT": GPT4O_AGENT_CONFIG.endpoint_url,
        "GPT4O_DEPLOYMENT": GPT4O_AGENT_CONFIG.deployment_name,
        "GPT4O_API_VERSION": GPT4O_AGENT_CONFIG.api_version,
        
        # GPT-5 Output Configuration
        "GPT5_ENDPOINT": GPT5_OUTPUT_CONFIG.endpoint_url,
        "GPT5_DEPLOYMENT": GPT5_OUTPUT_CONFIG.deployment_name,
        "GPT5_API_VERSION": GPT5_OUTPUT_CONFIG.api_version,
        
        # FLUX Image Generation Configuration
        "FLUX_ENDPOINT": FLUX_IMAGE_CONFIG.endpoint_url,
        "FLUX_MODEL": FLUX_IMAGE_CONFIG.model_id,
        "FLUX_API_VERSION": FLUX_IMAGE_CONFIG.api_version,
        
        # Azure Computer Vision Configuration
        "VISION_ENDPOINT": AZURE_VISION_CONFIG.endpoint_url,
        "VISION_API_VERSION": AZURE_VISION_CONFIG.api_version,
        
        # Model Strategy Configuration
        "MODEL_STRATEGY": "gpt4o-agents_gpt5-output_flux-images_cv-analysis",
        "ENABLE_PREMIUM_OUTPUT": "true",
        "ENABLE_IMAGE_GENERATION": "true",
        "ENABLE_VISION_ANALYSIS": "true"
    }

if __name__ == "__main__":
    # Initialize model manager and save configurations
    manager = ModelManager()
    manager.save_deployment_configs()
    
    # Create environment variables file
    env_vars = create_environment_variables()
    with open("deployment_configs/function_app_env_vars.json", 'w') as f:
        json.dump(env_vars, f, indent=2)
    
    print("🎉 Model deployment configurations created!")
    print("📂 Files saved to deployment_configs/")
    print("📋 Next steps:")
    print("1. Update environment variables with your actual endpoints")
    print("2. Run deploy_models.sh to deploy models")
    print("3. Configure Function App environment variables")
    print("4. Test model integrations")