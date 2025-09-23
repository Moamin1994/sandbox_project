"""
Setup proper OpenTelemetry tracing for Azure AI Foundry dashboard visibility
"""
import os

def setup_azure_tracing():
    """Configure OpenTelemetry tracing for Azure AI Foundry"""
    
    # Always try to setup Azure AI Foundry tracing (local development can connect to Azure)
    print("🔧 Setting up Azure AI Foundry tracing...")
    
    # Enable content recording for prompts and completions
    os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
    os.environ["AZURE_SDK_TRACING_IMPLEMENTATION"] = "opentelemetry"
    os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"
    
    # Disable automatic OTLP exporter configuration that might point to localhost
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""
    os.environ["OTEL_TRACES_EXPORTER"] = "none"
    os.environ["OTEL_METRICS_EXPORTER"] = "none"
    os.environ["OTEL_LOGS_EXPORTER"] = "none"
    
    try:
        from opentelemetry import trace, _events, _logs
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._events import EventLoggerProvider
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        
        # Setup resource
        resource = Resource(attributes={
            "service.name": "ArchitectAI-AzureFoundry"
        })
        
        # Get Azure AI Foundry endpoint from environment
        foundry_endpoint = os.environ.get("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
        if not foundry_endpoint:
            print("⚠️ AZURE_AI_FOUNDRY_PROJECT_ENDPOINT not found - using console tracing only")
            provider = TracerProvider(resource=resource)
            # Add console exporter for development visibility
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            trace.set_tracer_provider(provider)
        else:
            # Configure Azure AI Foundry tracing endpoint
            # Extract base URL and construct telemetry endpoint
            base_url = foundry_endpoint.replace('/api/projects/', '/').split('/api/')[0]
            traces_endpoint = f"{base_url}/v1/traces"
            logs_endpoint = f"{base_url}/v1/logs"
            
            print(f"🔗 Configuring tracing for Azure AI Foundry: {base_url}")
            
            # Setup tracer provider with Azure AI Foundry endpoint
            provider = TracerProvider(resource=resource)
            
            # Use Azure authentication for the exporter
            try:
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
                
                # Get access token for Azure AI services
                token = credential.get_token("https://cognitiveservices.azure.com/.default")
                headers = {
                    "Authorization": f"Bearer {token.token}",
                    "Content-Type": "application/json"
                }
                
                otlp_exporter = OTLPSpanExporter(
                    endpoint=traces_endpoint,
                    headers=headers
                )
                processor = BatchSpanProcessor(otlp_exporter)
                provider.add_span_processor(processor)
                
                # Setup logging with Azure authentication
                _logs.set_logger_provider(LoggerProvider())
                _logs.get_logger_provider().add_log_record_processor(
                    BatchLogRecordProcessor(OTLPLogExporter(
                        endpoint=logs_endpoint,
                        headers=headers
                    ))
                )
                
                print(f"✅ Azure authentication successful, traces will be sent to {traces_endpoint}")
                
            except Exception as e:
                print(f"⚠️ Azure authentication failed: {e}")
                print("📱 Using console tracing only")
                # Fallback to console tracing without Azure endpoints
                console_exporter = ConsoleSpanExporter()
                processor = BatchSpanProcessor(console_exporter)
                provider.add_span_processor(processor)
            
            trace.set_tracer_provider(provider)
        
        # Setup event logger
        _events.set_event_logger_provider(EventLoggerProvider())
        
        # Enable Azure AI telemetry (if available)
        try:
            from azure.ai.projects import enable_telemetry
            enable_telemetry()
            print("✅ Azure AI telemetry enabled")
        except ImportError:
            print("⚠️ enable_telemetry not available in current azure-ai-projects version")
        
        print("✅ OpenTelemetry tracing configured for Azure AI Foundry dashboard")
        return True
        
    except ImportError as e:
        print(f"⚠️ OpenTelemetry packages not installed: {e}")
        print("Run: pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-http opentelemetry-instrumentation-openai-v2")
        return False
    except Exception as e:
        print(f"❌ Error setting up tracing: {e}")
        return False

if __name__ == "__main__":
    setup_azure_tracing()