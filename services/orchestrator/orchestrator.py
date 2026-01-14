"""
Orchestrator - Main Orchestration Logic

This class implements the core orchestrator functionality:
- Intent classification
- Query planning
- Worker coordination
- Response validation
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, List, Optional, Any
from datetime import datetime

import httpx
import ollama
from loguru import logger
from pydantic import BaseModel, Field

from lib.intent_classifier import IntentClassifier, Classification, IntentType
from lib.query_planner import QueryPlanner, QueryPlan
from lib.response_validator import ResponseValidator, ValidationResult
from lib.streaming_handler import StreamingHandler, ThinkingStep, ThinkingStepType


class WorkerResponse(BaseModel):
    """Response from worker service."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None


class OrchestratorResult(BaseModel):
    """Final orchestrated result."""
    answer: str
    confidence: float
    intent: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    thinking_steps: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Orchestrator:
    """
    Main orchestrator class.
    
    Coordinates intent classification, query planning, worker execution,
    and response validation using a lighter LLM for fast decision-making.
    """
    
    def __init__(
        self,
        ollama_url: str,
        worker_api_url: str,
        model: str = "qwen2.5:14b",
        temperature: float = 0.3,
        confidence_threshold: float = 0.7,
    ):
        """
        Initialize orchestrator.
        
        Args:
            ollama_url: URL of Ollama service
            worker_api_url: URL of worker API
            model: Model name for orchestrator LLM
            temperature: LLM temperature (lower = more deterministic)
            confidence_threshold: Minimum confidence to proceed
        """
        self.ollama_url = ollama_url
        self.worker_api_url = worker_api_url
        self.model = model
        self.temperature = temperature
        self.confidence_threshold = confidence_threshold
        
        # Initialize components
        self.client = ollama.AsyncClient(host=ollama_url)
        self.http_client = httpx.AsyncClient(timeout=120.0)
        
        self.intent_classifier = IntentClassifier(
            client=self.client,
            model=model,
            temperature=temperature,
        )
        
        self.query_planner = QueryPlanner(
            client=self.client,
            model=model,
        )
        
        self.response_validator = ResponseValidator(
            client=self.client,
            model=model,
        )
        
        self.streaming_handler = StreamingHandler()
        
        logger.info(f"Orchestrator initialized with model: {model}")
    
    async def verify_connection(self) -> bool:
        """
        Verify connection to Ollama service.
        
        Returns:
            True if connection successful
            
        Raises:
            Exception if connection fails
        """
        try:
            models = await self.client.list()
            logger.debug(f"Connected to Ollama, {len(models.get('models', []))} models available")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise
    
    async def classify_intent(self, question: str) -> Classification:
        """
        Classify the intent of a user question.
        
        Args:
            question: User's question
            
        Returns:
            Classification result with intent type and extracted parameters
        """
        logger.info("Step 1: Classifying intent...")
        classification = await self.intent_classifier.classify(question)
        
        logger.info(
            f"Intent: {classification.intent_type}, "
            f"Confidence: {classification.confidence:.2f}"
        )
        
        return classification
    
    async def plan_query(
        self,
        question: str,
        classification: Classification,
    ) -> QueryPlan:
        """
        Plan how to execute the query based on classification.
        
        Args:
            question: Original question
            classification: Intent classification result
            
        Returns:
            Query execution plan
        """
        logger.info("Step 2: Planning query strategy...")
        plan = await self.query_planner.plan(question, classification)
        
        logger.info(f"Plan: {plan.strategy}, Steps: {len(plan.steps)}")
        
        return plan
    
    async def execute_via_worker(
        self,
        plan: QueryPlan,
        classification: Classification,
    ) -> WorkerResponse:
        """
        Execute query via worker API.
        
        Args:
            plan: Query execution plan
            classification: Intent classification
            
        Returns:
            Worker response
        """
        logger.info("Step 3: Executing via worker...")
        
        try:
            # Prepare worker request
            worker_request = {
                "task_type": classification.intent_type,
                "question": classification.original_question,
                "params": classification.extracted_params,
                "plan": plan.model_dump(),
                "config": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            }
            
            # Call worker API
            response = await self.http_client.post(
                f"{self.worker_api_url}/execute",
                json=worker_request,
                timeout=120.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                return WorkerResponse(**data)
            else:
                logger.error(f"Worker returned error: {response.status_code}")
                return WorkerResponse(
                    success=False,
                    error=f"Worker error: {response.status_code}",
                )
                
        except Exception as e:
            logger.error(f"Error calling worker: {e}")
            return WorkerResponse(
                success=False,
                error=str(e),
            )
    
    async def validate_response(
        self,
        question: str,
        answer: str,
        citations: List[Dict[str, Any]],
    ) -> ValidationResult:
        """
        Validate worker response.
        
        Args:
            question: Original question
            answer: Generated answer
            citations: Citations provided
            
        Returns:
            Validation result
        """
        logger.info("Step 4: Validating response...")
        validation = await self.response_validator.validate(
            question=question,
            answer=answer,
            citations=citations,
        )
        
        logger.info(f"Validation: {'✓ Passed' if validation.is_valid else '✗ Failed'}")
        
        return validation
    
    async def process_question(
        self,
        question: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a question through the full orchestration pipeline.
        
        Non-streaming version that returns complete result.
        
        Args:
            question: User's question
            session_id: Optional session ID for context
            
        Returns:
            Complete orchestrated result
        """
        start_time = datetime.now()
        thinking_steps = []
        
        try:
            # Step 1: Classify intent
            classification = await self.classify_intent(question)
            thinking_steps.append({
                "type": "classification",
                "content": f"Intent: {classification.intent_type}, Confidence: {classification.confidence:.2f}",
                "timestamp": datetime.now().isoformat(),
            })
            
            # Check confidence threshold
            if classification.confidence < self.confidence_threshold:
                return {
                    "answer": "I'm not quite sure what you're asking. Could you rephrase your question or provide more details?",
                    "confidence": classification.confidence,
                    "intent": "clarification_needed",
                    "citations": [],
                    "thinking_steps": thinking_steps,
                }
            
            # Handle clarification needed
            if classification.intent_type == IntentType.CLARIFICATION_NEEDED:
                return {
                    "answer": classification.clarification_question or "Could you provide more details?",
                    "confidence": classification.confidence,
                    "intent": classification.intent_type,
                    "citations": [],
                    "thinking_steps": thinking_steps,
                }
            
            # Step 2: Plan query
            plan = await self.plan_query(question, classification)
            thinking_steps.append({
                "type": "planning",
                "content": f"Strategy: {plan.strategy}",
                "timestamp": datetime.now().isoformat(),
            })
            
            # Step 3: Execute via worker
            worker_response = await self.execute_via_worker(plan, classification)
            
            if not worker_response.success:
                return {
                    "answer": f"I encountered an error: {worker_response.error}",
                    "confidence": 0.0,
                    "intent": classification.intent_type,
                    "citations": [],
                    "thinking_steps": thinking_steps,
                    "error": worker_response.error,
                }
            
            thinking_steps.append({
                "type": "execution",
                "content": "Worker executed successfully",
                "timestamp": datetime.now().isoformat(),
            })
            
            # Extract answer and citations
            result = worker_response.result or {}
            answer = result.get("answer", "No answer provided")
            citations = result.get("citations", [])
            
            # Step 4: Validate response
            validation = await self.validate_response(
                question=question,
                answer=answer,
                citations=citations,
            )
            
            thinking_steps.append({
                "type": "validation",
                "content": "Response validated" if validation.is_valid else "Validation issues found",
                "timestamp": datetime.now().isoformat(),
            })
            
            # Use validated answer if available
            final_answer = validation.improved_answer or answer
            
            # Calculate total time
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "answer": final_answer,
                "confidence": classification.confidence,
                "intent": classification.intent_type,
                "citations": citations,
                "thinking_steps": thinking_steps,
                "metadata": {
                    "elapsed_time_seconds": elapsed_time,
                    "validation_passed": validation.is_valid,
                    "worker_success": worker_response.success,
                },
            }
            
        except Exception as e:
            logger.error(f"Error in orchestration: {e}", exc_info=True)
            return {
                "answer": f"I encountered an error processing your question: {str(e)}",
                "confidence": 0.0,
                "intent": "error",
                "citations": [],
                "thinking_steps": thinking_steps,
                "error": str(e),
            }
    
    async def process_question_streaming(
        self,
        question: str,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a question with streaming thinking process.
        
        Yields SSE events showing the AI's thinking process.
        
        Args:
            question: User's question
            session_id: Optional session ID
            
        Yields:
            SSE events with thinking steps and final answer
        """
        try:
            # Emit start event
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.THOUGHT,
                content=f"Processing your question: {question[:100]}...",
            ))
            
            # Step 1: Classify intent
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.THOUGHT,
                content="Analyzing your question to understand what you're asking...",
            ))
            
            classification = await self.classify_intent(question)
            
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.OBSERVATION,
                content=f"Identified intent: {classification.intent_type} (confidence: {classification.confidence:.0%})",
                data={"classification": classification.model_dump()},
            ))
            
            # Check confidence
            if classification.confidence < self.confidence_threshold:
                yield self.streaming_handler.format_event(ThinkingStep(
                    step_type=ThinkingStepType.FINAL_ANSWER,
                    content="I'm not quite sure what you're asking. Could you rephrase?",
                ))
                return
            
            # Handle clarification needed
            if classification.intent_type == IntentType.CLARIFICATION_NEEDED:
                yield self.streaming_handler.format_event(ThinkingStep(
                    step_type=ThinkingStepType.FINAL_ANSWER,
                    content=classification.clarification_question or "Could you provide more details?",
                ))
                return
            
            # Step 2: Plan query
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.THOUGHT,
                content="Planning how to answer your question...",
            ))
            
            plan = await self.plan_query(question, classification)
            
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.ACTION,
                content=f"Executing strategy: {plan.strategy}",
            ))
            
            # Step 3: Execute via worker
            worker_response = await self.execute_via_worker(plan, classification)
            
            if not worker_response.success:
                yield self.streaming_handler.format_event(ThinkingStep(
                    step_type=ThinkingStepType.FINAL_ANSWER,
                    content=f"I encountered an error: {worker_response.error}",
                ))
                return
            
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.OBSERVATION,
                content="Retrieved information from knowledge base",
            ))
            
            # Extract answer and citations
            result = worker_response.result or {}
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            
            # Step 4: Validate
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.THOUGHT,
                content="Validating the answer quality...",
            ))
            
            validation = await self.validate_response(
                question=question,
                answer=answer,
                citations=citations,
            )
            
            if validation.is_valid:
                yield self.streaming_handler.format_event(ThinkingStep(
                    step_type=ThinkingStepType.OBSERVATION,
                    content="✓ Answer validated successfully",
                ))
            else:
                yield self.streaming_handler.format_event(ThinkingStep(
                    step_type=ThinkingStepType.OBSERVATION,
                    content=f"Validation issues: {', '.join(validation.issues)}",
                ))
            
            # Final answer
            final_answer = validation.improved_answer or answer
            
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.FINAL_ANSWER,
                content=final_answer,
                data={
                    "citations": citations,
                    "confidence": classification.confidence,
                    "intent": classification.intent_type,
                },
            ))
            
        except Exception as e:
            logger.error(f"Error in streaming orchestration: {e}", exc_info=True)
            yield self.streaming_handler.format_event(ThinkingStep(
                step_type=ThinkingStepType.FINAL_ANSWER,
                content=f"Error: {str(e)}",
            ))
