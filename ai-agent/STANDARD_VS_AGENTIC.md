# Standard vs Agentic Mode: Complete Comparison

## Quick Decision Guide

**Use Standard Mode** when:

- ✅ Simple factual questions
- ✅ Fast response needed
- ✅ Cost is a concern
- ✅ Single-step retrieval sufficient

**Use Agentic Mode** when:

- ✅ Complex multi-step tasks
- ✅ Need to generate/adjust designs
- ✅ Verification required
- ✅ Quality over speed matters
- ✅ User says "fix", "adjust", "verify"

## Detailed Comparison

### Architecture

| Aspect           | Standard Mode              | Agentic Mode           |
| ---------------- | -------------------------- | ---------------------- |
| **Pipeline**     | Fixed: Retrieve → Generate | Dynamic: Agent decides |
| **Steps**        | 1-2                        | 3-10 (adaptive)        |
| **Tools**        | None                       | 5 specialized tools    |
| **Planning**     | None                       | Autonomous             |
| **Verification** | None                       | Self-verifying         |

### Performance

| Metric             | Standard Mode | Agentic Mode       |
| ------------------ | ------------- | ------------------ |
| **Response Time**  | 2-5 seconds   | 10-30 seconds      |
| **API Calls**      | 1-2           | 3-10               |
| **Cost per Query** | $0.01-0.02    | $0.05-0.15         |
| **Accuracy**       | Good (85-90%) | Excellent (95-99%) |
| **Completeness**   | Partial       | Comprehensive      |

### Capabilities

| Capability               | Standard Mode | Agentic Mode |
| ------------------------ | ------------- | ------------ |
| **Answer Questions**     | ✅ Yes        | ✅ Yes       |
| **Retrieve Documents**   | ✅ Yes        | ✅ Yes       |
| **Analyze Compliance**   | ⚠️ Limited    | ✅ Full      |
| **Calculate Dimensions** | ❌ No         | ✅ Yes       |
| **Generate Designs**     | ⚠️ Basic      | ✅ Advanced  |
| **Verify Solutions**     | ❌ No         | ✅ Yes       |
| **Multi-step Reasoning** | ❌ No         | ✅ Yes       |
| **Self-correction**      | ❌ No         | ✅ Yes       |

## Example Scenarios

### Scenario 1: Simple Question

**Question**: "What are the extension depth limits?"

**Standard Mode**:

```
1. Retrieve relevant documents
2. Generate answer
→ Response: "Extension depth limit is 6m"
→ Time: 3 seconds
→ Cost: $0.01
```

**Agentic Mode**:

```
1. Agent decides to retrieve regulations
2. Calls retrieve_regulations tool
3. Analyzes results
4. Generates comprehensive answer
→ Response: "Extension depth limit is 6m for residential..."
→ Time: 8 seconds
→ Cost: $0.06
```

**Recommendation**: Use **Standard Mode** (faster, cheaper, sufficient)

---

### Scenario 2: Compliance Check

**Question**: "Is my building compliant?"

**Standard Mode**:

```
1. Retrieve regulations
2. Generate answer based on drawing
→ Response: "Based on the regulations, your building..."
→ Time: 4 seconds
→ Cost: $0.02
→ Accuracy: ~80% (may miss details)
```

**Agentic Mode**:

```
1. Retrieve all relevant regulations
2. Calculate all dimensions from drawing
3. Analyze each criterion systematically
4. Generate structured compliance report
→ Response: "✅ COMPLIANT: Height, plot coverage
             ⚠️ NEEDS VERIFICATION: Extension depth
             ℹ️ ADDITIONAL: Proximity to boundary"
→ Time: 15 seconds
→ Cost: $0.08
→ Accuracy: ~95% (comprehensive)
```

**Recommendation**: Use **Agentic Mode** (more thorough, structured)

---

### Scenario 3: Generate Compliant Design

**Question**: "My extension is 7m but limit is 6m. Fix it."

**Standard Mode**:

```
1. Retrieve regulations
2. Generate text response with suggestions
→ Response: "Your extension exceeds the limit.
            You should reduce it to 6m..."
→ Time: 5 seconds
→ Cost: $0.02
→ Output: Text suggestions only
```

**Agentic Mode**:

```
1. Retrieve extension regulations
2. Calculate current extension depth (7m)
3. Analyze violation (exceeds 6m limit)
4. Generate adjusted design (6m extension)
5. Verify new design complies
6. Return adjusted JSON + explanation
→ Response: Complete adjusted JSON with:
   - Corrected dimensions
   - Explanation of changes
   - Verification of compliance
→ Time: 25 seconds
→ Cost: $0.12
→ Output: Actionable adjusted JSON
```

**Recommendation**: Use **Agentic Mode** (only mode that can do this)

---

### Scenario 4: Complex Analysis

**Question**: "Analyze my building for all permitted development criteria"

**Standard Mode**:

```
1. Retrieve PD regulations
2. Generate general answer
→ Response: "Permitted development has several criteria..."
→ Time: 4 seconds
→ Cost: $0.02
→ Completeness: ~60% (general overview)
```

**Agentic Mode**:

```
1. Retrieve all PD regulations
2. Calculate plot area
3. Calculate extension depth
4. Calculate building height
5. Analyze each criterion
6. Generate comprehensive report
→ Response: Detailed analysis of:
   - Plot coverage: ✅ Compliant
   - Extension depth: ❌ Exceeds limit
   - Height: ✅ Compliant
   - Proximity: ⚠️ Needs verification
   - Materials: ℹ️ Not specified
→ Time: 30 seconds
→ Cost: $0.15
→ Completeness: ~95% (thorough)
```

**Recommendation**: Use **Agentic Mode** (comprehensive analysis needed)

