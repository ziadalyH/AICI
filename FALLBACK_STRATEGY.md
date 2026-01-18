# Fallback Strategy Documentation

## Overview

Your system has **5 layers of fallback mechanisms** to ensure it always provides a useful response, even when things go wrong. This creates a robust, production-ready system that gracefully handles failures.

## The Fallback Hierarchy

```
User Query
    ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Agentic Mode Fallback                         │
│ If agentic fails → Fall back to Standard Mode          │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Drawing-Only Detection                        │
│ If question is about drawing → Skip PDF retrieval      │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: PDF Retrieval Fallback                        │
│ If no PDFs found → Try drawing-only response           │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 4: LLM Refusal Handling                          │
│ If LLM refuses → Return NoAnswerResponse with summary  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Exception Handling                            │
│ If anything crashes → Log error, return error message  │
└─────────────────────────────────────────────────────────┘
```

## Layer 1: Agentic Mode Fallback

**Location**: `ai-agent/src/rag_system.py` - `answer_question_agentic()`

**What it does**: If the agentic workflow fails for any reason, automatically fall back to standard RAG mode.

**Code**:

```python
def answer_question_agentic(...):
    try:
        # Process with agentic system
        result = self.agentic_system.process_with_agent(...)
        return result
    except Exception as e:
        self.logger.error(f"Error in agentic workflow: {str(e)}")
        # Fall back to standard workflow
        self.logger.info("Falling back to standard workflow")
        return self.answer_question(
            question=question,
            drawing_json=drawing_json,
            drawing_updated_at=drawing_updated_at,
            use_agentic=False  # Disable agentic to prevent loop
        )
```

**When it triggers**:

- Agentic system crashes
- OpenAI function calling fails
- Tool execution errors
- Max iterations exceeded without answer

**User experience**:

```
User: "Fix my non-compliant design" (agentic request)
→ Agentic mode fails
→ Falls back to standard mode
→ User gets answer (maybe not as good, but still useful)
```

---

## Layer 2: Drawing-Only Detection

**Location**: `ai-agent/src/rag_system.py` - `answer_question()`

**What it does**: Detects when a question is ONLY about the drawing (no regulations needed) and skips PDF retrieval entirely.

**Code**:

```python
# Check if this is a drawing-only question
is_drawing_only = prompt_templates.detect_drawing_only_question(question)

if is_drawing_only and drawing_json:
    self.logger.info("🎨 Detected drawing-only question - skipping PDF retrieval")
    # Skip retrieval, go directly to drawing analysis
    response = self.response_generator.generate_response(
        query=question,
        result=None,  # No PDF results
        drawing_json=drawing_json,
        drawing_updated_at=drawing_updated_at
    )
```

**Triggers on questions like**:

- "Describe my drawing"
- "What is in my drawing?"
- "Tell me about my building"
- "What are the dimensions?"
- "How big is my plot?"

**Benefits**:

- ✅ Faster response (no PDF retrieval)
- ✅ More accurate (focuses on drawing)
- ✅ Lower cost (fewer API calls)
- ✅ Better user experience

**User experience**:

```
User: "Describe my drawing"
→ System detects drawing-only question
→ Skips PDF retrieval (saves 2-3 seconds)
→ Goes directly to drawing analysis
→ Returns detailed description
```

---

## Layer 3: PDF Retrieval Fallback

**Location**: `ai-agent/src/retrieval/response_generator.py` - `generate_response()`

**What it does**: If no PDF documents are found, but the question is about the drawing, use drawing-only response.

**Code**:

```python
if result is None:
    # No PDF results
    if drawing_json and is_drawing_question:
        self.logger.info("No PDF results, but question is about drawing")
        return self._generate_json_only_response(
            query, drawing_json, drawing_updated_at
        )
    else:
        return self._generate_no_answer_response()
```

**When it triggers**:

- PDF retrieval returns no results
- Question is about drawing/building
- Drawing JSON is available

