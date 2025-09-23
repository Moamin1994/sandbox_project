# Azure AI Foundry Multi-Agent Orchestrator

A cloud-native intelligent architectural design assistant powered by Azure AI Foundry, featuring **GPT-4o agents**, **GPT-5 premium output**, **FLUX image generation**, and **Azure Computer Vision analysis**.

## 🏗️ Architecture Overview

This system implements an intelligent multi-agent orchestration pattern on Azure AI Foundry with:

- **6 Specialized AI Agents** (GPT-4o): Architect, Designer, Structural Engineer, Material Expert, Code Generator, Project Manager
- **Premium Output Generation** (GPT-5): High-quality synthesis and user-facing content
- **Advanced Image Generation** (FLUX.1-Kontext-pro): Architectural visualization and design concepts
- **Computer Vision Analysis** (Azure CV): Image understanding and analysis
- **Comprehensive Observability**: OpenTelemetry tracing to Azure Application Insights

## 🚀 Quick Deployment

### Option 1: Streamlit Cloud (Recommended for Testing)

Deploy instantly to Streamlit Cloud for free:

1. **Fork this repository** to your GitHub account
2. **Sign up** at [Streamlit Cloud](https://share.streamlit.io/)
3. **Create new app** pointing to `streamlit_app.py`
4. **Configure secrets** with your Azure credentials
5. **Deploy!** - Your app will be live in minutes

📋 **Detailed Guide**: See [STREAMLIT_DEPLOYMENT.md](./STREAMLIT_DEPLOYMENT.md) for complete instructions.

### Option 2: Azure Cloud Native Deployment

For production workloads with full Azure integration:

#### Prerequisites

1. **Azure CLI** - [Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Azure Developer CLI** - [Install](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
3. **PowerShell 7+** (Windows) or **Bash** (Linux/macOS)
4. **Python 3.11+** for local development
5. **Azure Subscription** with appropriate permissions

#### One-Command Deployment

```powershell
# Clone and deploy
git clone <repository-url>
cd sandbox_project

# Set required environment variables
$env:FLUX_API_KEY = "your-flux-api-key"

# Deploy everything to Azure
.\deploy_complete.ps1 -Environment "prod" -Location "eastus2"
```

#### Step-by-Step Deployment

1. **Login to Azure**
   ```powershell
   az login
   ```

2. **Deploy Infrastructure**
   ```powershell
   .\deploy.ps1 -Preview  # Review changes first
   .\deploy.ps1           # Deploy infrastructure
   ```

3. **Deploy Models**
   ```powershell
   .\models\deploy_models.ps1
   ```

4. **Deploy Function App**
   ```powershell
   azd deploy
   ```

5. **Test Deployment**
   ```powershell
   .\deploy_complete.ps1 -TestOnly
   ```

## 🤖 Model Strategy

| Component | Model | Purpose | Configuration |
|-----------|-------|---------|---------------|
| **Agents** | GPT-4o (2024-11-20) | Intelligent agent workflows | High capacity (100 TPU), 4K tokens |
| **Output** | GPT-5 (preview) | Premium quality synthesis | Premium tier, 8K tokens, low temperature |
| **Images** | FLUX.1-Kontext-pro | Architectural visualization | GitHub Models endpoint |
| **Vision** | Azure Computer Vision | Image analysis | S1 tier, latest API version |

## 📁 Project Structure

```
sandbox_project/
├── infra/                      # Infrastructure as Code (Bicep)
│   ├── main.bicep             # Main deployment template
│   └── modules/               # Bicep modules
├── function_app/              # Azure Function App
│   ├── function_app.py        # Main orchestration function
│   ├── requirements.txt       # Python dependencies
│   └── host.json             # Function configuration
├── agents/                    # AI Agent Definitions
│   ├── agent_definitions.py   # 6 specialized agents
│   └── deploy_agents.py      # Agent deployment script
├── models/                    # Model Configurations
│   ├── model_configs.py      # Model deployment configs
│   └── deploy_models.ps1     # Model deployment script
├── tracing/                   # Observability
│   └── azure_foundry_tracing.py # OpenTelemetry setup
├── streamlit_cloud_app.py     # Cloud-native Streamlit app
├── deploy_complete.ps1        # Complete deployment script
└── azure.yaml                # Azure Developer CLI config
```

## 🔧 Configuration

### Environment Variables

Set these in your Function App configuration:

```json
{
  "GPT4O_ENDPOINT": "https://your-aoai.openai.azure.com/",
  "GPT4O_DEPLOYMENT": "gpt-4o-agents",
  "GPT5_ENDPOINT": "https://your-gpt5.openai.azure.com/",
  "GPT5_DEPLOYMENT": "gpt-5-premium",
  "FLUX_ENDPOINT": "https://models.inference.ai.azure.com",
  "VISION_ENDPOINT": "https://your-cv.cognitiveservices.azure.com/",
  "APPLICATIONINSIGHTS_CONNECTION_STRING": "InstrumentationKey=...",
  "KEY_VAULT_URL": "https://your-kv.vault.azure.net/"
}
```

### Agent Configuration

The system includes 6 specialized agents:

1. **Senior Architect** - Architectural design and planning
2. **Creative Designer** - Aesthetics and user experience
3. **Structural Engineer** - Safety and structural integrity
4. **Material Expert** - Material selection and sustainability
5. **Code Generator** - Building automation and smart systems
6. **Project Manager** - Coordination and integration

## 🎯 Usage Examples

### REST API (Function App)

```bash
# Test health endpoint
curl https://your-function-app.azurewebsites.net/api/health

# Orchestrate architectural design
curl -X POST https://your-function-app.azurewebsites.net/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "type": "architectural_design",
    "complexity": "medium",
    "project_description": "Modern sustainable office building",
    "generate_images": true,
    "context": {
      "location": "Seattle, WA",
      "building_type": "Commercial",
      "sustainability_focus": true
    }
  }'
```

### Streamlit App

1. Update configuration in `streamlit_cloud_app.py`
2. Set `AZURE_FUNCTION_APP_URL` environment variable
3. Run: `streamlit run streamlit_cloud_app.py`

### Python SDK

```python
import requests

# Initialize client
class AzureAIFoundryClient:
    def __init__(self, function_app_url):
        self.base_url = function_app_url
    
    def orchestrate(self, request_data):
        response = requests.post(
            f"{self.base_url}/api/orchestrate",
            json=request_data
        )
        return response.json()

# Use client
client = AzureAIFoundryClient("https://your-app.azurewebsites.net")
result = client.orchestrate({
    "type": "architectural_design",
    "project_description": "Smart residential complex"
})
```

## � Monitoring and Observability

### Azure Application Insights

- **Traces**: Full orchestration workflows and agent interactions
- **Metrics**: Agent execution counts, model usage, performance
- **Logs**: Structured logging with correlation IDs
- **Dependencies**: Model API calls and response times

### Custom Metrics

- `ai_agent_executions_total` - Agent execution counter
- `ai_model_requests_total` - Model API request counter  
- `ai_orchestration_duration_seconds` - Workflow duration
- `ai_agent_confidence_score` - Agent confidence levels

### Viewing Traces

1. Open [Azure Portal](https://portal.azure.com)
2. Navigate to your Application Insights resource
3. Go to **Transaction search** or **Application map**
4. Filter by `ai_orchestration_workflow` operation

## 🔐 Security and Authentication

### Azure AD Integration

- **Function App**: Uses system-assigned managed identity
- **Model Access**: Azure AD authentication for OpenAI and Cognitive Services
- **Key Vault**: Secure storage for API keys (FLUX)
- **RBAC**: Least-privilege access controls

### API Security

- Function-level authentication with API keys
- HTTPS-only communication
- CORS configured for specific origins
- Request validation and sanitization

## 🚀 Performance and Scaling

### Azure Function App (Flex Consumption)

- **Auto-scaling**: 0-100 instances based on demand
- **Cold start**: Optimized with Python 3.11
- **Timeout**: 10 minutes for complex orchestrations
- **Memory**: Optimized for AI workloads

### Model Scaling

- **GPT-4o**: 100 TPU capacity for concurrent agent work
- **GPT-5**: 50 TPU capacity for premium output
- **Computer Vision**: S1 tier for high throughput
- **FLUX**: Rate-limited by GitHub Models

## 🛠️ Development and Testing

### Local Development

1. Install dependencies:
   ```bash
   pip install -r function_app/requirements.txt
   ```

2. Copy settings:
   ```bash
   cp function_app/local.settings.template.json function_app/local.settings.json
   # Update with your values
   ```

3. Run locally:
   ```bash
   cd function_app
   func start
   ```

### Testing

```bash
# Unit tests
python -m pytest tests/

# Integration tests
python test_orchestration.py

# Load testing
python test_performance.py
```

## 📈 Cost Optimization

### Model Costs

- **GPT-4o**: $2.50-$10.00/1M tokens (input-output)
- **GPT-5**: Premium pricing (preview)
- **FLUX**: $0.003 per image
- **Computer Vision**: $1.50/1K transactions

### Azure Resources

- **Function App**: Pay-per-execution (Flex Consumption)
- **AI Foundry**: Included workspace costs
- **Application Insights**: $2.30/GB ingestion
- **Key Vault**: $0.03/10K operations

## � Troubleshooting

### Common Issues

1. **Function App not responding**
   ```bash
   # Check deployment status
   az functionapp show --name your-function-app --resource-group your-rg
   
   # View logs
   az functionapp logs tail --name your-function-app --resource-group your-rg
   ```

2. **Model deployment failures**
   ```bash
   # Check OpenAI deployment
   az cognitiveservices account deployment list --name your-aoai --resource-group your-rg
   
   # Check quota
   az cognitiveservices account deployment show --name your-aoai --resource-group your-rg --deployment-name gpt-4o-agents
   ```

3. **Tracing not appearing**
   - Verify Application Insights connection string
   - Check if OpenTelemetry is properly configured
   - Review Function App environment variables

### Support Resources

- [Azure AI Foundry Documentation](https://docs.microsoft.com/azure/ai-studio/)
- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)

## 🚀 Next Steps

1. **Production Readiness**
   - Configure private endpoints
   - Set up Azure Front Door
   - Implement rate limiting
   - Configure backup and disaster recovery

2. **Advanced Features**
   - Add voice interface with Azure Speech Services
   - Implement document processing with Azure Document Intelligence
   - Add integration with CAD software APIs
   - Create mobile app with Azure App Service

3. **AI Enhancements**
   - Fine-tune models for architectural domain
   - Add RAG with Azure AI Search
   - Implement agentic workflows with planning
   - Add multi-modal capabilities

## 📞 Support

For support and questions:
- Review the troubleshooting guide above
- Check Azure service health and quotas
- Review Application Insights for error details
- Test with reduced complexity requests first

---

**🏗️ Built with Azure AI Foundry | ☁️ Cloud-Native Architecture | 🤖 Intelligent Multi-Agent Orchestration**