"""Response generator module for formatting retrieval results and generating LLM answers.

This module uses centralized LLM inference service for all LLM responses.
"""

import logging
from typing import Union, List, Optional, TYPE_CHECKING, Dict, Any
from pathlib import Path

from ..models import (
    PDFResult,
    PDFResponse,
    NoAnswerResponse
)
from config.config import Config
from config.prompt_templates import PromptBuilder, PromptTemplates

if TYPE_CHECKING:
    from ..llm_inference import LLMInferenceService


class ResponseGenerator:
    """
    Format retrieval results into structured responses and generate natural language answers.
    
    Uses centralized LLM inference service for all LLM operations.
    
    This class handles:
    - Generating natural language answers using centralized LLM service
    - Formatting video-based responses with timestamps and citations
    - Formatting PDF-based responses with page/paragraph citations
    - Handling no-answer scenarios
    - Converting responses to human-readable display format
    """
    
    def __init__(
        self,
        config: Config,
        logger: logging.Logger,
        llm_service: 'LLMInferenceService',
        knowledge_summary_path: Optional[str] = None
    ):
        """
        Initialize the ResponseGenerator.
        
        Args:
            config: Configuration object containing LLM settings
            logger: Logger instance for logging operations
            llm_service: Centralized LLM inference service
            knowledge_summary_path: Optional path to knowledge summary file
        """
        self.config = config
        self.logger = logger
        self.llm_service = llm_service
        self.knowledge_summary_path = Path(knowledge_summary_path) if knowledge_summary_path else Path("data/knowledge_summary.json")
        
        # Initialize prompt builder
        self.prompt_builder = PromptBuilder()
        self.prompt_templates = PromptTemplates()
        
        self.logger.info("Initialized ResponseGenerator with centralized LLM service")
    
    def generate_response(
        self,
        query: str,
        result: Union[PDFResult, List[PDFResult], None],
        drawing_json: Optional[Dict[str, Any]] = None,
        drawing_updated_at: Optional[str] = None,
        conversation_history: Optional[str] = None
    ) -> Union[PDFResponse, NoAnswerResponse]:
        """
        Generate structured response with LLM-generated answer from retrieval result.
        
        Args:
            query: Original user query
            result: Retrieval result (PDFResult, List of results, or None)
            drawing_json: Optional user's building drawing JSON for context
            drawing_updated_at: Optional ISO timestamp of when drawing was last updated
            conversation_history: Optional formatted conversation history
            
        Returns:
            PDFResponse if result is PDFResult or List[PDFResult]
            NoAnswerResponse if result is None
        """
        self.logger.info(f"Generating response for query: {query[:50]}...")
        
        if result is None:
            self.logger.info("No retrieval result")
            # Only use JSON-only response if question is about the drawing
            if drawing_json and (
                (isinstance(drawing_json, list) and len(drawing_json) > 0) or
                (isinstance(drawing_json, dict) and len(drawing_json) > 0)
            ):
                # Check if question is about drawing/building specs
                drawing_keywords = ['plot', 'area', 'dimension', 'size', 'building', 'wall', 'door', 'window', 'floor', 'height', 'width', 'length', 'room', 'space', 'layout']
                is_drawing_question = any(keyword in query.lower() for keyword in drawing_keywords)
                
                if is_drawing_question:
                    self.logger.info("No PDF results, but question is about drawing - attempting JSON-only answer")
                    return self._generate_json_only_response(query, drawing_json, drawing_updated_at, conversation_history)
                else:
                    self.logger.info("No PDF results and question is not about drawing, returning NoAnswerResponse")
                    return self._generate_no_answer_response()
            else:
                self.logger.info("No retrieval result and no drawing_json, returning NoAnswerResponse")
                return self._generate_no_answer_response()
        
        # Handle list of results (LLM-based selection)
        elif isinstance(result, list):
            if not result:
                self.logger.info("Empty result list")
                # Only use JSON-only response if question is about the drawing
                if drawing_json and (
                    (isinstance(drawing_json, list) and len(drawing_json) > 0) or
                    (isinstance(drawing_json, dict) and len(drawing_json) > 0)
                ):
                    # Check if question is about drawing/building specs
                    drawing_keywords = ['plot', 'area', 'dimension', 'size', 'building', 'wall', 'door', 'window', 'floor', 'height', 'width', 'length', 'room', 'space', 'layout']
                    is_drawing_question = any(keyword in query.lower() for keyword in drawing_keywords)
                    
                    if is_drawing_question:
                        self.logger.info("No PDF results, but question is about drawing - attempting JSON-only answer")
                        return self._generate_json_only_response(query, drawing_json, drawing_updated_at, conversation_history)
                    else:
                        self.logger.info("No PDF results and question is not about drawing, returning NoAnswerResponse")
                        return self._generate_no_answer_response()
                else:
                    self.logger.info("Empty result list and no drawing_json, returning NoAnswerResponse")
                    return self._generate_no_answer_response()
            
            # Check if it's a list of PDFResult
            if isinstance(result[0], PDFResult):
                self.logger.info(f"Generating PDFResponse from {len(result)} PDF results")
                return self._generate_pdf_response_from_multiple(query, result, drawing_json, drawing_updated_at, conversation_history)
        
        # Handle single result (backward compatibility)
        elif isinstance(result, PDFResult):
            self.logger.info(
                f"Generating PDFResponse for {result.pdf_filename}, "
                f"page {result.page_number}"
            )
            return self._generate_pdf_response_from_single(query, result, drawing_json, drawing_updated_at, conversation_history)
        
        else:
            self.logger.error(f"Unexpected result type: {type(result)}")
            return self._generate_no_answer_response(
                message="An error occurred while generating the response."
            )
    
    def _generate_no_answer_response(self, message: str = "No relevant answer found in the knowledge base.") -> NoAnswerResponse:
        """
        Generate NoAnswerResponse with knowledge summary.
        
        Args:
            message: Custom message for the no-answer response
            
        Returns:
            NoAnswerResponse with knowledge summary included
        """
        knowledge_summary = None
        
        # Try to load knowledge summary
        try:
            if self.knowledge_summary_path.exists():
                import json
                with open(self.knowledge_summary_path, 'r') as f:
                    knowledge_summary = json.load(f)
                self.logger.info("Loaded knowledge summary for no-answer response")
            else:
                self.logger.warning(f"Knowledge summary file not found: {self.knowledge_summary_path}")
        except Exception as e:
            self.logger.error(f"Failed to load knowledge summary: {e}")
        
        return NoAnswerResponse(
            message=message,
            knowledge_summary=knowledge_summary
        )
    
    def _generate_json_only_response(
        self,
        query: str,
        drawing_json: Dict[str, Any],
        drawing_updated_at: Optional[str] = None,
        conversation_history: Optional[str] = None
    ) -> PDFResponse:
        """
        Generate response from drawing JSON only (no PDF context).
        Used when no relevant PDF documents are found but drawing data is available.
        
        Args:
            query: User's question
            drawing_json: User's building drawing JSON
            drawing_updated_at: ISO timestamp of when drawing was last updated
            conversation_history: Optional formatted conversation history
            
        Returns:
            PDFResponse with answer based solely on drawing JSON
        """
        self.logger.info("Generating JSON-only response (no PDF context)")
        
        # Log the timestamp value
        self.logger.info(f"📅 Drawing timestamp received: {drawing_updated_at}")
        self.logger.info(f"📅 Drawing timestamp type: {type(drawing_updated_at)}")
        
        # Format drawing context
        drawing_context = self._format_drawing_context(drawing_json, drawing_updated_at)
        
        # Format timestamp for display (convert ISO to DD/MM/YYYY, HH:MM:SS)
        formatted_timestamp = ""
        if drawing_updated_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(drawing_updated_at.replace('Z', '+00:00'))
                formatted_timestamp = dt.strftime("%d/%m/%Y, %H:%M:%S")
                self.logger.info(f"✅ Formatted timestamp: {formatted_timestamp}")
            except Exception as e:
                self.logger.error(f"❌ Failed to format timestamp: {e}")
                formatted_timestamp = drawing_updated_at
        else:
            self.logger.warning("⚠️ No drawing_updated_at provided!")
        
        self.logger.info(f"📅 Final formatted timestamp: '{formatted_timestamp}'")
        
        # Build prompt for JSON-only reasoning
        system_prompt = "You are a helpful assistant that analyzes building drawings and answers questions about them. Be precise and factual. Always mention the drawing version date in your response."
        
        # Add conversation history if available
        history_context = ""
        if conversation_history:
            history_context = f"\n\n{conversation_history}\n"
            self.logger.info("📜 Including conversation history in JSON-only response")
        
        prompt = f"""You are analyzing a building drawing. Answer the user's question based ONLY on the drawing data provided below.
{history_context}

User's Building Drawing (Last updated: {formatted_timestamp}):
{drawing_context}

Raw Drawing Data (JSON):
{str(drawing_json)[:2000]}  # Limit to prevent token overflow

Question: {query}

Instructions:
- Answer based ONLY on the drawing data provided
- CRITICAL: You MUST start your answer with: "Based on the updated drawing from {formatted_timestamp}, ..."
- Be specific and cite exact values from the drawing
- If the drawing data doesn't contain the information needed, say so clearly
- Do NOT make assumptions or reference external regulations
- If this is a follow-up question, use the conversation history for context

Answer:"""
        
        self.logger.info(f"📝 JSON-only prompt created ({len(prompt)} chars)")
        
        answer = self.llm_service.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        self.logger.info(f"✅ JSON-only answer generated")
        
        # Return as PDFResponse with special markers
        return PDFResponse(
            answer_type="pdf",  # Keep as "pdf" for compatibility
            pdf_filename="[Drawing Analysis]",
            page_number=0,
            paragraph_index=0,
            source_snippet=drawing_context,
            generated_answer=answer,
            score=1.0,  # Perfect score since we're using the exact data
            document_id="json_only",
            title=f"Building Drawing Analysis (Updated: {drawing_updated_at or 'Unknown'})"
        )
    
    def _generate_pdf_response_from_single(
        self,
        query: str,
        result: PDFResult,
        drawing_json: Optional[Dict[str, Any]] = None,
        drawing_updated_at: Optional[str] = None,
        conversation_history: Optional[str] = None
    ) -> PDFResponse:
        """Generate PDFResponse from a single PDFResult."""
        generated_answer = self.generate_answer_with_llm(
            query=query,
            context=result.source_snippet,
            drawing_json=drawing_json,
            drawing_updated_at=drawing_updated_at,
            conversation_history=conversation_history
        )
        
        return PDFResponse(
            answer_type="pdf",
            pdf_filename=result.pdf_filename,
            page_number=result.page_number,
            paragraph_index=result.paragraph_index,
            source_snippet=result.source_snippet,
            generated_answer=generated_answer,
            score=result.score,
            document_id=result.document_id,
            title=result.title  # Pass through title
        )
    
    def _generate_pdf_response_from_multiple(
        self,
        query: str,
        results: List[PDFResult],
        drawing_json: Optional[Dict[str, Any]] = None,
        drawing_updated_at: Optional[str] = None,
        conversation_history: Optional[str] = None
    ) -> Union[PDFResponse, NoAnswerResponse]:
        """
        Generate PDFResponse from multiple PDFResults.
        Let LLM choose the best context and generate answer.
        Returns NoAnswerResponse WITH knowledge summary if LLM refuses (final fallback).
        """
        # Log the results being processed
        self.logger.info("="*80)
        self.logger.info(f"GENERATING ANSWER FROM {len(results)} PDF RESULTS:")
        self.logger.info("="*80)
        for i, result in enumerate(results, 1):
            self.logger.info(f"\nResult {i}:")
            self.logger.info(f"  PDF: {result.pdf_filename}")
            self.logger.info(f"  Page: {result.page_number}, Paragraph: {result.paragraph_index}")
            self.logger.info(f"  Title: {result.title or 'No title'}")
            self.logger.info(f"  Score: {result.score:.4f}")
            self.logger.info(f"  Snippet length: {len(result.source_snippet)} chars")
            self.logger.info(f"  Snippet preview: {result.source_snippet[:300]}...")
        self.logger.info("="*80)
        
        # Combine contexts with metadata
        combined_context = self._combine_contexts_for_llm(
            query=query,
            results=results,
            result_type="pdf"
        )
        
        self.logger.info(f"📊 Combined {len(results)} contexts ({len(combined_context)} chars)")
        
        # Generate answer with LLM (it will pick the best context)
        generated_answer, best_idx = self.generate_answer_with_llm_selection(
            query=query,
            contexts=combined_context,
            num_results=len(results),
            drawing_json=drawing_json,
            drawing_updated_at=drawing_updated_at,
            conversation_history=conversation_history
        )
        
        # Check if LLM refused to answer
        if generated_answer is None:
            self.logger.info("LLM refused to answer from PDFs (final fallback), returning NoAnswerResponse WITH knowledge summary")
            # This is the final fallback - include knowledge summary
            return self._generate_no_answer_response(
                message="I couldn't find relevant information to answer your question. Please try rephrasing or asking a different question."
            )
        
        self.logger.info(f"✅ LLM selected context {best_idx + 1}")
        
        # Build all_sources list with all results
        all_sources = []
        for i, result in enumerate(results):
            all_sources.append({
                "type": "pdf",
                "document": result.pdf_filename,
                "page": result.page_number,
                "paragraph": result.paragraph_index,
                "snippet": result.source_snippet,
                "relevance": result.score,
                "title": result.title,
                "selected": (i == best_idx)  # Mark which one was selected
            })
        
        self.logger.info(f"📚 Returning {len(all_sources)} sources (selected: #{best_idx + 1})")
        
        # Return response with the best result's metadata AND all sources
        best_result = results[best_idx]
        
        return PDFResponse(
            answer_type="pdf",
            pdf_filename=best_result.pdf_filename,
            page_number=best_result.page_number,
            paragraph_index=best_result.paragraph_index,
            source_snippet=best_result.source_snippet,
            generated_answer=generated_answer,
            score=best_result.score,
            document_id=best_result.document_id,
            title=best_result.title,
            all_sources=all_sources,  # Include all sources
            selected_source_index=best_idx  # Which one was selected
        )
    
    def _combine_contexts_for_llm(
        self,
        query: str,
        results: List[PDFResult],
        result_type: str = "pdf"
    ) -> str:
        """Combine multiple PDF contexts into a single prompt for LLM."""
        contexts = []
        
        for i, result in enumerate(results):
            context_text = result.source_snippet
            contexts.append(f"[Context {i+1}]\n{context_text}\n")
        
        return "\n".join(contexts)
    
    def generate_answer_with_llm_selection(
        self,
        query: str,
        contexts: str,
        num_results: int,
        drawing_json: Optional[Dict[str, Any]] = None,
        drawing_updated_at: Optional[str] = None,
        conversation_history: Optional[str] = None
    ) -> tuple[Optional[str], int]:
        """
        Use centralized LLM service to select best context and generate answer.
        
        Returns:
            Tuple of (generated_answer, best_context_index) or (None, index) if refused
        """
        self.logger.debug(f"Generating LLM answer with selection from {num_results} contexts")
        
        # Format drawing JSON context if provided
        drawing_context = ""
        if drawing_json:
            drawing_context = self._format_drawing_context(drawing_json, drawing_updated_at)
            self.logger.info(f"✅ Drawing context included ({len(drawing_context)} chars)")
            self.logger.info(f"📅 Drawing timestamp value: {drawing_updated_at}")
            self.logger.info(f"📅 Drawing timestamp type: {type(drawing_updated_at)}")
        
        # Add conversation history if available
        history_context = ""
        if conversation_history:
            history_context = f"\n\n{conversation_history}\n"
            self.logger.info(f"📜 Conversation history included ({len(conversation_history)} chars)")
        
        # Build prompt template with conditional parts
        building_spec_note = " and the user's building specifications" if drawing_json else ""
        building_spec_instruction1 = "- When relevant, reference specific values from the building specifications (height, floors, area, etc.)\n" if drawing_json else ""
        building_spec_instruction2 = "- If the regulations mention limits or requirements, compare them to the building specifications\n" if drawing_json else ""
        
        # Format timestamp for display (convert ISO to DD/MM/YYYY, HH:MM:SS)
        formatted_timestamp = ""
        if drawing_updated_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(drawing_updated_at.replace('Z', '+00:00'))
                formatted_timestamp = dt.strftime("%d/%m/%Y, %H:%M:%S")
                self.logger.info(f"✅ Formatted timestamp: {formatted_timestamp}")
            except Exception as e:
                self.logger.error(f"❌ Failed to format timestamp: {e}")
                formatted_timestamp = drawing_updated_at
        else:
            self.logger.warning("⚠️ No drawing_updated_at provided!")
        
        building_spec_instruction3 = f"- IMPORTANT: ONLY if your answer uses information from the building drawing, start with: 'Based on the updated drawing from {formatted_timestamp}, ...'\n- If your answer is based solely on the PDF documents, do NOT mention the drawing timestamp\n" if drawing_json and formatted_timestamp else ""
        history_instruction = "- If this is a follow-up question, use the conversation history for context\n" if conversation_history else ""
        
        self.logger.info(f"🔍 Building spec instruction 3: '{building_spec_instruction3}'")
        
        # Detect compliance questions and adjust instructions
        is_compliance_question = any(word in query.lower() for word in ['comply', 'compliance', 'permitted development', 'allowed', 'legal'])
        
        compliance_instruction = ""
        if is_compliance_question and drawing_json:
            compliance_instruction = """
SPECIAL INSTRUCTIONS FOR COMPLIANCE QUESTIONS:
- Even if contexts are fragmented, synthesize the information available
- List specific rules mentioned in the contexts
- Compare building specs against those specific rules
- If you can check ANY rules (even partially), provide that information
- Format: "Based on the available regulations and your drawing from {formatted_timestamp}:
  ✅ [Rules that appear to be met]
  ⚠️ [Rules that need checking or may not be met]
  ℹ️ [Additional rules that apply but need more information]"
- Do NOT refuse to answer if you have ANY relevant rule information
"""
        
        prompt = f"""You are given multiple context snippets from building regulations documents. Your task is to:
1. Identify which context (if any) best answers the question
2. Generate a concise answer based on that context{building_spec_note}

IMPORTANT: If none of the contexts contain information to answer the question, respond with "I cannot answer this question based on the provided context."
{compliance_instruction}
{history_context}
{contexts}
{drawing_context}

Question: {query}

Instructions:
- First, identify the best context number (1-{num_results}) that answers the question
- Then provide your answer based on that context{building_spec_note}
{building_spec_instruction1}{building_spec_instruction2}{building_spec_instruction3}{history_instruction}- Format: Start with "[Using Context X]" then provide the answer

Answer:"""
        
        try:
            answer = self.llm_service.generate(prompt)
            
            # Parse which context was used
            best_idx = 0  # Default to first
            if "[Using Context" in answer:
                try:
                    import re
                    match = re.search(r'\[Using Context (\d+)\]', answer)
                    if match:
                        best_idx = int(match.group(1)) - 1  # Convert to 0-indexed
                        # Remove the context indicator from the answer
                        answer = re.sub(r'\[Using Context \d+\]\s*', '', answer).strip()
                except:
                    pass
            
            # Check if LLM refused to answer
            refusal_phrases = [
                "i cannot answer",
                "i can't answer",
                "cannot answer this question",
                "can't answer this question",
                "not enough information",
                "insufficient information",
                "no information",
                "don't have enough",
                "doesn't contain"
            ]
            
            answer_lower = answer.lower()
            if any(phrase in answer_lower for phrase in refusal_phrases):
                self.logger.info("LLM refused to answer - returning None to trigger NoAnswerResponse")
                return None, best_idx
            
            self.logger.info(f"✅ LLM answer generated")
            
            return answer, best_idx
            
        except Exception as e:
            self.logger.error(f"Failed to generate LLM answer: {str(e)}")
            # Return a fallback message
            return "I found relevant information but couldn't generate a detailed answer. Please refer to the source snippet.", 0
    
    def generate_answer_with_llm(
        self,
        query: str,
        context: str,
        drawing_json: Optional[Dict[str, Any]] = None,
        drawing_updated_at: Optional[str] = None,
        conversation_history: Optional[str] = None
    ) -> str:
        """
        Use centralized LLM service to generate natural language answer from context.
        
        Args:
            query: User's question
            context: Retrieved context snippet
            drawing_json: Optional user's building drawing JSON
            drawing_updated_at: ISO timestamp of when drawing was last updated
            conversation_history: Optional formatted conversation history
            
        Returns:
            Natural language answer generated by LLM
        """
        self.logger.debug(f"Generating LLM answer for query: {query[:50]}...")
        
        # Format drawing JSON context if provided
        drawing_context = ""
        if drawing_json:
            drawing_context = self._format_drawing_context(drawing_json, drawing_updated_at)
            self.logger.info(f"✅ Drawing context included ({len(drawing_context)} chars)")
        
        # Add conversation history if available
        history_context = ""
        if conversation_history:
            history_context = f"\n\n{conversation_history}\n"
            self.logger.info(f"📜 Conversation history included ({len(conversation_history)} chars)")
        
        # Build enhanced prompt with drawing context
        system_prompt = "You are a helpful assistant that answers questions about building regulations. Be concise and accurate. When referencing drawing data, always mention the drawing version date."
        
        # Format timestamp for display (convert ISO to DD/MM/YYYY, HH:MM:SS)
        formatted_timestamp = ""
        if drawing_updated_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(drawing_updated_at.replace('Z', '+00:00'))
                formatted_timestamp = dt.strftime("%d/%m/%Y, %H:%M:%S")
            except:
                formatted_timestamp = drawing_updated_at
        
        building_spec_note = " and the building specifications" if drawing_json else ""
        building_spec_instruction1 = "- When relevant, reference specific values from the building specifications (height, floors, area, etc.)\n" if drawing_json else ""
        building_spec_instruction2 = "- If the regulations mention limits or requirements, compare them to the building specifications\n" if drawing_json else ""
        building_spec_instruction3 = f"- IMPORTANT: ONLY if your answer uses information from the building drawing, start with: 'Based on the updated drawing from {formatted_timestamp}, ...'\n- If your answer is based solely on the PDF documents, do NOT mention the drawing timestamp\n" if drawing_json and drawing_updated_at else ""
        history_instruction = "- If this is a follow-up question, use the conversation history for context\n" if conversation_history else ""
        
        prompt = f"""Based on the following context from building regulations, answer the user's question concisely and accurately.

IMPORTANT: If the context does not contain information to answer the question, respond with "I cannot answer this question based on the provided context."
{history_context}
Context from regulations: {context}
{drawing_context}

Question: {query}

Instructions:
- Provide a clear, concise answer based on the regulations context{building_spec_note}
{building_spec_instruction1}{building_spec_instruction2}{building_spec_instruction3}{history_instruction}- Be specific and cite relevant details from the regulations

Answer:"""
        
        answer = self.llm_service.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        return answer
    
    def _format_drawing_context(self, drawing_json: Dict[str, Any], drawing_updated_at: Optional[str] = None) -> str:
        """
        Format drawing JSON into a readable context string for the LLM.
        
        Args:
            drawing_json: User's building drawing JSON (can be dict or list)
            drawing_updated_at: ISO timestamp of when drawing was last updated
            
        Returns:
            Formatted string describing the building specifications
        """
        if not drawing_json:
            return ""
        
        timestamp_note = f" (Last updated: {drawing_updated_at})" if drawing_updated_at else ""
        context_parts = [f"\n\nUser's Building Drawing{timestamp_note}:"]
        
        # Handle array format (list of drawing elements)
        if isinstance(drawing_json, list):
            # Analyze the drawing elements
            layers = {}
            for element in drawing_json:
                layer = element.get("layer", "Unknown")
                if layer not in layers:
                    layers[layer] = []
                layers[layer].append(element)
            
            context_parts.append(f"- Drawing contains {len(drawing_json)} elements")
            context_parts.append("- Layers present:")
            
            for layer, elements in layers.items():
                context_parts.append(f"  * {layer}: {len(elements)} element(s)")
            
            # Calculate plot dimensions if plot boundary exists
            plot_boundary = next((e for e in drawing_json if e.get("layer") == "Plot Boundary"), None)
            if plot_boundary and "points" in plot_boundary:
                points = plot_boundary["points"]
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                width = abs(max(x_coords) - min(x_coords))
                height = abs(max(y_coords) - min(y_coords))
                
                # Convert to meters (assuming drawing units are in mm or similar)
                width_m = round(width / 1000, 2)
                height_m = round(height / 1000, 2)
                area_m2 = round((width * height) / 1000000, 2)
                
                context_parts.append(f"- Plot Dimensions: {width_m}m x {height_m}m")
                context_parts.append(f"- Plot Area: {area_m2}m²")
            
            # Check proximity to highway
            has_highway = any(e.get("layer") == "Highway" for e in drawing_json)
            if has_highway:
                context_parts.append("- Building is near a highway")
            
            return "\n".join(context_parts)
        
        # Handle dictionary format (structured properties)
        else:
            # Extract building type/ID
            if "id" in drawing_json:
                context_parts.append(f"- Building ID: {drawing_json['id']}")
            if "type" in drawing_json:
                context_parts.append(f"- Building Type: {drawing_json['type']}")
            
            # Extract properties
            if "properties" in drawing_json:
                props = drawing_json["properties"]
                context_parts.append("- Properties:")
                
                if "height" in props:
                    context_parts.append(f"  * Height: {props['height']}m")
                if "floors" in props:
                    context_parts.append(f"  * Number of Floors: {props['floors']}")
                if "area" in props:
                    context_parts.append(f"  * Floor Area: {props['area']}m²")
                if "zone" in props:
                    context_parts.append(f"  * Zone: {props['zone']}")
                if "use" in props:
                    context_parts.append(f"  * Use: {props['use']}")
                
                # Include any other properties
                for key, value in props.items():
                    if key not in ["height", "floors", "area", "zone", "use"]:
                        context_parts.append(f"  * {key.replace('_', ' ').title()}: {value}")
            
            # Extract geometry if present
            if "geometry" in drawing_json:
                geom = drawing_json["geometry"]
                if "coordinates" in geom:
                    context_parts.append(f"- Geometry: {geom.get('type', 'Unknown')} with coordinates provided")
            
            return "\n".join(context_parts)
    
    def format_for_display(
        self,
        response: Union[PDFResponse, NoAnswerResponse]
    ) -> str:
        """
        Format response for human-readable display.
        
        Args:
            response: Response object to format
            
        Returns:
            Human-readable string representation
        """
        self.logger.debug(f"Formatting response for display: {response.answer_type}")
        
        if isinstance(response, PDFResponse):
            # Format PDF response with page/paragraph citation
            title_line = f"Section: {response.title}\n" if response.title else ""
            formatted = f"""Answer Type: PDF
Document: {response.pdf_filename}
{title_line}Page: {response.page_number}
Paragraph: {response.paragraph_index}

Answer:
{response.generated_answer}

Source Text:
"{response.source_snippet}"
"""
            
        elif isinstance(response, NoAnswerResponse):
            # Format no-answer response
            formatted = f"""Answer Type: No Answer
Message: {response.message}
"""
            
        else:
            formatted = f"Unknown response type: {type(response)}"
        
        self.logger.debug("Response formatted for display")
        return formatted
