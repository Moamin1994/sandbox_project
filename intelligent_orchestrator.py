"""
Intelligent Agent Orchestrator with Smart Routing and Collaboration
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass
from fixed_agents import SimpleAzureAgent

# OpenTelemetry imports for tracing
try:
    from opentelemetry import trace, context
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation import get_current_span
    from opentelemetry.semconv.trace import SpanAttributes
    TRACING_AVAILABLE = True
    tracer = trace.get_tracer(__name__)
except ImportError:
    TRACING_AVAILABLE = False
    tracer = None


class TaskType(Enum):
    VISION_ANALYSIS = "vision_analysis"
    ARCHITECTURAL_CONSULTATION = "architectural_consultation" 
    PROMPT_ENGINEERING = "prompt_engineering"
    QUALITY_ASSURANCE = "quality_assurance"
    STYLE_ANALYSIS = "style_analysis"
    TECHNICAL_REVIEW = "technical_review"


@dataclass
class AgentTask:
    task_type: TaskType
    input_data: str
    context: Dict[str, Any]
    dependencies: Set[TaskType]
    priority: int = 1
    completed: bool = False
    result: Optional[str] = None


class IntelligentOrchestrator:
    """Smart agent orchestrator with dynamic routing and collaboration"""
    
    def __init__(self):
        # Initialize specialized agents
        self.agents = {
            TaskType.VISION_ANALYSIS: SimpleAzureAgent(
                name="Vision Analyst",
                instructions="""You are an expert architectural vision analyst. 
                
                COLLABORATION PROTOCOL:
                - If analysis reveals specific architectural styles, flag for Style Analysis
                - If technical issues detected, flag for Technical Review
                - Always provide structured output with confidence scores
                
                Analyze images for: architectural style, spatial composition, materials, lighting, design principles.
                Return JSON format: {"analysis": "...", "style": "...", "technical_notes": "...", "confidence": 0.0-1.0, "next_steps": []}""",
                model_deployment="gpt-4o"
            ),
            
            TaskType.ARCHITECTURAL_CONSULTATION: SimpleAzureAgent(
                name="Architectural Expert", 
                instructions="""You are a senior architectural consultant with intelligent routing capabilities.
                
                COLLABORATION PROTOCOL:
                - Determine if additional specialist input needed
                - Route complex technical questions to Technical Review
                - Route style-specific requests to Style Analysis
                - Coordinate with other agents based on complexity
                
                Provide: recommendations, design strategy, technical considerations, space planning.
                Return JSON format: {"consultation": "...", "recommendations": [], "routing": [], "confidence": 0.0-1.0}""",
                model_deployment="gpt-4o"
            ),
            
            TaskType.PROMPT_ENGINEERING: SimpleAzureAgent(
                name="FLUX Prompt Engineer",
                instructions="""You are a FLUX prompt optimization specialist.
                
                COLLABORATION PROTOCOL:
                - Request clarification from Vision Analyst if image analysis unclear
                - Coordinate with Architectural Expert for technical accuracy
                - Validate prompts with Quality Assurance
                
                Create optimized FLUX prompts for architectural visualization.
                Return JSON format: {"prompt": "...", "style_tags": [], "technical_specs": [], "confidence": 0.0-1.0}""",
                model_deployment="gpt-4o"
            ),
            
            TaskType.QUALITY_ASSURANCE: SimpleAzureAgent(
                name="Quality Assurance",
                instructions="""You are a QA specialist with orchestration awareness.
                
                COLLABORATION PROTOCOL:
                - Review all agent outputs for consistency
                - Identify gaps requiring additional agent input
                - Coordinate final output compilation
                - Suggest workflow improvements
                
                Review and enhance architectural consultation outputs.
                Return JSON format: {"review": "...", "enhancements": [], "gaps": [], "final_output": "...", "confidence": 0.0-1.0}""",
                model_deployment="gpt-5-model"  # Premium model for final QA
            ),
            
            TaskType.STYLE_ANALYSIS: SimpleAzureAgent(
                name="Style Specialist",
                instructions="""You are an architectural style specialist.
                
                Focus on: historical context, style authenticity, regional variations, contemporary interpretations.
                Return JSON format: {"style_analysis": "...", "historical_context": "...", "recommendations": [], "confidence": 0.0-1.0}""",
                model_deployment="gpt-4o"
            ),
            
            TaskType.TECHNICAL_REVIEW: SimpleAzureAgent(
                name="Technical Reviewer", 
                instructions="""You are a technical architecture specialist.
                
                Focus on: structural considerations, building codes, technical feasibility, engineering constraints.
                Return JSON format: {"technical_review": "...", "constraints": [], "recommendations": [], "confidence": 0.0-1.0}""",
                model_deployment="gpt-4o"
            )
        }
        
        self.conversation_memory = {}
        self.workflow_history = []
    
    async def process_request(self, 
                            user_message: str, 
                            user_images: Optional[List[bytes]] = None,
                            session_id: str = "default") -> Dict[str, Any]:
        """Intelligent multi-agent processing with dynamic routing"""
        
        if TRACING_AVAILABLE and tracer:
            with tracer.start_as_current_span("intelligent_orchestrator.process_request") as span:
                span.set_attribute("session_id", session_id)
                span.set_attribute("has_images", bool(user_images))
                span.set_attribute("message_length", len(user_message))
                span.set_attribute("user_message_preview", user_message[:200] + "..." if len(user_message) > 200 else user_message)
                
                try:
                    result = await self._process_request_internal(user_message, user_images, session_id)
                    
                    # Add detailed workflow attributes
                    final_output = result.get('final_output', {})
                    self._add_workflow_attributes(span, final_output)
                    
                    span.set_attribute("workflow_tasks", len(result.get('workflow_executed', [])))
                    span.set_attribute("confidence_score", final_output.get('confidence_score', 0))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        else:
            return await self._process_request_internal(user_message, user_images, session_id)
    
    async def _process_request_internal(self, 
                                      user_message: str, 
                                      user_images: Optional[List[bytes]] = None,
                                      session_id: str = "default") -> Dict[str, Any]:
        """Internal processing method with tracing"""
        
        # Initialize session memory
        if session_id not in self.conversation_memory:
            self.conversation_memory[session_id] = {"context": "", "agent_outputs": {}}
        
        # Step 1: Determine initial workflow based on input
        initial_tasks = self._plan_workflow(user_message, user_images)
        
        # Step 2: Execute tasks with intelligent routing
        results = await self._execute_workflow(initial_tasks, user_message, user_images, session_id)
        
        # Step 3: Post-process and compile final output
        final_output = await self._compile_final_output(results, session_id)
        
        return final_output
    
    def _plan_workflow(self, user_message: str, user_images: Optional[List[bytes]]) -> List[AgentTask]:
        """Intelligently plan workflow based on input"""
        tasks = []
        
        # Always start with core tasks
        if user_images:
            tasks.append(AgentTask(
                task_type=TaskType.VISION_ANALYSIS,
                input_data=user_message,
                context={"has_images": True},
                dependencies=set(),
                priority=1
            ))
        
        tasks.append(AgentTask(
            task_type=TaskType.ARCHITECTURAL_CONSULTATION,
            input_data=user_message,
            context={},
            dependencies={TaskType.VISION_ANALYSIS} if user_images else set(),
            priority=2
        ))
        
        tasks.append(AgentTask(
            task_type=TaskType.PROMPT_ENGINEERING,
            input_data=user_message,
            context={},
            dependencies={TaskType.ARCHITECTURAL_CONSULTATION},
            priority=3
        ))
        
        tasks.append(AgentTask(
            task_type=TaskType.QUALITY_ASSURANCE,
            input_data=user_message,
            context={},
            dependencies={TaskType.PROMPT_ENGINEERING},
            priority=4
        ))
        
        # Conditional tasks based on content
        if any(keyword in user_message.lower() for keyword in ["style", "historical", "period", "classical", "modern"]):
            tasks.append(AgentTask(
                task_type=TaskType.STYLE_ANALYSIS,
                input_data=user_message,
                context={},
                dependencies={TaskType.VISION_ANALYSIS} if user_images else set(),
                priority=2
            ))
        
        if any(keyword in user_message.lower() for keyword in ["structural", "engineering", "technical", "code", "regulation"]):
            tasks.append(AgentTask(
                task_type=TaskType.TECHNICAL_REVIEW,
                input_data=user_message,
                context={},
                dependencies={TaskType.ARCHITECTURAL_CONSULTATION},
                priority=3
            ))
        
        return tasks
    
    async def _execute_workflow(self, 
                               tasks: List[AgentTask], 
                               user_message: str,
                               user_images: Optional[List[bytes]],
                               session_id: str) -> Dict[TaskType, str]:
        """Execute tasks with dependency management and intelligent routing"""
        
        results = {}
        remaining_tasks = tasks.copy()
        context = self.conversation_memory[session_id]["context"]
        
        while remaining_tasks:
            # Find tasks ready to execute (dependencies satisfied)
            ready_tasks = [
                task for task in remaining_tasks 
                if task.dependencies.issubset(set(results.keys()))
            ]
            
            if not ready_tasks:
                break  # Deadlock prevention
            
            # Execute ready tasks (can be parallel)
            for task in ready_tasks:
                if TRACING_AVAILABLE and tracer:
                    with tracer.start_as_current_span(f"agent_execution.{task.task_type.value}") as span:
                        span.set_attribute("task_type", task.task_type.value)
                        span.set_attribute("has_dependencies", len(task.dependencies) > 0)
                        span.set_attribute("dependency_count", len(task.dependencies))
                        span.set_attribute("priority", task.priority)
                        
                        try:
                            print(f"🤖 Executing {task.task_type.value}...")
                            result = await self._execute_single_task(task, user_images, session_id, results, context)
                            results[task.task_type] = result
                            span.set_attribute("result_length", len(str(result)))
                            span.set_status(Status(StatusCode.OK))
                        except Exception as e:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                            print(f"❌ Error executing {task.task_type.value}: {e}")
                            results[task.task_type] = f"Error: {str(e)}"
                else:
                    print(f"🤖 Executing {task.task_type.value}...")
                    try:
                        result = await self._execute_single_task(task, user_images, session_id, results, context)
                        results[task.task_type] = result
                    except Exception as e:
                        print(f"❌ Error executing {task.task_type.value}: {e}")
                        results[task.task_type] = f"Error: {str(e)}"
                
                # Mark task as completed
                task.completed = True
                task.result = results.get(task.task_type, "")
                
                # Dynamic routing: check if agent suggests additional tasks
                additional_tasks = self._parse_routing_suggestions(results.get(task.task_type, ""), task.task_type)
                for new_task in additional_tasks:
                    if new_task not in [t.task_type for t in remaining_tasks]:
                        remaining_tasks.append(AgentTask(
                            task_type=new_task,
                            input_data=user_message,
                            context={"dynamic_routing": True},
                            dependencies={task.task_type},
                            priority=5
                        ))
                
                remaining_tasks.remove(task)
        
        return results
    
    async def _execute_single_task(self, task: AgentTask, user_images: Optional[List[bytes]], 
                                  session_id: str, results: Dict[TaskType, str], context: str) -> str:
        """Execute a single agent task with proper context"""
        
        # Prepare context from previous results
        task_context = context
        for dep in task.dependencies:
            if dep in results:
                task_context += f"\n{dep.value}: {results[dep]}\n"
        
        # Execute agent
        agent = self.agents[task.task_type]
        if task.task_type == TaskType.VISION_ANALYSIS and user_images:
            result = agent.process_request(task.input_data, images=user_images, context=task_context)
        else:
            result = agent.process_request(task.input_data, context=task_context)
        
        return result
    
    def _parse_routing_suggestions(self, agent_result: str, source_task: TaskType) -> List[TaskType]:
        """Parse agent results for routing suggestions"""
        suggestions = []
        
        # Simple keyword-based routing (could be enhanced with JSON parsing)
        if "style analysis" in agent_result.lower() and source_task != TaskType.STYLE_ANALYSIS:
            suggestions.append(TaskType.STYLE_ANALYSIS)
        
        if "technical review" in agent_result.lower() and source_task != TaskType.TECHNICAL_REVIEW:
            suggestions.append(TaskType.TECHNICAL_REVIEW)
        
        return suggestions
    
    async def _compile_final_output(self, results: Dict[TaskType, str], session_id: str) -> Dict[str, Any]:
        """Compile and enhance final output with tracing"""
        
        if TRACING_AVAILABLE and tracer:
            with tracer.start_as_current_span("intelligent_orchestrator.compile_final_output") as span:
                span.set_attribute("session_id", session_id)
                span.set_attribute("results_count", len(results))
                span.set_attribute("workflow_tasks", [task.value for task in results.keys()])
                
                try:
                    # Update conversation memory
                    self.conversation_memory[session_id]["agent_outputs"] = results
                    
                    # Extract key information
                    final_output = {
                        'workflow_executed': list(results.keys()),
                        'architectural_analysis': results.get(TaskType.VISION_ANALYSIS, ''),
                        'expert_consultation': results.get(TaskType.ARCHITECTURAL_CONSULTATION, ''),
                        'style_analysis': results.get(TaskType.STYLE_ANALYSIS, ''),
                        'technical_review': results.get(TaskType.TECHNICAL_REVIEW, ''),
                        'optimized_prompt': results.get(TaskType.PROMPT_ENGINEERING, ''),
                        'quality_review': results.get(TaskType.QUALITY_ASSURANCE, ''),
                        'confidence_score': self._calculate_overall_confidence(results),
                        'agent_collaboration': True,
                        'intelligent_routing': True
                    }
                    
                    span.set_attribute("confidence_score", final_output['confidence_score'])
                    span.set_status(Status(StatusCode.OK))
                    return {'final_output': final_output, 'all_results': results}
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        else:
            # Fallback without tracing
            self.conversation_memory[session_id]["agent_outputs"] = results
            
            final_output = {
                'workflow_executed': list(results.keys()),
                'architectural_analysis': results.get(TaskType.VISION_ANALYSIS, ''),
                'expert_consultation': results.get(TaskType.ARCHITECTURAL_CONSULTATION, ''),
                'style_analysis': results.get(TaskType.STYLE_ANALYSIS, ''),
                'technical_review': results.get(TaskType.TECHNICAL_REVIEW, ''),
                'optimized_prompt': results.get(TaskType.PROMPT_ENGINEERING, ''),
                'quality_review': results.get(TaskType.QUALITY_ASSURANCE, ''),
                'confidence_score': self._calculate_overall_confidence(results),
                'agent_collaboration': True,
                'intelligent_routing': True
            }
            
            return {'final_output': final_output, 'all_results': results}
    
    def _calculate_overall_confidence(self, results: Dict[TaskType, str]) -> float:
        """Calculate overall confidence based on agent outputs"""
        # Simple confidence calculation (could be enhanced with JSON parsing)
        base_confidence = 0.8 if len(results) >= 3 else 0.6
        
        # Boost confidence if additional specialists were consulted
        if TaskType.STYLE_ANALYSIS in results:
            base_confidence += 0.05
        if TaskType.TECHNICAL_REVIEW in results:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)

    def _add_workflow_attributes(self, span, workflow_data: Dict[str, Any]):
        """Add custom workflow attributes to tracing span"""
        if not TRACING_AVAILABLE or not span:
            return
        
        # Core workflow attributes
        span.set_attribute("ai.workflow.type", "architectural_consultation")
        span.set_attribute("ai.workflow.agent_count", len(self.agents))
        span.set_attribute("ai.workflow.orchestrator", "intelligent")
        
        # Task execution attributes
        if 'workflow_executed' in workflow_data:
            executed_tasks = workflow_data['workflow_executed']
            span.set_attribute("ai.workflow.tasks_executed", len(executed_tasks))
            span.set_attribute("ai.workflow.task_types", [t.value if hasattr(t, 'value') else str(t) for t in executed_tasks])
        
        # Quality metrics
        if 'confidence_score' in workflow_data:
            span.set_attribute("ai.workflow.confidence", workflow_data['confidence_score'])
        
        # Collaboration indicators
        span.set_attribute("ai.workflow.collaboration_enabled", workflow_data.get('agent_collaboration', False))
        span.set_attribute("ai.workflow.intelligent_routing", workflow_data.get('intelligent_routing', False))


# Global instance
intelligent_orchestrator = IntelligentOrchestrator()