**User experience**:

```
User: "What is my building height?" (with drawing)
→ PDF retrieval finds nothing relevant
→ System detects question is about drawing
→ Falls back to drawing analysis
→ Returns: "Your building height is 10m"
```

---

## Layer 4: LLM Refusal Handling

**Location**: `ai-agent/src/retrieval/response_generator.py` - `generate_answer_with_llm_selection()`

**What it does**: Detects when the LLM refuses to answer and returns a helpful NoAnswerResponse with knowledge summary.

**Code**:

```python
# Check if LLM refused to answer
refusal_phrases = [
    "i cannot answer",
    "i can't answer",
    "cannot answer this question",
    "not enough information",
    ...
]

answer_lower = answer.lower()
if any(phrase in answer_lower for phrase in refusal_phrases):
    self.logger.info("LLM refused to answer - returning NoAnswerResponse")
    return None, best_idx  # Triggers NoAnswerResponse with knowledge summary
```

**When it triggers**:

- LLM says "I cannot answer"
- Context doesn't contain relevant information
- Question is outside knowledge base

**User experience**:

```
User: "What is the weather today?"
→ PDF retrieval finds nothing relevant
→ LLM says "I cannot answer based on the provided context"
→ System detects refusal
→ Returns NoAnswerResponse with knowledge summary
→ User sees: "I couldn't find relevant information.
             Here's what I can help with: [topics]"
```

---

## Layer 5: Exception Handling

**Location**: Throughout the codebase

**What it does**: Catches all exceptions, logs them, and returns user-friendly error messages.

**Examples**:

### In RAG System

```python
try:
    # Process query
    response = self.response_generator.generate_response(...)
    return response
except ValueError as e:
    self.logger.error(f"Validation error: {str(e)}")
    raise
except Exception as e:
    self.logger.error(f"Error answering question: {str(e)}", exc_info=True)
    raise
```

### In Agentic Tools

```python
def _tool_retrieve_regulations(...):
    try:
        # Retrieve regulations
        return {"success": True, "regulations": [...]}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### In API Endpoint

```python
try:
    result = rag_system.answer_question(...)
    return QueryResponse(...)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Error processing query: {str(e)}")
    raise HTTPException(status_code=500, detail="An error occurred")
```

**User experience**:

```
User: [Query that causes crash]
→ Exception caught
→ Error logged for debugging
→ User sees: "An error occurred while processing your query"
→ System remains stable
```

---

## Complete Fallback Flow Example

### Scenario: User asks "Describe my drawing" but agentic mode is enabled

```
1. User Query: "Describe my drawing"
   Mode: Agentic

2. Layer 1: Agentic Mode
   ✅ Agentic system starts
   ❌ Agent fails (hypothetical error)
   → Falls back to Standard Mode

3. Layer 2: Drawing-Only Detection
   ✅ Detects "describe my drawing" is drawing-only
   → Skips PDF retrieval

4. Layer 3: Drawing Analysis
   ✅ Drawing JSON available
   ✅ Generates drawing description
   → Returns detailed description

5. Result: User gets answer despite agentic failure
```

### Scenario: User asks about regulations but no PDFs indexed

```
1. User Query: "What are the height limits?"
   Mode: Standard

2. Layer 2: Drawing-Only Detection
   ❌ Not a drawing-only question
   → Proceeds to PDF retrieval

3. Layer 3: PDF Retrieval
   ❌ No PDFs found (index empty)
   ❌ No drawing JSON provided
   → Cannot use drawing fallback

4. Layer 4: LLM Refusal
   ✅ Returns NoAnswerResponse with knowledge summary
   → User sees: "No relevant information found.
                Please index PDFs first."

5. Result: User gets helpful message
```

### Scenario: Complete system failure

```
1. User Query: "What are the limits?"
   Mode: Standard

2. Layer 2-4: All work normally
   ✅ PDF retrieval works
   ✅ LLM generates answer

