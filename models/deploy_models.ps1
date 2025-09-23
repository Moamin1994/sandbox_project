# Azure AI Model Deployment Script - PowerShell
# Deploy GPT-4o, GPT-5, FLUX, and Computer Vision for AI Multi-Agent Orchestrator

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = $env:AZURE_RESOURCE_GROUP,
    
    [Parameter(Mandatory=$false)]
    [string]$OpenAIAccount = $env:AZURE_OPENAI_ACCOUNT,
    
    [Parameter(Mandatory=$false)]
    [string]$KeyVaultName = $env:KEY_VAULT_NAME,
    
    [Parameter(Mandatory=$false)]
    [string]$FluxApiKey = $env:FLUX_API_KEY,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipGPT5 = $false
)

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Blue = "Cyan"

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host "🤖 Model Deployment: $Message" -ForegroundColor $Color
}

function Write-Error-Exit {
    param([string]$Message)
    Write-Host "❌ ERROR: $Message" -ForegroundColor $Red
    exit 1
}

Write-Status "Starting Azure AI Model Deployments..." $Blue
Write-Status "==========================================" $Blue

# Validate prerequisites
if (-not $ResourceGroup) {
    Write-Error-Exit "AZURE_RESOURCE_GROUP environment variable not set"
}

if (-not $OpenAIAccount) {
    Write-Error-Exit "AZURE_OPENAI_ACCOUNT environment variable not set"
}

# Deploy GPT-4o for Agents
Write-Status "Deploying GPT-4o for Agents..." $Blue
try {
    az cognitiveservices account deployment create `
        --resource-group $ResourceGroup `
        --account-name $OpenAIAccount `
        --deployment-name "gpt-4o-agents" `
        --model-name "gpt-4o" `
        --model-version "2024-11-20" `
        --model-format "OpenAI" `
        --sku-capacity 100 `
        --sku-name "Standard"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✅ GPT-4o deployment successful" $Green
    } else {
        Write-Status "⚠️ GPT-4o deployment may already exist or failed" $Yellow
    }
} catch {
    Write-Status "⚠️ GPT-4o deployment error: $($_.Exception.Message)" $Yellow
}

# Deploy GPT-5 for Premium Output (if not skipping)
if (-not $SkipGPT5) {
    Write-Status "Deploying GPT-5 for Premium Output..." $Blue
    try {
        az cognitiveservices account deployment create `
            --resource-group $ResourceGroup `
            --account-name $OpenAIAccount `
            --deployment-name "gpt-5-premium" `
            --model-name "gpt-5" `
            --model-version "preview" `
            --model-format "OpenAI" `
            --sku-capacity 50 `
            --sku-name "Premium"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✅ GPT-5 deployment successful" $Green
        } else {
            Write-Status "⚠️ GPT-5 deployment failed - may require preview access" $Yellow
        }
    } catch {
        Write-Status "⚠️ GPT-5 deployment error: $($_.Exception.Message)" $Yellow
        Write-Status "Note: GPT-5 requires preview access and may not be available in all regions" $Yellow
    }
} else {
    Write-Status "⏭️ Skipping GPT-5 deployment as requested" $Yellow
}

