# Agentic AI System Documentation

## Overview

The Agentic AI System adds complete autonomous reasoning capabilities to the Hybrid RAG Q&A System using OpenAI's function calling. This enables multi-step reasoning, tool use, self-verification, and iterative refinement.

## What is Agentic AI?

Agentic AI refers to AI systems that can:

- **Plan**: Break down complex tasks into steps
- **Act**: Use tools autonomously to gather information
- **Observe**: Analyze results from tool execution
- **Iterate**: Refine solutions based on feedback
- **Verify**: Check their own work for correctness

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Agentic RAG System                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Agent Loop (max 10 iterations)                       │  │
│  │                                                        │  │
│  │  1. Agent decides what to do next                     │  │
│  │  2. Calls appropriate function/tool                   │  │
│  │  3. Receives result                                   │  │
│  │  4. Updates reasoning state                           │  │
│  │  5. Repeat or provide final answer                    │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Retrieve   │  │   Analyze   │  │  Generate   │
│ Regulations │  │ Compliance  │  │  Compliant  │
│             │  │             │  │   Design    │
└─────────────┘  └─────────────┘  └─────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │     Verify      │
                │   Compliance    │
                └─────────────────┘
```

## Available Tools/Functions

The agent has access to 5 powerful tools:

### 1. retrieve_regulations

**Purpose**: Search for relevant building regulations in the knowledge base

**When to use**:

- User asks about specific rules or requirements
- Need to find regulations for compliance checking
- Looking for permitted development criteria

**Example**:

```json
{
  "query": "extension depth limits for residential buildings",
  "top_k": 5
}
```

**Returns**:

```json
{
  "success": true,
  "count": 5,
  "regulations": [
    {
      "id": 0,
      "document": "Building_Regulations_2024.pdf",
      "page": 12,
      "content": "Extensions must not exceed 6m in depth...",
      "relevance": 0.89
    }
  ]
}
```

### 2. analyze_drawing_compliance

**Purpose**: Analyze a building drawing against regulations to identify violations

**When to use**:

- User asks "Is my design compliant?"
- Need to check specific aspects of a drawing
- Before generating adjusted designs

**Example**:

```json
{
  "drawing_json": {...},
  "regulations": ["Extension depth limit: 6m", "Height limit: 12m"]
}
```

**Returns**:

```json
{
  "success": true,
  "violations": ["Extension depth of 7m exceeds the 6m limit"],
  "compliant": ["Building height of 10m is within the 12m limit"],
  "measurements": {
    "extension_depth": "7m",
    "building_height": "10m"
  }
}
```

### 3. calculate_drawing_dimensions

**Purpose**: Calculate specific measurements from a building drawing

**When to use**:

- Need exact measurements for analysis
- User asks about dimensions
- Before compliance checking

**Example**:

```json
{
  "drawing_json": {...},
  "dimension_type": "all"  // or "plot_area", "extension_depth", "building_height"
}
```

**Returns**:

```json
{
  "success": true,
  "dimensions": {
    "plot_width_m": 20.0,
    "plot_height_m": 15.0,
    "plot_area_m2": 300.0,
    "extension_depth_m": 7.0
  }
}
```

### 4. generate_compliant_design

**Purpose**: Create an adjusted, compliant version of a non-compliant drawing

**When to use**:

- User asks to "fix" or "adjust" their design
- After identifying violations
- User wants a compliant alternative

**Example**:

```json
{
  "original_drawing": {...},
  "violations": ["Extension depth exceeds 6m limit"],
  "regulations": ["Maximum extension depth: 6m"]
}
```

**Returns**:

```json
{
  "success": true,
  "adjusted_drawing": {...},
  "changes_made": [
    "Reduced extension depth from 7m to 6m",
    "Adjusted rear wall position"
  ],
  "compliance_verification": "The adjusted design now complies with all regulations"
}
```

### 5. verify_compliance

**Purpose**: Verify if a drawing complies with regulations (final check)

**When to use**:

- After generating adjusted designs
- User wants confirmation of compliance
- Final verification step

**Example**:

```json
{
  "drawing_json": {...},
  "regulations": ["Extension depth: max 6m", "Height: max 12m"]
}
```

**Returns**:

```json
{
  "success": true,
  "compliant": true,
  "explanation": "All measurements are within permitted limits",
  "remaining_issues": []
}
```

## Usage

### Standard Endpoint (Non-Agentic)

```bash
POST /api/agent/query
```

Uses the traditional RAG pipeline without agentic capabilities.

### Agentic Endpoint

```bash
POST /api/agent/query-agentic
```

Enables full agentic workflow with function calling.

### Example Request

```bash
curl -X POST "http://localhost:8001/api/agent/query-agentic" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "My extension is 7m deep. Can you provide an adjusted compliant design?",
    "drawing_json": [
      {"type": "POLYLINE", "layer": "Walls", "points": [[0,0], [10000,0], [10000,8000], [0,8000]], "closed": true},
      {"type": "POLYLINE", "layer": "Walls", "points": [[3000,8000], [7000,8000], [7000,15000], [3000,15000]], "closed": true},
      {"type": "POLYLINE", "layer": "Plot Boundary", "points": [[0,0], [20000,0], [20000,20000], [0,20000]], "closed": true}
    ],
    "drawing_updated_at": "2026-01-18T10:30:00Z"
  }'
