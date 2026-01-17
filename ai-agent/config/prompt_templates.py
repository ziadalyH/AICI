"""
Prompt templates for LLM interactions.

This module centralizes all prompt templates used throughout the system,
making them easy to maintain, version, and test.

Best practices:
- Use f-string style placeholders: {variable_name}
- Keep prompts clear and concise
- Document expected variables for each template
- Version prompts when making significant changes
"""

from typing import Dict, Any


class PromptTemplates:
    """Centralized prompt templates for the RAG system."""
    
    # ============================================================================
    # SYSTEM PROMPTS
    # ============================================================================
    
    SYSTEM_GENERAL = """You are a helpful assistant that answers questions about building regulations. Be concise and accurate. When referencing drawing data, always mention the drawing version date."""
    
    SYSTEM_DRAWING_ANALYSIS = """You are a helpful assistant that analyzes building drawings and answers questions about them. Be precise and factual. Always mention the drawing version date in your response."""
    
    # ============================================================================
    # PDF + DRAWING RESPONSE (Multiple Contexts)
    # ============================================================================
    
    PDF_MULTIPLE_CONTEXTS = """Based on the following contexts from building regulations, answer the user's question.
{compliance_instruction}
{contexts}

{drawing_context}

Question: {query}

Instructions:
- First, identify the best context number (1-{num_contexts}) that answers the question
- Then provide your answer based on that context{building_spec_note}
{building_spec_instruction1}{building_spec_instruction2}{building_spec_instruction3}- Format: Start with "[Using Context X]" then provide the answer

Answer:"""

    # ============================================================================
    # PDF + DRAWING RESPONSE (Single Context)
    # ============================================================================
    
    PDF_SINGLE_CONTEXT = """Based on the following context from building regulations, answer the user's question concisely and accurately.

IMPORTANT: If the context does not contain information to answer the question, respond with "I cannot answer this question based on the provided context."
Context from regulations: {context}
{drawing_context}

Question: {query}

Instructions:
- Provide a clear, concise answer based on the regulations context{building_spec_note}
{building_spec_instruction1}{building_spec_instruction2}{building_spec_instruction3}- Be specific and cite relevant details from the regulations

Answer:"""

    # ============================================================================
    # JSON-ONLY RESPONSE (Drawing Analysis)
    # ============================================================================
    
    JSON_ONLY_DRAWING = """You are analyzing a building drawing. Answer the user's question based ONLY on the drawing data provided below.

User's Building Drawing (Last updated: {formatted_timestamp}):
{drawing_context}

Raw Drawing Data (JSON):
{drawing_json_preview}

Question: {query}

Instructions:
- Answer based ONLY on the drawing data provided
- CRITICAL: You MUST start your answer with: "Based on the updated drawing from {formatted_timestamp}, ..."
- Be specific and cite exact values from the drawing
- If the drawing data doesn't contain the information needed, say so clearly
- Do NOT make assumptions or reference external regulations

Answer:"""

    # ============================================================================
    # CONDITIONAL INSTRUCTIONS (Building Specifications)
    # ============================================================================
    
    @staticmethod
    def get_building_spec_note(has_drawing: bool) -> str:
        """Get the building specification note for prompts."""
        return " and the user's building specifications" if has_drawing else ""
    
    @staticmethod
    def get_building_spec_instruction1(has_drawing: bool) -> str:
        """Get instruction about referencing building specifications."""
        return "- When relevant, reference specific values from the building specifications (height, floors, area, etc.)\n" if has_drawing else ""
    
    @staticmethod
    def get_building_spec_instruction2(has_drawing: bool) -> str:
        """Get instruction about comparing regulations to building specs."""
        return "- If the regulations mention limits or requirements, compare them to the building specifications\n" if has_drawing else ""
    
    @staticmethod
    def get_building_spec_instruction3(has_drawing: bool, formatted_timestamp: str) -> str:
        """Get instruction about mentioning drawing timestamp."""
        if has_drawing and formatted_timestamp:
            return (
                f"- IMPORTANT: ONLY if your answer uses information from the building drawing, "
                f"start with: 'Based on the updated drawing from {formatted_timestamp}, ...'\n"
                f"- If your answer is based solely on the PDF documents, do NOT mention the drawing timestamp\n"
            )
        return ""
    

    
    # ============================================================================
    # COMPLIANCE QUESTION INSTRUCTIONS
    # ============================================================================
    
    @staticmethod
    def get_compliance_instruction(is_compliance_question: bool, has_drawing: bool, formatted_timestamp: str) -> str:
        """Get special instructions for compliance questions."""
        if not is_compliance_question or not has_drawing:
            return ""
        
        return f"""

⚠️ CRITICAL COMPLIANCE QUESTION INSTRUCTIONS - OVERRIDE STANDARD RULES ⚠️

This is a COMPLIANCE question. You MUST attempt to answer even with partial information:

1. DO NOT say "I cannot answer" - synthesize available information
2. List ALL specific rules/limits mentioned in ANY context
3. Compare building specs against those rules
4. Provide structured answer format:

Based on the available regulations and your drawing from {formatted_timestamp}:

✅ COMPLIANT:
[List rules that the building clearly meets]

⚠️ NEEDS VERIFICATION:
[List rules that may not be met or need more information]

ℹ️ ADDITIONAL REQUIREMENTS:
[List other relevant rules mentioned in contexts]

5. If contexts are fragmented, synthesize what you CAN determine
6. ALWAYS provide this structured answer for compliance questions
"""
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    @staticmethod
    def format_contexts(pdf_results: list, selected_index: int = None) -> str:
        """
        Format multiple PDF results as numbered contexts.
        
        Args:
            pdf_results: List of PDFResult objects
            selected_index: Optional index of the selected context (0-based)
            
        Returns:
            Formatted string with numbered contexts
        """
        contexts = []
        for i, result in enumerate(pdf_results, 1):
            selected_marker = " [SELECTED]" if selected_index is not None and i == selected_index + 1 else ""
            context = f"""Context {i} (Score: {result.score:.2f}){selected_marker}:
Source: {result.pdf_filename}, Page {result.page_number}
{result.source_snippet}"""
            contexts.append(context)
        
        return "\n\n".join(contexts)
    

    
    @staticmethod
    def format_drawing_context_section(drawing_context: str) -> str:
        """
        Format drawing context for inclusion in prompts.
        
        Args:
            drawing_context: Formatted drawing context string
            
        Returns:
            Formatted drawing section or empty string
        """
        if not drawing_context:
            return ""
        return f"\n\nUser's Building Specifications:\n{drawing_context}\n"
    
    @staticmethod
    def detect_compliance_question(query: str) -> bool:
        """
        Detect if a question is about compliance/regulations.
        
        Args:
            query: User's question
            
        Returns:
            True if question is about compliance
        """
        compliance_keywords = [
            'comply', 'compliance', 'permitted development', 
            'allowed', 'legal', 'regulation', 'requirement',
            'rule', 'restriction', 'permission'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in compliance_keywords)
    
    @staticmethod
    def detect_drawing_question(query: str) -> bool:
        """
        Detect if a question is about the building drawing/specifications.
        
        Args:
            query: User's question
            
        Returns:
            True if question is about drawing
        """
        drawing_keywords = [
            'plot', 'area', 'dimension', 'size', 'building', 
            'wall', 'door', 'window', 'floor', 'height', 
            'width', 'length', 'room', 'space', 'layout',
            'my building', 'my plot', 'my property'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in drawing_keywords)
    
    @staticmethod
    def format_timestamp(iso_timestamp: str) -> str:
        """
        Convert ISO timestamp to display format.
        
        Args:
            iso_timestamp: ISO 8601 timestamp string
            
        Returns:
            Formatted timestamp as "DD/MM/YYYY, HH:MM:SS"
        """
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y, %H:%M:%S")
        except Exception:
            return iso_timestamp


