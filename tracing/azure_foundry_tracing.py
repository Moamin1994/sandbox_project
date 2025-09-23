"""
Azure AI Foundry OpenTelemetry Tracing Configuration
Comprehensive observability for multi-agent orchestration with Azure Application Insights
"""

import os
import logging
from typing import Dict, Any, Optional
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor
import structlog

class AzureAIFoundryTracing:
    """
    Comprehensive OpenTelemetry tracing for Azure AI Foundry orchestration
    Provides full observability across agents, models, and workflows
    """
    
    def __init__(self):
        self.service_name = "ai-multi-agent-orchestrator"
        self.service_version = "1.0.0"
        self.environment = os.getenv("AZURE_ENV_NAME", "dev")
        self.connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP", "rg-ai-orchestrator-dev")
        
        # Initialize tracer and meter
        self.tracer = None
        self.meter = None
        
        # Initialize counters and histograms
        self.agent_execution_counter = None
        self.model_request_counter = None
        self.orchestration_duration_histogram = None
        self.agent_confidence_histogram = None
        
        self.logger = structlog.get_logger()
        
    def configure_tracing(self) -> trace.Tracer:
        """Configure comprehensive OpenTelemetry tracing for Azure AI Foundry"""
        try:
            # Create resource with comprehensive metadata
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": self.service_version,
                "service.instance.id": os.getenv("WEBSITE_INSTANCE_ID", "local"),
                "deployment.environment": self.environment,
                "cloud.provider": "azure",
                "cloud.platform": "azure_functions",
                "cloud.region": os.getenv("AZURE_LOCATION", "eastus2"),
                "cloud.resource_group": self.resource_group,
                "ai.orchestrator.type": "multi_agent",
                "ai.model.strategy": "gpt4o_agents_gpt5_output",
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.language": "python",
                "telemetry.sdk.version": "1.27.0"
            })
            
            # Configure Azure Monitor integration if connection string is available
            if self.connection_string:
                self.logger.info("Configuring Azure Monitor integration")
                configure_azure_monitor(
                    connection_string=self.connection_string,
                    resource=resource
                )
            else:
                self.logger.warning("Application Insights connection string not found")
                
                # Fallback to standard OTLP configuration
                provider = TracerProvider(resource=resource)
                
                # OTLP exporter for Azure AI Foundry
                otlp_exporter = OTLPSpanExporter(
                    endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4317"),
                    headers={}
                )
                
                processor = BatchSpanProcessor(
                    otlp_exporter,
                    max_queue_size=2048,
                    max_export_batch_size=512,
                    export_timeout_millis=30000,
                    schedule_delay_millis=5000
                )
                
                provider.add_span_processor(processor)
                trace.set_tracer_provider(provider)
            
            # Get tracer
            self.tracer = trace.get_tracer(
                __name__,
                version=self.service_version,
                schema_url="https://opentelemetry.io/schemas/1.21.0"
            )
            
            # Configure metrics
            self._configure_metrics()
            
            # Instrument libraries
            self._configure_instrumentation()
            
            self.logger.info("OpenTelemetry tracing configured successfully",
                           service=self.service_name,
                           environment=self.environment)
            
            return self.tracer
            
        except Exception as e:
            self.logger.error("Failed to configure tracing", error=str(e))
            # Return a no-op tracer to prevent application failure
            return trace.get_tracer(__name__)
    
    def _configure_metrics(self):
        """Configure custom metrics for AI orchestration monitoring"""
        try:
            # Get meter
            self.meter = metrics.get_meter(
                __name__,
                version=self.service_version
            )
            
            # Agent execution counter
            self.agent_execution_counter = self.meter.create_counter(
                name="ai_agent_executions_total",
                description="Total number of agent executions",
                unit="1"
            )
            
            # Model request counter
            self.model_request_counter = self.meter.create_counter(
                name="ai_model_requests_total",
                description="Total number of model API requests",
                unit="1"
            )
            
            # Orchestration duration histogram
            self.orchestration_duration_histogram = self.meter.create_histogram(
                name="ai_orchestration_duration_seconds",
                description="Duration of orchestration workflows",
                unit="s"
            )
            
            # Agent confidence histogram
            self.agent_confidence_histogram = self.meter.create_histogram(
                name="ai_agent_confidence_score",
                description="Confidence scores from agent responses",
                unit="1"
            )
            
            # Model token usage histogram
            self.token_usage_histogram = self.meter.create_histogram(
                name="ai_model_token_usage",
                description="Token usage for model requests",
                unit="1"
            )
            
            self.logger.info("Custom metrics configured successfully")
            
        except Exception as e:
            self.logger.error("Failed to configure metrics", error=str(e))
    
    def _configure_instrumentation(self):
        """Configure automatic instrumentation for AI and HTTP libraries"""
        try:
            # OpenAI instrumentation for GPT-4o and GPT-5
            OpenAIInstrumentor().instrument()
            
            # HTTP client instrumentation for FLUX and other APIs
            HTTPXClientInstrumentor().instrument()
            RequestsInstrumentor().instrument()
            
            self.logger.info("Automatic instrumentation configured")
            
        except Exception as e:
            self.logger.error("Failed to configure instrumentation", error=str(e))
    
    def trace_orchestration(self, request_data: Dict[str, Any]):
        """Create tracing context for orchestration workflow"""
        return self.tracer.start_as_current_span(
            "ai_orchestration_workflow",
            attributes={
                "orchestration.type": request_data.get("type", "general"),
                "orchestration.complexity": request_data.get("complexity", "medium"),
                "orchestration.generate_images": request_data.get("generate_images", False),
                "orchestration.user_id": request_data.get("user_id", "anonymous"),
                "orchestration.session_id": request_data.get("session_id", "default"),
                "orchestration.request_size": len(str(request_data))
            }
        )
    
    def trace_agent_execution(self, agent_name: str, agent_role: str, model: str):
        """Create tracing context for individual agent execution"""
        span = self.tracer.start_as_current_span(
            f"agent_execution_{agent_name}",
            attributes={
                "agent.name": agent_name,
                "agent.role": agent_role,
                "agent.model": model,
                "agent.type": "gpt4o_specialist"
            }
        )
        
        # Increment agent execution counter
        if self.agent_execution_counter:
            self.agent_execution_counter.add(1, {
                "agent_name": agent_name,
                "agent_role": agent_role,
                "agent_model": model
            })
        
        return span
    
    def trace_model_request(self, model: str, operation: str, tokens: int = 0):
        """Create tracing context for model API requests"""
        span = self.tracer.start_as_current_span(
            f"model_request_{model}",
            attributes={
                "model.name": model,
                "model.operation": operation,
                "model.tokens": tokens,
                "model.provider": "azure_openai" if "gpt" in model else "other"
            }
        )
        
        # Increment model request counter
        if self.model_request_counter:
            self.model_request_counter.add(1, {
                "model_name": model,
                "operation": operation
            })
        
        # Record token usage
        if self.token_usage_histogram and tokens > 0:
            self.token_usage_histogram.record(tokens, {
                "model_name": model,
                "operation": operation
            })
        
        return span
    
    def trace_workflow_step(self, step_name: str, step_type: str):
        """Create tracing context for workflow steps"""
        return self.tracer.start_as_current_span(
            f"workflow_step_{step_name}",
            attributes={
                "workflow.step": step_name,
                "workflow.type": step_type,
                "workflow.category": "multi_agent_collaboration"
            }
        )
    
    def record_agent_confidence(self, agent_name: str, confidence: float):
        """Record agent confidence score"""
        if self.agent_confidence_histogram:
            self.agent_confidence_histogram.record(confidence, {
                "agent_name": agent_name
            })
    
    def record_orchestration_duration(self, duration: float, workflow_type: str):
        """Record orchestration workflow duration"""
        if self.orchestration_duration_histogram:
            self.orchestration_duration_histogram.record(duration, {
                "workflow_type": workflow_type
            })
    
    def add_span_attributes(self, span, attributes: Dict[str, Any]):
        """Add custom attributes to current span"""
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    def add_span_event(self, span, event_name: str, attributes: Dict[str, Any] = None):
        """Add event to current span"""
        span.add_event(event_name, attributes or {})
    
    def record_exception(self, span, exception: Exception):
        """Record exception in span"""
        span.record_exception(exception)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))