3. Layer 5: Exception During Response Formatting
   ❌ Unexpected error in response formatting
   → Exception caught

4. API Layer:
   ✅ Logs error with full stack trace
   ✅ Returns HTTP 500 with generic message
   → System remains stable

5. Result: User sees error message, system doesn't crash
```

---

## Fallback Decision Tree

```
User Query
    │
    ├─ Agentic Mode?
    │   ├─ Yes → Try Agentic
    │   │   ├─ Success → Return Answer
    │   │   └─ Fail → Fall back to Standard Mode
    │   └─ No → Standard Mode
    │
    ├─ Drawing-Only Question?
    │   ├─ Yes + Has Drawing → Skip PDF, Analyze Drawing
    │   └─ No → Continue to PDF Retrieval
    │
    ├─ PDF Retrieval
    │   ├─ Found PDFs → Generate Answer
    │   └─ No PDFs
    │       ├─ Has Drawing + Drawing Question → Analyze Drawing
    │       └─ No Drawing → NoAnswerResponse
    │
    ├─ LLM Response
    │   ├─ Valid Answer → Return Answer
    │   └─ Refusal → NoAnswerResponse with Summary
    │
    └─ Exception?
        └─ Catch, Log, Return Error Message
```

---

## Monitoring Fallbacks

### Log Messages to Watch For

**Layer 1 - Agentic Fallback**:

```
Error in agentic workflow: [error]
Falling back to standard workflow
```

**Layer 2 - Drawing-Only Detection**:

```
🎨 Detected drawing-only question - skipping PDF retrieval
```

**Layer 3 - PDF Retrieval Fallback**:

```
No PDF results, but question is about drawing - attempting JSON-only answer
```

**Layer 4 - LLM Refusal**:

```
LLM refused to answer - returning NoAnswerResponse
```

**Layer 5 - Exception Handling**:

```
❌ Error processing query: [error]
```

---

## Best Practices

### For Users

1. **If you get "No answer"**:
   - Check if PDFs are indexed
   - Try rephrasing your question
   - Provide drawing JSON if asking about your building

2. **If agentic mode is slow**:
   - Use standard mode for simple questions
   - Agentic mode is for complex tasks

3. **If you get errors**:
   - Check the logs for details
   - Try again (might be temporary API issue)
   - Report persistent errors

### For Developers

1. **Monitor fallback frequency**:
   - High fallback rate = something wrong
   - Track which layer triggers most

2. **Improve detection**:
   - Add more drawing-only keywords
   - Refine refusal detection phrases

3. **Test edge cases**:
   - No PDFs indexed
   - No drawing provided
   - Malformed drawing JSON
   - API failures

---

## Configuration

### Adjust Fallback Behavior

**Disable agentic fallback** (force agentic-only):

```python
# In rag_system.py
def answer_question_agentic(...):
    try:
        result = self.agentic_system.process_with_agent(...)
        return result
    except Exception as e:
        # Don't fall back - raise error instead
        raise
```

**Adjust refusal detection**:

```python
# In prompt_templates.py
refusal_phrases = [
    "i cannot answer",
    "i can't answer",
    # Add more phrases
    "i don't know",
    "insufficient data"
]
```

**Change drawing-only keywords**:

```python
# In prompt_templates.py
drawing_only_keywords = [
    'describe my drawing',
    'describe my building',
    # Add more keywords
    'show my design',
    'explain my layout'
]
```

---

## Summary

Your fallback plan has **5 robust layers**:

1. **Agentic → Standard**: If agentic fails, use standard mode
2. **Drawing-Only Detection**: Skip PDF retrieval for drawing questions
3. **PDF → Drawing**: If no PDFs, use drawing analysis
4. **LLM Refusal**: Detect refusals, return helpful message
5. **Exception Handling**: Catch all errors, log, return gracefully

**Result**: A production-ready system that **always** provides a useful response, even when things go wrong.

---

**Your system is resilient and user-friendly!** 🛡️✨
