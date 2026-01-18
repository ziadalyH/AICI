"""Agentic AI System with OpenAI Function Calling.

This module implements a complete agentic workflow using OpenAI's function calling
to enable multi-step reasoning, tool use, and autonomous decision-making.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI

from config.config import Config
from .models import PDFResult, PDFResponse, NoAnswerResponse
from .retrieval.retrieval_engine import RetrievalEngine
from .retrieval.query_processor import QueryProcessor
from config.prompt_templates import PromptTemplates


class AgenticRAGSystem:
    """
    Agentic RAG system with multi-step reasoning and tool use.
    
    This system can:
    - Break down complex tasks into steps
    - Use tools autonomously (retrieve, analyze, generate, verify)
    - Self-verify and iterate on solutions
    - Maintain conversation context
    """
    
    def __init__(
        self,
        config: Config,
        retrieval_engine: RetrievalEngine,
        query_processor: QueryProcessor,
        logger: logging.Logger
    ):
        """
        Initialize the agentic system.
        
        Args:
            config: Configuration object
            retrieval_engine: Engine for retrieving documents
            query_processor: Processor for queries
            logger: Logger instance
        """
        self.config = config
        self.retrieval_engine = retrieval_engine
        self.query_processor = query_processor
        self.logger = logger
        self.openai_client = OpenAI(api_key=config.llm_api_key)
        self.prompt_templates = PromptTemplates()
        
        # Define available tools/functions
        self.functions = self._define_functions()
        
        self.logger.info("🤖 Initialized Agentic RAG System with function calling")
    
    def _define_functions(self) -> List[Dict[str, Any]]:
        """
        Define available functions for the agent.
        
        Returns:
            List of function definitions in OpenAI format
        """
        return [
            {
                "name": "retrieve_regulations",
                "description": "Retrieve relevant building regulations from the knowledge base. Use this when you need to find specific rules, requirements, or regulations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant regulations"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to retrieve (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "analyze_drawing_compliance",
                "description": "Analyze the user's building drawing against regulations to identify compliance issues. Uses the drawing from the current context. Returns a structured analysis of violations and compliant aspects.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regulations": {
                            "type": "array",
                            "description": "List of relevant regulations to check against",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["regulations"]
                }
            },
            {
                "name": "calculate_drawing_dimensions",
                "description": "Calculate specific dimensions from the user's building drawing (plot area, extension depth, building height, etc.). Uses the drawing from the current context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dimension_type": {
                            "type": "string",
                            "enum": ["plot_area", "extension_depth", "building_height", "all"],
                            "description": "Type of dimension to calculate"
                        }
                    },
                    "required": ["dimension_type"]
                }
            },
            {
                "name": "generate_compliant_design",
                "description": "Generate an adjusted, compliant version of a building drawing based on identified violations. Returns corrected JSON with explanations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "original_drawing": {
                            "type": "object",
                            "description": "The original non-compliant drawing"
                        },
                        "violations": {
                            "type": "array",
                            "description": "List of violations to fix",
                            "items": {"type": "string"}
                        },
                        "regulations": {
                            "type": "array",
                            "description": "Relevant regulations to comply with",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["original_drawing", "violations", "regulations"]
                }
            },
            {
                "name": "verify_compliance",
                "description": "Verify if the user's building drawing complies with regulations. Uses the drawing from the current context. Returns true/false with detailed explanation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regulations": {
                            "type": "array",
                            "description": "Regulations to verify against",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["regulations"]
                }
            }
        ]
    
    def process_with_agent(
        self,
        query: str,
        drawing_json: Optional[Dict[str, Any]] = None,
        drawing_updated_at: Optional[str] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Process a query using the agentic workflow with function calling.
        
        Args:
            query: User's question
            drawing_json: Optional building drawing JSON
            drawing_updated_at: Optional timestamp
            max_iterations: Maximum number of agent iterations
            
        Returns:
            Dictionary with answer, reasoning steps, and sources
        """
        self.logger.info("=" * 80)
        self.logger.info("🤖 AGENTIC WORKFLOW STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Query: {query}")
        self.logger.info(f"Has drawing: {bool(drawing_json)}")
        self.logger.info(f"Max iterations: {max_iterations}")
        
        # Initialize conversation
        messages = [
            {
                "role": "system",
                "content": self._get_agent_system_prompt()
            },
            {
                "role": "user",
                "content": self._format_user_query(query, drawing_json, drawing_updated_at)
            }
        ]
        
        # Store context for tool execution
        self.current_context = {
            "query": query,
            "drawing_json": drawing_json,
            "drawing_updated_at": drawing_updated_at,
            "regulations_cache": [],
            "reasoning_steps": []
        }
        
        # Agent loop
        for iteration in range(max_iterations):
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"🔄 ITERATION {iteration + 1}/{max_iterations}")
            self.logger.info(f"{'='*80}")
            
            try:
                # Call OpenAI with function calling
                response = self.openai_client.chat.completions.create(
                    model=self.config.llm_model,
                    messages=messages,
                    functions=self.functions,
                    function_call="auto",
                    temperature=self.config.llm_temperature
                )
                
                message = response.choices[0].message
                
                # Check if agent wants to call a function
                if message.function_call:
                    function_name = message.function_call.name
                    function_args = json.loads(message.function_call.arguments)
                    
                    self.logger.info(f"🔧 Agent calling function: {function_name}")
                    self.logger.info(f"📋 Arguments: {json.dumps(function_args, indent=2)[:200]}...")
                    
                    # Execute the function
                    function_result = self._execute_function(function_name, function_args)
                    
                    self.logger.info(f"✅ Function result: {str(function_result)[:200]}...")
                    
                    # Add to reasoning steps
                    self.current_context["reasoning_steps"].append({
                        "step": iteration + 1,
                        "action": function_name,
                        "arguments": function_args,
                        "result": function_result
                    })
                    
                    # Add function call and result to conversation
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": function_name,
                            "arguments": message.function_call.arguments
                        }
                    })
                    messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(function_result)
                    })
                    
                else:
                    # Agent has final answer
                    final_answer = message.content
                    
                    self.logger.info("=" * 80)
                    self.logger.info("✅ AGENTIC WORKFLOW COMPLETED")
                    self.logger.info("=" * 80)
                    self.logger.info(f"Total iterations: {iteration + 1}")
                    self.logger.info(f"Functions called: {len(self.current_context['reasoning_steps'])}")
                    
                    return {
                        "answer": final_answer,
                        "reasoning_steps": self.current_context["reasoning_steps"],
                        "sources": self._extract_sources(),
                        "iterations": iteration + 1
                    }
                    
            except Exception as e:
                self.logger.error(f"❌ Error in iteration {iteration + 1}: {str(e)}")
                raise
        
        # Max iterations reached
        self.logger.warning(f"⚠️ Max iterations ({max_iterations}) reached")
        return {
            "answer": "I've analyzed your question but need more iterations to provide a complete answer. Please try rephrasing or breaking down your question.",
            "reasoning_steps": self.current_context["reasoning_steps"],
            "sources": self._extract_sources(),
            "iterations": max_iterations
        }
    
    def _get_agent_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are an expert building regulations AI agent with access to tools.