## Cost Analysis

### Standard Mode

- **Simple question**: $0.01
- **With drawing**: $0.02
- **Complex question**: $0.03
- **Average**: $0.02 per query

### Agentic Mode

- **Simple task (3 steps)**: $0.05
- **Medium task (5 steps)**: $0.08
- **Complex task (8 steps)**: $0.12
- **Very complex (10 steps)**: $0.15
- **Average**: $0.10 per query

### Cost Optimization Strategy

1. **Use Standard for**:
   - Informational queries
   - Simple lookups
   - High-volume requests
   - Development/testing

2. **Use Agentic for**:
   - Compliance checks
   - Design generation
   - Verification tasks
   - Critical decisions

3. **Hybrid Approach**:
   - Start with Standard
   - Escalate to Agentic if needed
   - Use Agentic for final verification

## Response Quality

### Standard Mode Quality

**Strengths**:

- Fast and efficient
- Good for straightforward questions
- Consistent performance
- Low latency

**Limitations**:

- May miss nuances
- No verification
- Can't perform calculations
- Limited to single-step reasoning

**Best For**:

- "What is X?"
- "Tell me about Y"
- "Where can I find Z?"

### Agentic Mode Quality

**Strengths**:

- Comprehensive analysis
- Self-verifying
- Handles complexity
- Actionable outputs
- Transparent reasoning

**Limitations**:

- Slower response
- Higher cost
- May be overkill for simple questions

**Best For**:

- "Is my design compliant?"
- "Fix my non-compliant building"
- "Analyze all criteria"
- "Generate adjusted design"

## User Experience

### Standard Mode UX

```
User: "What are height limits?"
[2 seconds]
System: "Height limit is 12m for residential buildings."

✅ Fast
✅ Direct
⚠️ No context
⚠️ No verification
```

### Agentic Mode UX

```
User: "Is my 15m building compliant?"
[15 seconds - with progress indicators]
System:
"I've analyzed your building against regulations:

🔍 Retrieved 5 relevant regulations
📏 Calculated building height: 15m
❌ Analysis: Exceeds 12m limit for residential zones

Your building is NOT compliant. The height of 15m
exceeds the maximum permitted height of 12m.

Reasoning Steps:
1. Retrieved height regulations
2. Calculated building dimensions
3. Analyzed compliance
"

✅ Comprehensive
✅ Verified
✅ Transparent
⚠️ Slower
```

## API Endpoints

### Standard Endpoint

```bash
POST /api/agent/query

{
  "question": "What are the limits?",
  "drawing_json": {...}
}

Response:
{
  "answer": "...",
  "sources": [...]
}
```

### Agentic Endpoint

```bash
POST /api/agent/query-agentic

{
  "question": "Fix my non-compliant design",
  "drawing_json": {...}
}

Response:
{
  "answer": "...",
  "sources": [...],
  "reasoning_steps": [
    {"step": 1, "action": "retrieve_regulations", ...},
    {"step": 2, "action": "analyze_compliance", ...},
    {"step": 3, "action": "generate_compliant_design", ...}
  ]
}
```

## Monitoring & Debugging

### Standard Mode Logs

```
Processing query: What are the limits?
Step 1: Processing query
Step 2: Retrieving relevant PDF content
Step 3: Generating response
Query processed successfully
```

### Agentic Mode Logs

```
🤖 AGENTIC WORKFLOW STARTED
Query: Fix my design
Has drawing: True

🔄 ITERATION 1/10
🔧 Agent calling function: retrieve_regulations
✅ Function result: Found 5 regulations

🔄 ITERATION 2/10
🔧 Agent calling function: analyze_compliance
✅ Function result: Found 2 violations

🔄 ITERATION 3/10
🔧 Agent calling function: generate_compliant_design
✅ Function result: Created adjusted design

✅ AGENTIC WORKFLOW COMPLETED
Total iterations: 3
Functions called: 3
```

## Recommendations by Use Case

### For End Users (Frontend)

**Default**: Standard Mode

- Fast responses for most questions
- Lower costs
- Good user experience

**Upgrade to Agentic**:

- User clicks "Verify Compliance" button
- User clicks "Generate Compliant Design" button
- User asks complex questions
- Show progress indicator during agentic processing

### For API Clients

**Standard Mode**:

- Informational endpoints
- Search functionality
- Quick lookups
- High-volume requests

**Agentic Mode**:

- Compliance checking endpoints
- Design generation endpoints
- Verification endpoints
- Critical decision support

### For Developers

**During Development**:

- Use Standard Mode for testing
- Lower costs
- Faster iteration

**For Production**:

- Use Agentic Mode for critical features
- Better quality
- More reliable results

## Migration Strategy

### Phase 1: Parallel Running

- Keep Standard Mode as default
- Add Agentic Mode as optional
- A/B test with users
- Monitor costs and quality

### Phase 2: Selective Upgrade

- Use Agentic for specific features
- Keep Standard for general queries
- Optimize based on metrics

### Phase 3: Smart Routing

- Analyze question complexity
- Route automatically to appropriate mode
- Best of both worlds

## Conclusion

Both modes have their place:

**Standard Mode** = Fast, cheap, good for simple tasks  
**Agentic Mode** = Smart, thorough, best for complex tasks

**Best Practice**: Use Standard by default, escalate to Agentic when needed.

---

**Need Help Deciding?**

Ask yourself:

1. Does the task require multiple steps? → **Agentic**
2. Do I need verification? → **Agentic**
3. Do I need to generate/adjust designs? → **Agentic**
4. Is it a simple question? → **Standard**
5. Is speed critical? → **Standard**
6. Is cost a concern? → **Standard**