# ============================================================================
# PROMPT BUILDER CLASS
# ============================================================================

class PromptBuilder:
    """
    Builder class for constructing prompts with proper formatting.
    
    Usage:
        builder = PromptBuilder()
        prompt = builder.build_pdf_multiple_contexts(
            query="What is permitted development?",
            pdf_results=[...],
            drawing_context="...",
            formatted_timestamp="17/01/2026, 14:08:20"
        )
    """
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_pdf_multiple_contexts(
        self,
        query: str,
        pdf_results: list,
        drawing_context: str = None,
        formatted_timestamp: str = None
    ) -> tuple[str, str]:
        """
        Build prompt for PDF response with multiple contexts.
        
        Returns:
            Tuple of (prompt, system_prompt)
        """
        # Format contexts
        contexts = self.templates.format_contexts(pdf_results)
        
        # Format optional sections
        drawing_section = self.templates.format_drawing_context_section(drawing_context)
        
        # Build conditional instructions
        has_drawing = bool(drawing_context)
        is_compliance = self.templates.detect_compliance_question(query)
        
        building_spec_note = self.templates.get_building_spec_note(has_drawing)
        building_spec_instruction1 = self.templates.get_building_spec_instruction1(has_drawing)
        building_spec_instruction2 = self.templates.get_building_spec_instruction2(has_drawing)
        building_spec_instruction3 = self.templates.get_building_spec_instruction3(has_drawing, formatted_timestamp or "")
        compliance_instruction = self.templates.get_compliance_instruction(is_compliance, has_drawing, formatted_timestamp or "")
        
        # Build prompt
        prompt = self.templates.PDF_MULTIPLE_CONTEXTS.format(
            contexts=contexts,
            drawing_context=drawing_section,
            query=query,
            num_contexts=len(pdf_results),
            building_spec_note=building_spec_note,
            building_spec_instruction1=building_spec_instruction1,
            building_spec_instruction2=building_spec_instruction2,
            building_spec_instruction3=building_spec_instruction3,
            compliance_instruction=compliance_instruction
        )
        
        return prompt, self.templates.SYSTEM_GENERAL
    
    def build_pdf_single_context(
        self,
        query: str,
        context: str,
        drawing_context: str = None,
        formatted_timestamp: str = None
    ) -> tuple[str, str]:
        """
        Build prompt for PDF response with single context.
        
        Returns:
            Tuple of (prompt, system_prompt)
        """
        # Format optional sections
        drawing_section = self.templates.format_drawing_context_section(drawing_context)
        
        # Build conditional instructions
        has_drawing = bool(drawing_context)
        
        building_spec_note = self.templates.get_building_spec_note(has_drawing)
        building_spec_instruction1 = self.templates.get_building_spec_instruction1(has_drawing)
        building_spec_instruction2 = self.templates.get_building_spec_instruction2(has_drawing)
        building_spec_instruction3 = self.templates.get_building_spec_instruction3(has_drawing, formatted_timestamp or "")
        
        # Build prompt
        prompt = self.templates.PDF_SINGLE_CONTEXT.format(
            context=context,
            drawing_context=drawing_section,
            query=query,
            building_spec_note=building_spec_note,
            building_spec_instruction1=building_spec_instruction1,
            building_spec_instruction2=building_spec_instruction2,
            building_spec_instruction3=building_spec_instruction3
        )
        
        return prompt, self.templates.SYSTEM_GENERAL
    
    def build_json_only_drawing(
        self,
        query: str,
        drawing_context: str,
        drawing_json: dict,
        formatted_timestamp: str
    ) -> tuple[str, str]:
        """
        Build prompt for JSON-only drawing analysis.
        
        Returns:
            Tuple of (prompt, system_prompt)
        """
        # Limit JSON preview to prevent token overflow
        drawing_json_preview = str(drawing_json)[:2000]
        
        # Build prompt
        prompt = self.templates.JSON_ONLY_DRAWING.format(
            formatted_timestamp=formatted_timestamp,
            drawing_context=drawing_context,
            drawing_json_preview=drawing_json_preview,
            query=query
        )
        
        return prompt, self.templates.SYSTEM_DRAWING_ANALYSIS
