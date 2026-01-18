# Agentic AI Quick Start Guide

## What You Just Got

Your system now has **complete agentic AI capabilities** using OpenAI's function calling. The agent can autonomously:

- 🧠 **Reason** through complex multi-step tasks
- 🔧 **Use tools** to retrieve, analyze, and generate
- ✅ **Verify** its own solutions
- 🔄 **Iterate** until the task is complete

## Quick Test

### 1. Start the Services

```bash
cd AICI
docker-compose up
```

### 2. Test Standard Mode (Fast)

```bash
curl -X POST "http://localhost:8001/api/agent/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the extension depth limits?"
  }'
```

### 3. Test Agentic Mode (Smart)

```bash
curl -X POST "http://localhost:8001/api/agent/query-agentic" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "My extension is 7m deep but the limit is 6m. Can you provide an adjusted compliant JSON?",
    "drawing_json": [
      {"type": "POLYLINE", "layer": "Walls", "points": [[0,0], [10000,0], [10000,8000], [0,8000]], "closed": true},
      {"type": "POLYLINE", "layer": "Walls", "points": [[3000,8000], [7000,8000], [7000,15000], [3000,15000]], "closed": true}
    ]
  }'
```

## What Happens in Agentic Mode

The agent will:

1. **Retrieve** regulations about extension depth limits
2. **Calculate** the current extension depth from your drawing
3. **Analyze** what's wrong (7m exceeds 6m limit)
4. **Generate** an adjusted compliant design
5. **Verify** the new design meets all requirements
6. **Return** the adjusted JSON with full explanation

All steps are logged and returned in `reasoning_steps`.

## Example Response

```json
{
  "answer": "I've analyzed your extension and created a compliant design...",
  "reasoning_steps": [
    {
      "step": 1,
      "action": "retrieve_regulations",
      "result": "Found 5 relevant regulations"
    },
    {
      "step": 2,
      "action": "calculate_drawing_dimensions",
      "result": "Extension depth: 7m"
    },
    {
      "step": 3,
      "action": "analyze_drawing_compliance",
      "result": "Violation: Extension exceeds 6m limit"
    },
    {
      "step": 4,
      "action": "generate_compliant_design",
      "result": "Created adjusted design with 6m extension"
    },
    {
      "step": 5,
      "action": "verify_compliance",
      "result": "Design is now compliant"
    }
  ]
}
```

## Run the Test Suite

```bash
cd AICI/ai-agent
python test_agentic.py
```

This will run 6 test cases demonstrating different agentic capabilities.

## When to Use Each Mode

### Standard Mode (`/api/agent/query`)

- ✅ Simple questions
- ✅ Fast responses needed
- ✅ Lower cost
- ✅ Single-step retrieval

### Agentic Mode (`/api/agent/query-agentic`)

- ✅ Complex multi-step tasks
- ✅ Need to generate adjusted designs
- ✅ Verification required
- ✅ "Fix", "adjust", "verify" requests
- ✅ Quality over speed

## Available Tools

The agent has 5 tools at its disposal:

1. **retrieve_regulations** - Search the knowledge base
2. **analyze_drawing_compliance** - Check if drawing complies
3. **calculate_drawing_dimensions** - Measure plot, extension, etc.
4. **generate_compliant_design** - Create adjusted designs
5. **verify_compliance** - Final verification check

## Configuration

The agentic system uses your existing `.env` configuration:

```bash
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4  # Recommended for best results
LLM_TEMPERATURE=0.3
```

**Tip**: GPT-4 works better than GPT-3.5 for agentic workflows.

## Cost Considerations

Agentic mode makes multiple LLM calls:

- Standard query: 1-2 API calls
- Agentic query: 3-10 API calls (depending on complexity)

Use agentic mode for complex tasks where quality matters.

## Monitoring

Check the logs to see the agent's reasoning:

```bash
docker-compose logs -f ai-agent
```

You'll see:

```
🤖 AGENTIC WORKFLOW STARTED
🔄 ITERATION 1/10
🔧 Agent calling function: retrieve_regulations
✅ Function result: ...
🔄 ITERATION 2/10
...
✅ AGENTIC WORKFLOW COMPLETED
```

## Next Steps

1. **Read the full documentation**: `AGENTIC_SYSTEM.md`
2. **Run the test suite**: `python test_agentic.py`
3. **Try your own queries**: Use the API endpoints
4. **Integrate with frontend**: Update frontend to use agentic endpoint

## Troubleshooting

### "Service unavailable"

- Make sure services are running: `docker-compose ps`
- Check logs: `docker-compose logs ai-agent`

### "Agent reaches max iterations"

- Question too complex - try breaking it down
- Or increase `max_iterations` in the code

### Slow responses

- Expected - agent is doing multiple steps
- Use standard mode for simple queries

## Support

- Full documentation: `AGENTIC_SYSTEM.md`
- API docs: http://localhost:8001/docs
- Test examples: `test_agentic.py`

---

**You now have a complete agentic AI system! 🎉**