Your capabilities:
- retrieve_regulations: Search for relevant building regulations
- analyze_drawing_compliance: Check if a drawing complies with regulations
- calculate_drawing_dimensions: Calculate measurements from drawings
- generate_compliant_design: Create adjusted, compliant designs
- verify_compliance: Verify if a design meets requirements

Your workflow:
1. Understand the user's question
2. Decide which tools you need to use
3. Call tools in the right order
4. Synthesize information from tool results
5. Provide a clear, comprehensive answer

Guidelines:
- Always retrieve regulations first if the question involves compliance
- Calculate dimensions when needed for analysis
- If asked to fix/adjust a design, use generate_compliant_design
- Verify your solutions with verify_compliance
- Be thorough but efficient - don't call unnecessary tools
- Provide clear explanations with your final answer

Remember: You can call multiple tools in sequence. Think step by step."""
    
    def _format_user_query(
        self,
        query: str,
        drawing_json: Optional[Dict[str, Any]],
        drawing_updated_at: Optional[str]
    ) -> str:
        """Format the user query with context."""
        parts = [f"User Question: {query}"]
        
        if drawing_json:
            timestamp_note = f" (Last updated: {drawing_updated_at})" if drawing_updated_at else ""
            parts.append(f"\nBuilding Drawing Available{timestamp_note}: Yes")
            parts.append(f"Drawing Preview: {json.dumps(drawing_json)[:500]}...")
        
        return "\n".join(parts)
    
    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a function call from the agent.
        
        Args:
            function_name: Name of the function to execute
            arguments: Function arguments
            
        Returns:
            Function result as dictionary
        """
        try:
            if function_name == "retrieve_regulations":
                return self._tool_retrieve_regulations(
                    query=arguments["query"],
                    top_k=arguments.get("top_k", 5)
                )
            
            elif function_name == "analyze_drawing_compliance":
                return self._tool_analyze_compliance(
                    regulations=arguments["regulations"]
                )
            
            elif function_name == "calculate_drawing_dimensions":
                return self._tool_calculate_dimensions(
                    dimension_type=arguments["dimension_type"]
                )
            
            elif function_name == "generate_compliant_design":
                return self._tool_generate_compliant_design(
                    original_drawing=arguments["original_drawing"],
                    violations=arguments["violations"],
                    regulations=arguments["regulations"]
                )
            
            elif function_name == "verify_compliance":
                return self._tool_verify_compliance(
                    regulations=arguments["regulations"]
                )
            
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            self.logger.error(f"Error executing {function_name}: {str(e)}")
            return {"error": str(e)}
    
    def _tool_retrieve_regulations(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Tool: Retrieve relevant regulations."""
        self.logger.info(f"🔍 Retrieving regulations for: {query}")
        
        try:
            # Process query and retrieve
            query_embedding = self.query_processor.process_query(query)
            retrieval_result = self.retrieval_engine.retrieve(query_embedding, query)
            
            if isinstance(retrieval_result, list) and retrieval_result:
                # Cache for later use
                self.current_context["regulations_cache"] = retrieval_result[:top_k]
                
                # Format results
                regulations = []
                for i, result in enumerate(retrieval_result[:top_k]):
                    regulations.append({
                        "id": i,
                        "document": result.pdf_filename,
                        "page": result.page_number,
                        "content": result.source_snippet,
                        "relevance": result.score
                    })
                
                return {
                    "success": True,
                    "count": len(regulations),
                    "regulations": regulations
                }
            else:
                return {
                    "success": False,
                    "count": 0,
                    "message": "No relevant regulations found"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_analyze_compliance(
        self,
        regulations: List[str]
    ) -> Dict[str, Any]:
        """Tool: Analyze drawing compliance."""
        self.logger.info("🔍 Analyzing drawing compliance")
        
        # Get drawing from context
        drawing_json = self.current_context.get("drawing_json")
        if not drawing_json:
            return {"success": False, "error": "No drawing available in context"}
        
        try:
            # Use LLM to analyze compliance
            prompt = f"""Analyze this building drawing against the regulations and identify violations.

REGULATIONS:
{json.dumps(regulations, indent=2)}

DRAWING:
{json.dumps(drawing_json, indent=2)}

Provide a structured analysis:
1. List all violations found
2. List compliant aspects
3. Provide specific measurements that violate rules

Format as JSON:
{{
    "violations": ["violation 1", "violation 2"],
    "compliant": ["compliant aspect 1"],
    "measurements": {{"dimension": "value"}}
}}"""
            
            response = self.openai_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": "You are a building regulations expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            result["success"] = True
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_calculate_dimensions(
        self,
        dimension_type: str
    ) -> Dict[str, Any]:
        """Tool: Calculate dimensions from drawing."""
        self.logger.info(f"📏 Calculating dimensions: {dimension_type}")
        
        # Get drawing from context
        drawing_json = self.current_context.get("drawing_json")
        if not drawing_json:
            return {"success": False, "error": "No drawing available in context"}
        
        try:
            dimensions = {}
            
            # Handle list format (drawing elements)
            if isinstance(drawing_json, list):
                # Calculate plot area
                if dimension_type in ["plot_area", "all"]:
                    plot_boundary = next((e for e in drawing_json if e.get("layer") == "Plot Boundary"), None)
                    if plot_boundary and "points" in plot_boundary:
                        points = plot_boundary["points"]
                        x_coords = [p[0] for p in points]
                        y_coords = [p[1] for p in points]
                        width = abs(max(x_coords) - min(x_coords))
                        height = abs(max(y_coords) - min(y_coords))
                        dimensions["plot_width_m"] = round(width / 1000, 2)
                        dimensions["plot_height_m"] = round(height / 1000, 2)
                        dimensions["plot_area_m2"] = round((width * height) / 1000000, 2)
                
                # Calculate extension depth
                if dimension_type in ["extension_depth", "all"]:
                    walls_elements = [e for e in drawing_json if e.get("layer") == "Walls"]
                    if len(walls_elements) >= 2:
                        main_house = walls_elements[0]
                        extension = walls_elements[1]
                        
                        if "points" in main_house and "points" in extension:
                            wall_y = max([p[1] for p in main_house["points"]])
                            ext_y = max([p[1] for p in extension["points"]])
                            depth_mm = abs(ext_y - wall_y)
                            dimensions["extension_depth_m"] = round(depth_mm / 1000, 2)
            
            # Handle dict format
            elif isinstance(drawing_json, dict) and "properties" in drawing_json:
                props = drawing_json["properties"]
                if "height" in props:
                    dimensions["building_height_m"] = props["height"]
                if "area" in props:
                    dimensions["floor_area_m2"] = props["area"]
            
            return {
                "success": True,
                "dimensions": dimensions
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_generate_compliant_design(
        self,
        original_drawing: Dict[str, Any],
        violations: List[str],
        regulations: List[str]
    ) -> Dict[str, Any]:
        """Tool: Generate compliant design."""
        self.logger.info("🔧 Generating compliant design")
        
        try:
            prompt = f"""Generate an adjusted, compliant version of this building drawing.

ORIGINAL DRAWING:
{json.dumps(original_drawing, indent=2)}

VIOLATIONS TO FIX:
{json.dumps(violations, indent=2)}

REGULATIONS TO COMPLY WITH:
{json.dumps(regulations, indent=2)}

Provide:
1. Adjusted JSON (complete, valid JSON)
2. Explanation of changes made
3. Verification that it now complies

Format as JSON:
{{
    "adjusted_drawing": {{...}},
    "changes_made": ["change 1", "change 2"],
    "compliance_verification": "explanation"
}}"""
            
            response = self.openai_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": "You are a building design expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            result["success"] = True
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_verify_compliance(
        self,
        regulations: List[str]
    ) -> Dict[str, Any]:
        """Tool: Verify compliance."""
        self.logger.info("✅ Verifying compliance")
        
        # Get drawing from context
        drawing_json = self.current_context.get("drawing_json")
        if not drawing_json:
            return {"success": False, "error": "No drawing available in context"}
        
        try:
            prompt = f"""Verify if this building drawing complies with the regulations.

DRAWING:
{json.dumps(drawing_json, indent=2)}

REGULATIONS:
{json.dumps(regulations, indent=2)}

Provide:
1. Is it compliant? (true/false)
2. Detailed explanation
3. Any remaining issues

Format as JSON:
{{
    "compliant": true/false,
    "explanation": "detailed explanation",
    "remaining_issues": ["issue 1", "issue 2"] or []
}}"""
            
            response = self.openai_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": "You are a building regulations expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            result["success"] = True
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_sources(self) -> List[Dict[str, Any]]:
        """Extract sources from cached regulations."""
        sources = []
        
        for result in self.current_context.get("regulations_cache", []):
            sources.append({
                "type": "pdf",
                "document": result.pdf_filename,
                "page": result.page_number,
                "paragraph": result.paragraph_index,
                "snippet": result.source_snippet,
                "relevance": result.score,
                "title": result.title
            })
        
        return sources