# Global tracer instance
_tracer_instance = None

def get_tracer() -> AzureAIFoundryTracing:
    """Get global tracer instance"""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = AzureAIFoundryTracing()
        _tracer_instance.configure_tracing()
    return _tracer_instance

def configure_cloud_tracing() -> AzureAIFoundryTracing:
    """Configure tracing for cloud deployment"""
    return get_tracer()

# Tracing decorators for common patterns

def trace_agent_method(agent_name: str, agent_role: str, model: str = "gpt-4o"):
    """Decorator to trace agent methods"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.trace_agent_execution(agent_name, agent_role, model) as span:
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, dict) and "confidence" in result:
                        tracer.record_agent_confidence(agent_name, result["confidence"])
                    return result
                except Exception as e:
                    tracer.record_exception(span, e)
                    raise
        return wrapper
    return decorator

def trace_model_call(model: str, operation: str):
    """Decorator to trace model API calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.trace_model_request(model, operation) as span:
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, dict) and "usage" in result:
                        span.set_attribute("model.tokens_used", result["usage"].get("total_tokens", 0))
                    return result
                except Exception as e:
                    tracer.record_exception(span, e)
                    raise
        return wrapper
    return decorator

# Configuration for Azure AI Foundry Dashboard
AZURE_AI_FOUNDRY_TRACING_CONFIG = {
    "service_name": "ai-multi-agent-orchestrator",
    "service_version": "1.0.0",
    "custom_dimensions": {
        "ai.orchestrator.type": "multi_agent",
        "ai.model.strategy": "gpt4o_agents_gpt5_output_flux_images",
        "ai.platform": "azure_ai_foundry",
        "ai.environment": os.getenv("AZURE_ENV_NAME", "dev")
    },
    "trace_sampling_rate": float(os.getenv("TRACE_SAMPLE_RATE", "1.0")),
    "enable_metrics": True,
    "enable_logs": True,
    "log_level": os.getenv("LOG_LEVEL", "INFO")
}

if __name__ == "__main__":
    # Test tracing configuration
    tracer = configure_cloud_tracing()
    print("✅ Azure AI Foundry tracing configured successfully!")
    print(f"Service: {tracer.service_name}")
    print(f"Environment: {tracer.environment}")
    print(f"Connection String: {'✅ Configured' if tracer.connection_string else '❌ Missing'}")