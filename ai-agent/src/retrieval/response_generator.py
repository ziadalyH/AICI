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
        drawing_updated_at: Optional[str] = None
    ) -> Union[PDFResponse, NoAnswerResponse]:
        """
        Generate structured response with LLM-generated answer from retrieval result.
        
        Args:
            query: Original user query
            result: Retrieval result (PDFResult, List of results, or None)
            drawing_json: Optional user's building drawing JSON for context
            drawing_updated_at: Optional ISO timestamp of when drawing was last updated
            
        Returns:
            PDFResponse if result is PDFResult or List[PDFResult]
            NoAnswerResponse if result is None
        """
        self.logger.info(f"Generating response for query: {query[:50]}...")
        
        # Check if user is requesting an adjusted/compliant version
        is_adjustment_request = self.prompt_templates.detect_adjustment_request(query)
        
        if result is None:
            self.logger.info("No retrieval result")
            # Only use JSON-only response if question is about the drawing
            if drawing_json and (
                (isinstance(drawing_json, list) and len(drawing_json) > 0) or
                (isinstance(drawing_json, dict) and len(drawing_json) > 0)
            ):
                # Check if question is about drawing/building specs
                is_drawing_question = self.prompt_templates.detect_drawing_question(query)
                
                if is_drawing_question:
                    self.logger.info("No PDF results, but question is about drawing - attempting JSON-only answer")
                    return self._generate_json_only_response(query, drawing_json, drawing_updated_at)
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
                    is_drawing_question = self.prompt_templates.detect_drawing_question(query)
                    
                    if is_drawing_question:
                        self.logger.info("No PDF results, but question is about drawing - attempting JSON-only answer")
                        return self._generate_json_only_response(query, drawing_json, drawing_updated_at)
                    else:
                        self.logger.info("No PDF results and question is not about drawing, returning NoAnswerResponse")
                        return self._generate_no_answer_response()
                else:
                    self.logger.info("Empty result list and no drawing_json, returning NoAnswerResponse")
                    return self._generate_no_answer_response()
            
            # Check if it's a list of PDFResult
            if isinstance(result[0], PDFResult):
                # If user is requesting adjustments and has drawing, use adjustment flow
                if is_adjustment_request and drawing_json:
                    self.logger.info(f"🔧 Adjustment request detected - generating compliant JSON")
                    return self._generate_compliance_with_adjustment(query, result, drawing_json, drawing_updated_at)
                else:
                    self.logger.info(f"Generating PDFResponse from {len(result)} PDF results")
                    return self._generate_pdf_response_from_multiple(query, result, drawing_json, drawing_updated_at)
        
        # Handle single result (backward compatibility)
        elif isinstance(result, PDFResult):
            # If user is requesting adjustments and has drawing, use adjustment flow
            if is_adjustment_request and drawing_json:
                self.logger.info(f"🔧 Adjustment request detected - generating compliant JSON")
                return self._generate_compliance_with_adjustment(query, [result], drawing_json, drawing_updated_at)
            else:
                self.logger.info(
                    f"Generating PDFResponse for {result.pdf_filename}, "
                    f"page {result.page_number}"
                )
                return self._generate_pdf_response_from_single(query, result, drawing_json, drawing_updated_at)
        
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
        drawing_updated_at: Optional[str] = None
    ) -> PDFResponse:
        """
        Generate response from drawing JSON only (no PDF context).
        Used when no relevant PDF documents are found but drawing data is available.
        
        Args:
            query: User's question
            drawing_json: User's building drawing JSON
            drawing_updated_at: ISO timestamp of when drawing was last updated
            
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
        formatted_timestamp = self.prompt_templates.format_timestamp(drawing_updated_at) if drawing_updated_at else ""
        
        if formatted_timestamp:
            self.logger.info(f"✅ Formatted timestamp: {formatted_timestamp}")
        else:
            self.logger.warning("⚠️ No drawing_updated_at provided!")
        
        self.logger.info(f"📅 Final formatted timestamp: '{formatted_timestamp}'")
        
        # Use prompt builder to create JSON-only prompt
        prompt, system_prompt = self.prompt_builder.build_json_only_drawing(
            query=query,
            drawing_context=drawing_context,
            drawing_json=drawing_json,
            formatted_timestamp=formatted_timestamp
        )
        
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
    
    def _generate_compliance_with_adjustment(
        self,
        query: str,
        pdf_results: List[PDFResult],
        drawing_json: Dict[str, Any],
        drawing_updated_at: Optional[str] = None
    ) -> PDFResponse:
        """
        Generate response with compliance analysis and adjusted compliant JSON.
        
        Args:
            query: User's question
            pdf_results: List of PDF results with regulations
            drawing_json: User's building drawing JSON
            drawing_updated_at: ISO timestamp of when drawing was last updated
            
        Returns:
            PDFResponse with compliance analysis and adjusted JSON
        """
        self.logger.info("🔧 Generating compliance analysis with adjusted JSON")
        
        # Format drawing context
        drawing_context = self._format_drawing_context(drawing_json, drawing_updated_at)
        
        # Format timestamp for display
        formatted_timestamp = self.prompt_templates.format_timestamp(drawing_updated_at) if drawing_updated_at else ""
        
        # Use prompt builder to create compliance adjustment prompt
        prompt, system_prompt = self.prompt_builder.build_compliance_with_adjustment(
            query=query,
            pdf_results=pdf_results,
            drawing_context=drawing_context,
            drawing_json=drawing_json,
            formatted_timestamp=formatted_timestamp
        )
        
        self.logger.info(f"📝 Compliance adjustment prompt created ({len(prompt)} chars)")
        
        answer = self.llm_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2000  # Increase token limit for JSON generation
        )
        
        self.logger.info(f"✅ Compliance adjustment answer generated")
        
        # Build all_sources list with all PDF results
        all_sources = []
        for i, result in enumerate(pdf_results):
            all_sources.append({
                "type": "pdf",
                "document": result.pdf_filename,
                "page": result.page_number,
                "paragraph": result.paragraph_index,
                "snippet": result.source_snippet,
                "relevance": result.score,
                "title": result.title,
                "selected": (i == 0)  # Mark first as selected
            })
        
        # Return response with the best result's metadata
        best_result = pdf_results[0]
        
        return PDFResponse(
            answer_type="pdf",
            pdf_filename=best_result.pdf_filename,
            page_number=best_result.page_number,
            paragraph_index=best_result.paragraph_index,
            source_snippet=best_result.source_snippet,
            generated_answer=answer,
            score=best_result.score,
            document_id=best_result.document_id,
            title=f"Compliance Analysis with Adjusted Design (Drawing: {drawing_updated_at or 'Unknown'})",
            all_sources=all_sources,
            selected_source_index=0
        )
    
    def _generate_pdf_response_from_single(
        self,
        query: str,
        result: PDFResult,
        drawing_json: Optional[Dict[str, Any]] = None,
        drawing_updated_at: Optional[str] = None
    ) -> PDFResponse:
        """Generate PDFResponse from a single PDFResult."""
        generated_answer = self.generate_answer_with_llm(
            query=query,
            context=result.source_snippet,
            drawing_json=drawing_json,
            drawing_updated_at=drawing_updated_at
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
        drawing_updated_at: Optional[str] = None
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
            drawing_updated_at=drawing_updated_at
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
        drawing_updated_at: Optional[str] = None
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
        
        # Format timestamp for display
        formatted_timestamp = self.prompt_templates.format_timestamp(drawing_updated_at) if drawing_updated_at else ""
        
        if formatted_timestamp:
            self.logger.info(f"✅ Formatted timestamp: {formatted_timestamp}")
        else:
            self.logger.warning("⚠️ No drawing_updated_at provided!")
        
        # Detect question types
        is_compliance_question = self.prompt_templates.detect_compliance_question(query)
        
        # Build conditional instructions
        has_drawing = bool(drawing_json)
        
        building_spec_note = self.prompt_templates.get_building_spec_note(has_drawing)
        building_spec_instruction1 = self.prompt_templates.get_building_spec_instruction1(has_drawing)
        building_spec_instruction2 = self.prompt_templates.get_building_spec_instruction2(has_drawing)
        building_spec_instruction3 = self.prompt_templates.get_building_spec_instruction3(has_drawing, formatted_timestamp)
        compliance_instruction = self.prompt_templates.get_compliance_instruction(is_compliance_question, has_drawing, formatted_timestamp)
        
        self.logger.info(f"🔍 Building spec instruction 3: '{building_spec_instruction3}'")
        
        # Format optional sections
        drawing_section = self.prompt_templates.format_drawing_context_section(drawing_context)
        
        # Build prompt using template
        prompt = self.prompt_templates.PDF_MULTIPLE_CONTEXTS.format(
            contexts=contexts,
            drawing_context=drawing_section,
            query=query,
            num_contexts=num_results,
            building_spec_note=building_spec_note,
            building_spec_instruction1=building_spec_instruction1,
            building_spec_instruction2=building_spec_instruction2,
            building_spec_instruction3=building_spec_instruction3,
            compliance_instruction=compliance_instruction
        )
        
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
            
            # POST-PROCESSING: Ensure timestamp is included when drawing is present
            if drawing_json and formatted_timestamp and answer:
                # Check if timestamp is already mentioned
                has_timestamp = (
                    'drawing from' in answer_lower or 
                    formatted_timestamp.lower() in answer_lower or
                    'updated drawing' in answer_lower
                )
                
                if not has_timestamp:
                    # Prepend timestamp to answer
                    self.logger.info(f"⚠️ LLM did not include timestamp, prepending it...")
                    answer = f"Based on the available regulations and your drawing from {formatted_timestamp}, {answer[0].lower()}{answer[1:]}"
                    self.logger.info(f"✅ Timestamp prepended to answer")
            
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
        drawing_updated_at: Optional[str] = None
    ) -> str:
        """
        Use centralized LLM service to generate natural language answer from context.
        
        Args:
            query: User's question
            context: Retrieved context snippet
            drawing_json: Optional user's building drawing JSON
            drawing_updated_at: ISO timestamp of when drawing was last updated
            
        Returns:
            Natural language answer generated by LLM
        """
        self.logger.debug(f"Generating LLM answer for query: {query[:50]}...")
        
        # Format drawing JSON context if provided
        drawing_context = ""
        if drawing_json:
            drawing_context = self._format_drawing_context(drawing_json, drawing_updated_at)
            self.logger.info(f"✅ Drawing context included ({len(drawing_context)} chars)")
        
        # Format timestamp for display
        formatted_timestamp = self.prompt_templates.format_timestamp(drawing_updated_at) if drawing_updated_at else ""
        
        # Use prompt builder to create single context prompt
        prompt, system_prompt = self.prompt_builder.build_pdf_single_context(
            query=query,
            context=context,
            drawing_context=drawing_context,
            formatted_timestamp=formatted_timestamp
        )
        
        answer = self.llm_service.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # POST-PROCESSING: Ensure timestamp is included when drawing is present
        if drawing_json and formatted_timestamp and answer:
            # Check if timestamp is already mentioned
            answer_lower = answer.lower()
            has_timestamp = (
                'drawing from' in answer_lower or 
                formatted_timestamp.lower() in answer_lower or
                'updated drawing' in answer_lower
            )
            
            if not has_timestamp:
                # Prepend timestamp to answer
                self.logger.info(f"⚠️ LLM did not include timestamp, prepending it...")
                answer = f"Based on the available regulations and your drawing from {formatted_timestamp}, {answer[0].lower()}{answer[1:]}"
        
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
        self.logger.info("🎨 _format_drawing_context called")
        self.logger.info(f"   drawing_json type: {type(drawing_json)}")
        self.logger.info(f"   drawing_json is None: {drawing_json is None}")
        self.logger.info(f"   drawing_json is empty: {not drawing_json if drawing_json else 'N/A'}")
        
        if not drawing_json:
            self.logger.warning("⚠️ drawing_json is empty or None, returning empty string")
            return ""
        
        # Log the raw drawing JSON for debugging
        self.logger.info("=" * 80)
        self.logger.info("📐 DRAWING JSON RECEIVED:")
        self.logger.info(f"Type: {type(drawing_json)}")
        self.logger.info(f"Length: {len(drawing_json) if isinstance(drawing_json, list) else 'N/A'}")
        self.logger.info(f"Content: {str(drawing_json)[:500]}...")
        self.logger.info("=" * 80)
        
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
            
            # Calculate extension depth - handle multiple approaches
            self.logger.info("🔍 Starting extension depth calculation...")
            
            # Approach 1: Look for explicit "Extension" layer
            extension = next((e for e in drawing_json if e.get("layer") == "Extension"), None)
            self.logger.info(f"   Extension layer found: {extension is not None}")
            
            # Approach 2: If no Extension layer, look for multiple "Walls" layers
            # The second Walls layer is likely the extension
            walls_elements = [e for e in drawing_json if e.get("layer") == "Walls"]
            self.logger.info(f"   Number of Walls layers: {len(walls_elements)}")
            
            if extension and "points" in extension:
                # Found explicit Extension layer
                self.logger.info("   Using explicit Extension layer")
                if walls_elements and "points" in walls_elements[0]:
                    # Get rear wall Y coordinate (maximum Y from first Walls element)
                    wall_points = walls_elements[0]["points"]
                    wall_y_coords = [p[1] for p in wall_points]
                    rear_wall_y = max(wall_y_coords)
                    
                    # Get extension furthest point Y coordinate
                    ext_points = extension["points"]
                    ext_y_coords = [p[1] for p in ext_points]
                    extension_furthest_y = max(ext_y_coords)
                    
                    # Calculate extension depth
                    extension_depth_mm = abs(extension_furthest_y - rear_wall_y)
                    extension_depth_m = round(extension_depth_mm / 1000, 2)
                    
                    context_parts.append(f"- Extension Depth: {extension_depth_m}m (from rear wall)")
                    self.logger.info(f"✅ Extension depth calculated from 'Extension' layer: {extension_depth_m}m")
            
            elif len(walls_elements) >= 2:
                # Multiple Walls layers - assume first is main house, second is extension
                self.logger.info("   Using second Walls layer as extension")
                main_house = walls_elements[0]
                extension_element = walls_elements[1]
                
                self.logger.info(f"   Main house has points: {'points' in main_house}")
                self.logger.info(f"   Extension has points: {'points' in extension_element}")
                
                if "points" in main_house and "points" in extension_element:
                    # Get rear wall Y coordinate (maximum Y from main house)
                    wall_points = main_house["points"]
                    wall_y_coords = [p[1] for p in wall_points]
                    rear_wall_y = max(wall_y_coords)
                    
                    # Get extension furthest point Y coordinate
                    ext_points = extension_element["points"]
                    ext_y_coords = [p[1] for p in ext_points]
                    extension_furthest_y = max(ext_y_coords)
                    
                    # Calculate extension depth
                    extension_depth_mm = abs(extension_furthest_y - rear_wall_y)
                    extension_depth_m = round(extension_depth_mm / 1000, 2)
                    
                    context_parts.append(f"- Extension Depth: {extension_depth_m}m (from rear wall)")
                    self.logger.info(f"✅ Extension depth calculated from second 'Walls' layer: {extension_depth_m}m")
                    self.logger.info(f"   Main house rear wall Y: {rear_wall_y}")
                    self.logger.info(f"   Extension furthest Y: {extension_furthest_y}")
                else:
                    self.logger.warning(f"⚠️ Walls elements missing 'points' field")
            
            else:
                self.logger.warning("⚠️ Could not calculate extension depth - no Extension layer or multiple Walls layers found")
            
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
