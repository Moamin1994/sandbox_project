# 🚀 Streamlit Cloud Deployment Guide

## Overview
This guide will help you deploy your ArchitectAI Studio to Streamlit Cloud with full Azure AI Foundry integration.

## Prerequisites
- GitHub account with this repository
- Streamlit Cloud account (sign up at https://share.streamlit.io/)
- Azure AI Foundry project with API keys

## Step 1: Prepare Your Repository
Your repository is already configured for Streamlit Cloud deployment with:
- ✅ Optimized `requirements.txt`
- ✅ `.streamlit/config.toml` configuration
- ✅ Cloud-compatible environment variable handling

## Step 2: Deploy to Streamlit Cloud

### 2.1 Connect to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click "New app"
4. Select this repository: `Moamin1994/sandbox_project`
5. Set main file path: `streamlit_app.py`
6. Click "Deploy!"

### 2.2 Configure Secrets
After deployment, you need to add your Azure secrets:

1. In your Streamlit Cloud app dashboard, click "⚙️ Settings"
2. Go to "Secrets" tab
3. Add the following secrets (copy from your local `.env` file):

```toml
# Azure AI Foundry Project Configuration
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT = "https://your-project.services.ai.azure.com/api/projects/yourProject"
AZURE_AI_FOUNDRY_MODEL_DEPLOYMENT_NAME = "gpt-4o"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = "https://your-resource.cognitiveservices.azure.com/"
AZURE_OPENAI_API_KEY = "your-azure-openai-api-key"

# Azure Computer Vision
AZURE_COMPUTER_VISION_ENDPOINT = "https://your-resource.cognitiveservices.azure.com/"
AZURE_COMPUTER_VISION_KEY = "your-computer-vision-key"

# FLUX API Configuration
FLUX_API_KEY = "your-flux-api-key"
FLUX_ENDPOINT = "https://your-project.services.ai.azure.com/openai/deployments/FLUX.1-Kontext-pro/images/generations?api-version=2025-04-01-preview"

# Model Configuration
MODEL_NAME = "gpt-5-chat"
DEPLOYMENT_NAME = "gpt-5-model"
GPT4O_DEPLOYMENT_NAME = "gpt-4o"
GPT5_DEPLOYMENT_NAME = "gpt-5-model"
DEFAULT_AGENT_MODEL = "gpt-4o"
DEFAULT_OUTPUT_MODEL = "gpt-5-model"

# API Configuration
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
MAX_TOKENS = "1000"
TEMPERATURE = "1.0"
TOP_P = "1.0"
```

**Important:** 
- Don't include quotes around the values in Streamlit Cloud secrets
- Make sure to replace all placeholder values with your actual credentials

## Step 3: Verify Deployment

### 3.1 Check App Status
- Your app should be accessible at: `https://share.streamlit.io/moamin1994/sandbox_project/main/streamlit_app.py`
- Look for successful startup messages in the logs

### 3.2 Test Features
1. **Azure AI Foundry Tracing**: Look for "✅ Azure authentication successful" in logs
2. **Agent System**: Test the multi-agent workflow
3. **Image Generation**: Verify FLUX API integration
4. **Computer Vision**: Test image analysis features

## Step 4: Monitor and Maintain

### 4.1 Logs and Debugging
- Access logs from your Streamlit Cloud dashboard
- Azure AI Foundry traces will appear in your Azure AI Foundry dashboard
- Monitor app performance and usage

### 4.2 Updates
- Push changes to your GitHub repository
- Streamlit Cloud will automatically redeploy
- No need to reconfigure secrets unless they change

## Troubleshooting

### Common Issues

**"Module not found" errors:**
- Check that all dependencies are in `requirements.txt`
- Verify Python version compatibility

**Azure authentication failures:**
- Verify all secrets are correctly set in Streamlit Cloud
- Check that Azure endpoints are correct and accessible
- Ensure API keys have proper permissions

**Tracing not working:**
- Check AZURE_AI_FOUNDRY_PROJECT_ENDPOINT format
- Verify Azure AI Foundry project is accessible
- Look for authentication success messages in logs

**App crashes on startup:**
- Check app logs in Streamlit Cloud dashboard
- Verify all required environment variables are set
- Check for import errors in dependencies

### Getting Help
- Streamlit Cloud documentation: https://docs.streamlit.io/streamlit-cloud
- Azure AI Foundry documentation: https://docs.microsoft.com/azure/ai-foundry/
- Check GitHub Issues for this repository

## Security Notes
- Never commit secrets to your repository
- Use Streamlit Cloud's secrets management for all sensitive data
- Regularly rotate your API keys
- Monitor usage and costs in Azure portal

## Next Steps
After successful deployment:
1. Share your app URL with users
2. Monitor usage through Azure AI Foundry dashboard
3. Consider setting up custom domains if needed
4. Plan for scaling based on usage patterns

---

🎉 **Congratulations!** Your ArchitectAI Studio is now deployed to Streamlit Cloud with full Azure AI Foundry integration!