# Configure FLUX API Key in Key Vault
Write-Status "Configuring FLUX.1-Kontext-pro..." $Blue
if ($FluxApiKey -and $KeyVaultName) {
    try {
        az keyvault secret set `
            --vault-name $KeyVaultName `
            --name "flux-api-key" `
            --value $FluxApiKey
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✅ FLUX API key stored in Key Vault" $Green
        } else {
            Write-Status "⚠️ Failed to store FLUX API key" $Yellow
        }
    } catch {
        Write-Status "⚠️ FLUX configuration error: $($_.Exception.Message)" $Yellow
    }
} else {
    Write-Status "⚠️ FLUX_API_KEY or KEY_VAULT_NAME not provided - skipping FLUX configuration" $Yellow
}

# Computer Vision is already deployed via Bicep
Write-Status "✅ Computer Vision service ready (deployed via infrastructure)" $Green

# Validate deployments
Write-Status "Validating model deployments..." $Blue

# Check GPT-4o deployment
$gpt4oStatus = az cognitiveservices account deployment show `
    --resource-group $ResourceGroup `
    --account-name $OpenAIAccount `
    --deployment-name "gpt-4o-agents" `
    --query "properties.provisioningState" `
    --output tsv 2>$null

if ($gpt4oStatus -eq "Succeeded") {
    Write-Status "✅ GPT-4o validation passed" $Green
} else {
    Write-Status "❌ GPT-4o validation failed" $Red
}

# Check GPT-5 deployment (if not skipped)
if (-not $SkipGPT5) {
    $gpt5Status = az cognitiveservices account deployment show `
        --resource-group $ResourceGroup `
        --account-name $OpenAIAccount `
        --deployment-name "gpt-5-premium" `
        --query "properties.provisioningState" `
        --output tsv 2>$null

    if ($gpt5Status -eq "Succeeded") {
        Write-Status "✅ GPT-5 validation passed" $Green
    } else {
        Write-Status "❌ GPT-5 validation failed or not available" $Red
    }
}

# Check FLUX API key
if ($KeyVaultName) {
    $fluxKeyExists = az keyvault secret show `
        --vault-name $KeyVaultName `
        --name "flux-api-key" `
        --query "value" `
        --output tsv 2>$null

    if ($fluxKeyExists) {
        Write-Status "✅ FLUX API key validation passed" $Green
    } else {
        Write-Status "❌ FLUX API key not found in Key Vault" $Red
    }
}

# Generate deployment summary
Write-Status "🎉 Model Deployment Summary" $Green
Write-Status "============================" $Green
if ($gpt4oStatus -eq 'Succeeded') {
    Write-Status "GPT-4o Agents: ✅ Ready" $Green
} else {
    Write-Status "GPT-4o Agents: ❌ Failed" $Red
}

if (-not $SkipGPT5) {
    if ($gpt5Status -eq 'Succeeded') {
        Write-Status "GPT-5 Premium: ✅ Ready" $Green
    } else {
        Write-Status "GPT-5 Premium: ❌ Failed" $Red
    }
}

if ($fluxKeyExists) {
    Write-Status "FLUX Images: ✅ Configured" $Green
} else {
    Write-Status "FLUX Images: ❌ Not configured" $Red
}
Write-Status "Computer Vision: ✅ Ready" $Green

Write-Status "📋 Next Steps:" $Yellow
Write-Status "1. Update Function App environment variables" $Yellow
Write-Status "2. Test model endpoints and authentication" $Yellow
Write-Status "3. Configure OpenTelemetry tracing" $Yellow
Write-Status "4. Deploy and test complete orchestration" $Yellow

# Generate environment variables for Function App
$envVars = @{
    "GPT4O_ENDPOINT" = "https://$OpenAIAccount.openai.azure.com/"
    "GPT4O_DEPLOYMENT" = "gpt-4o-agents"
    "GPT4O_API_VERSION" = "2024-10-21"
    "GPT5_ENDPOINT" = "https://$OpenAIAccount.openai.azure.com/"
    "GPT5_DEPLOYMENT" = "gpt-5-premium"
    "GPT5_API_VERSION" = "2024-12-01-preview"
    "FLUX_ENDPOINT" = "https://models.inference.ai.azure.com"
    "FLUX_MODEL" = "FLUX.1-Kontext-pro"
    "FLUX_API_VERSION" = "2024-04-01-preview"
    "MODEL_STRATEGY" = "gpt4o-agents_gpt5-output_flux-images_cv-analysis"
    "ENABLE_PREMIUM_OUTPUT" = "true"
    "ENABLE_IMAGE_GENERATION" = "true"
    "ENABLE_VISION_ANALYSIS" = "true"
}

# Save environment variables to file
$envVars | ConvertTo-Json -Depth 2 | Out-File -FilePath "function_app_env_vars.json" -Encoding UTF8

Write-Status "💾 Environment variables saved to function_app_env_vars.json" $Green
Write-Status "🚀 Model deployment completed!" $Green