```

### Example Response

```json
{
  "answer": "I've analyzed your extension and created a compliant design. Your original extension depth of 7m exceeds the permitted 6m limit. I've adjusted the design to reduce the extension depth to exactly 6m while maintaining functionality. The adjusted design now fully complies with building regulations.",
  "answer_type": "pdf",
  "sources": [
    {
      "type": "pdf",
      "document": "Building_Regulations_2024.pdf",
      "page": 12,
      "relevance": 0.89,
      "snippet": "Extensions must not exceed 6m in depth..."
    }
  ],
  "drawing_context_used": true,
  "reasoning_steps": [
    {
      "step": 1,
      "action": "retrieve_regulations",
      "arguments": {"query": "extension depth limits"},
      "result": {"success": true, "count": 5}
    },
    {
      "step": 2,
      "action": "calculate_drawing_dimensions",
      "arguments": {"dimension_type": "extension_depth"},
      "result": {"success": true, "dimensions": {"extension_depth_m": 7.0}}
    },
    {
      "step": 3,
      "action": "analyze_drawing_compliance",
      "arguments": {"drawing_json": {...}, "regulations": [...]},
      "result": {"success": true, "violations": ["Extension depth exceeds 6m"]}
    },
    {
      "step": 4,
      "action": "generate_compliant_design",
      "arguments": {"original_drawing": {...}, "violations": [...]},
      "result": {"success": true, "adjusted_drawing": {...}}
    },
    {
      "step": 5,
      "action": "verify_compliance",
      "arguments": {"drawing_json": {...}},
      "result": {"success": true, "compliant": true}
    }
  ]
}
```

## Agent Workflow Examples

### Example 1: Simple Compliance Check

**User**: "Is my building compliant?"

**Agent Reasoning**:

1. Retrieve regulations about building compliance
2. Calculate dimensions from drawing
3. Analyze compliance against regulations
4. Provide structured answer

**Tools Used**: `retrieve_regulations` → `calculate_drawing_dimensions` → `analyze_drawing_compliance`

### Example 2: Generate Compliant Design

**User**: "My extension is too deep. Can you fix it?"

**Agent Reasoning**:

1. Retrieve extension depth regulations
2. Calculate current extension depth
3. Analyze what's wrong
4. Generate adjusted compliant design
5. Verify the adjusted design complies
6. Provide adjusted JSON with explanation

**Tools Used**: `retrieve_regulations` → `calculate_drawing_dimensions` → `analyze_drawing_compliance` → `generate_compliant_design` → `verify_compliance`

### Example 3: Complex Multi-Aspect Analysis

**User**: "Check if my building meets all permitted development criteria"

**Agent Reasoning**:

1. Retrieve all permitted development regulations
2. Calculate all dimensions (plot area, extension depth, height)
3. Analyze compliance for each criterion
4. Provide comprehensive report

**Tools Used**: `retrieve_regulations` → `calculate_drawing_dimensions` (multiple calls) → `analyze_drawing_compliance`

## Configuration

The agentic system uses the same configuration as the main RAG system:

```bash
# .env
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4  # Recommended for agentic workflows
LLM_TEMPERATURE=0.3
```

**Note**: GPT-4 is recommended for agentic workflows as it has better reasoning capabilities than GPT-3.5 or GPT-4o-mini.

## Benefits of Agentic Approach

### 1. Multi-Step Reasoning

- Breaks down complex questions automatically
- Handles tasks that require multiple operations
- More thorough analysis

### 2. Autonomous Tool Use

- Agent decides which tools to use
- Calls tools in the right order
- No need to manually orchestrate steps

### 3. Self-Verification

- Agent can verify its own solutions
- Iterates if needed
- Higher quality results

### 4. Transparency

- All reasoning steps are logged
- Users can see what the agent did
- Easier to debug and trust

### 5. Flexibility

- Handles unexpected questions
- Adapts to different scenarios
- More robust than fixed pipelines

## Comparison: Standard vs Agentic

| Feature      | Standard RAG   | Agentic RAG             |
| ------------ | -------------- | ----------------------- |
| Reasoning    | Single-step    | Multi-step              |
| Tool Use     | Fixed pipeline | Autonomous              |
| Verification | None           | Self-verifying          |
| Complexity   | Simple queries | Complex tasks           |
| Transparency | Limited        | Full reasoning trace    |
| Iterations   | None           | Up to 10                |
| Cost         | Lower          | Higher (more API calls) |
| Quality      | Good           | Excellent               |

## When to Use Each Mode

### Use Standard Mode When:

- Simple factual questions
- Single-step retrieval sufficient
- Cost is a concern
- Fast response needed

### Use Agentic Mode When:

- Complex multi-step tasks
- Need to generate adjusted designs
- Verification required
- Quality over speed
- User asks to "fix", "adjust", or "verify"

## Limitations

1. **Cost**: Agentic mode makes multiple LLM calls (higher cost)
2. **Latency**: Takes longer due to multiple iterations
3. **Max Iterations**: Limited to 10 iterations (configurable)
4. **Model Dependency**: Works best with GPT-4 (GPT-3.5 may struggle)

## Future Enhancements

Potential improvements:

- [ ] Add more specialized tools (calculate costs, check planning permission)
- [ ] Implement conversation memory across sessions
- [ ] Add human-in-the-loop for critical decisions
- [ ] Support for parallel tool execution
- [ ] Integration with external APIs (planning portals, etc.)
- [ ] Visual reasoning for drawing analysis
- [ ] Multi-agent collaboration

## Troubleshooting

### Agent Reaches Max Iterations

**Cause**: Question too complex or agent stuck in loop  
**Solution**: Rephrase question, increase max_iterations, or use standard mode

### Agent Doesn't Call Expected Tools

**Cause**: Unclear question or model limitations  
**Solution**: Be more specific in question, use GPT-4 instead of GPT-3.5

### High API Costs

**Cause**: Many agentic queries  
**Solution**: Use standard mode for simple queries, reserve agentic for complex tasks

### Slow Response Times

**Cause**: Multiple tool calls and LLM iterations  
**Solution**: Expected behavior, use standard mode if speed is critical

## Monitoring

The agentic system provides detailed logging:

```
🤖 AGENTIC WORKFLOW STARTED
Query: My extension is 7m deep. Can you fix it?
Has drawing: True
Max iterations: 10

🔄 ITERATION 1/10
🔧 Agent calling function: retrieve_regulations
📋 Arguments: {"query": "extension depth limits"}
✅ Function result: {"success": true, "count": 5}

🔄 ITERATION 2/10
🔧 Agent calling function: calculate_drawing_dimensions
...

✅ AGENTIC WORKFLOW COMPLETED
Total iterations: 5
Functions called: 5
```

## API Reference

See the interactive API documentation at:

- http://localhost:8001/docs

Look for the `/api/agent/query-agentic` endpoint.

## Examples

See `examples/agentic_queries.md` for more example queries and expected agent behaviors.

---

**Built with OpenAI Function Calling** | **Part of the Hybrid RAG Q&A System**
