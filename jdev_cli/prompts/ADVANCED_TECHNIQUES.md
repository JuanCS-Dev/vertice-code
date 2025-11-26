# Advanced Prompt Engineering Techniques

Based on official documentation from Google AI, OpenAI, and Anthropic.

## 1. GOOGLE AI BEST PRACTICES (69-page White Paper)

### Core Principles
- **Clarity & Specificity**: Direct commands, step-by-step tasks, eliminate ambiguity
- **Output Format**: Always specify desired format (JSON, markdown, etc.)
- **Simple Language**: Concise action verbs - act, analyze, categorize, compare
- **System Prompts**: Set global instructions for session behavior

### Few-Shot Prompting
- **Zero-shot**: Task description only (for well-understood tasks)
- **One-shot**: Single example to illustrate style
- **Few-shot**: Multiple examples for complex tasks (3-5 optimal)

### Model Configuration
- **Temperature**: 0.1-0.3 (deterministic), 0.7-1.0 (creative)
- **Top-P/K**: Control diversity and randomness
- **Token Limits**: Specify max length for resource management

### Chain-of-Thought & ReAct
- Break complex problems into stepwise thinking
- Encourage reasoning before answers
- Use for logical reasoning, math, code analysis

### PTCF Framework (Gemini)
1. **Persona**: "You are an AI code assistant..."
2. **Task**: "Read the file and extract..."
3. **Context**: Working directory, recent files, git branch
4. **Format**: "Return JSON: [{"tool": "...", "args": {...}}]"

---

## 2. OPENAI BEST PRACTICES

### Core Recommendations
1. **Use Latest Model**: More capable = easier prompting
2. **Instructions First**: Put instructions at start, use delimiters (###, """)
3. **Be Specific**: Define outcomes, context, length, format, style
4. **Show Format**: Demonstrate ideal output with examples
5. **Iterate**: Prompt engineering is empirical - test & refine

### Chat-Based Models (ChatML)
- Use distinct `system`, `user`, `assistant` messages
- System: Overall guidance and behavior
- User: Specific requests and examples
- Assistant: Previous responses for context

### Chain-of-Thought
- "Show your reasoning before giving the final answer"
- "Think step by step"
- "Break this down into smaller steps"

### Control Mechanisms
- Token limits
- Stop sequences
- Delimiters for sections
- Temperature tuning

---

## 3. ANTHROPIC CLAUDE BEST PRACTICES

### Function Calling & Tool Use
- Define clear tool schemas (name, description, parameters)
- Use `strict: true` for schema validation in production
- Iterate: pass tool results back to Claude
- Break complex workflows into multiple tool calls

### Tool Schema Structure
```json
{
  "name": "readfile",
  "description": "Read contents of a file at the specified path",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Absolute or relative file path"
      }
    },
    "required": ["path"]
  }
}
```

### Prompt Structure
- Precision and clarity
- Structured inputs (JSON, XML)
- Breaking tasks into steps
- Role assignment
- Using examples for multishot prompting
- Force schema and output format

### Best Practices
- **Clear task definition**: State goal explicitly
- **Schema validation**: Use strict mode
- **Iterative improvement**: Test and refine
- **Context management**: Don't overload tools
- **Examples**: Provide few-shot examples

---

## 4. UNIVERSAL BEST PRACTICES

### Tool Calling Excellence
1. **Descriptive Names**: Use clear, action-oriented names
   - Good: `readfile`, `searchfiles`, `gitcommit`
   - Bad: `do_thing`, `process`, `handle`

2. **Rich Descriptions**: Explain what, why, when
   ```
   "Read the complete contents of a file. Use this when user asks 
   to view, read, or examine file contents. Returns full text."
   ```

3. **Parameter Clarity**: Document each parameter
   - Type, description, constraints
   - Mark required vs optional
   - Provide examples

4. **Category Grouping**: Organize tools by function
   - file_reading, file_writing, git, search, execution
   - Helps LLM understand relationships

### Few-Shot Examples Best Practices
- **Cover Common Cases**: 80% of user requests
- **Show Correct Format**: Exact JSON structure
- **Include Edge Cases**: Error handling, multiple steps
- **Categorize**: Group by tool type for selection
- **Progressive Complexity**: Simple → complex examples

### Error Recovery Patterns
- Always include error context
- Show previous action that failed
- Suggest alternatives
- Ask for clarification when ambiguous

### Context Management
- Keep recent history (5-10 turns)
- Track modified files
- Remember last commands
- Include git branch/status
- Working directory awareness

### Output Format Enforcement
```
"Respond with ONLY:
1. JSON array of tool calls: [{"tool": "name", "args": {...}}]
   OR
2. Helpful text response if no tools needed

Never mix JSON and text in response."
```

---

## 5. PRODUCTION PATTERNS

### Multi-Step Workflows
```
System: You are an AI assistant. When a task requires multiple
steps, plan ahead and execute them in sequence.

User: Create a new Python file called utils.py with a hello function

Expected Response:
[
  {"tool": "writefile", "args": {
    "path": "utils.py", 
    "content": "def hello(name):\n    return f'Hello, {name}!'\n"
  }}
]
```

### Parallel Tool Calls
```
User: Show me main.py and config.json

Expected Response:
[
  {"tool": "readfile", "args": {"path": "main.py"}},
  {"tool": "readfile", "args": {"path": "config.json"}}
]
```

### Error Recovery
```
System: When a tool call fails, analyze the error and suggest fixes.

Previous Error: FileNotFoundError: 'main.py' not found

User: Read main.py

Response:
[
  {"tool": "listfiles", "args": {"path": "."}},
  {"tool": "searchfiles", "args": {"pattern": "main", "file_pattern": "*.py"}}
]
```

### Contextual Awareness
```
Context:
- Working directory: /home/user/project
- Modified files: config.py
- Recent files: main.py, utils.py
- Git branch: feature/new-api

User: commit my changes

Response:
[
  {"tool": "gitstatus", "args": {}},
  {"tool": "gitadd", "args": {"files": ["config.py"]}},
  {"tool": "gitcommit", "args": {"message": "Update config"}}
]
```

---

## 6. ANTI-PATTERNS (AVOID)

❌ **Vague Instructions**
- "Do something with the file" → ✅ "Read the contents of main.py"

❌ **Mixed Output**
- Returning both JSON and text in same response

❌ **Missing Required Parameters**
- Always include all required parameters in tool calls

❌ **Ambiguous Tool Selection**
- Provide clear guidelines for which tool to use when

❌ **No Error Handling**
- Always plan for failures and provide recovery paths

❌ **Overloading Context**
- Don't send 50+ tool schemas at once
- Filter to relevant tools based on query

❌ **Negative Instructions**
- "Don't use X" → ✅ "Use Y for this task"

---

## 7. TESTING & VALIDATION

### Prompt Quality Metrics
- **Tool Call Accuracy**: 80%+ correct first attempt
- **Parameter Completeness**: All required params present
- **Format Compliance**: Valid JSON, no mixed output
- **Error Recovery**: Graceful handling of failures
- **Context Usage**: Leverages available context

### Testing Strategy
1. **Unit Tests**: Individual tool calls
2. **Integration Tests**: Multi-step workflows
3. **Edge Cases**: Errors, ambiguity, complex queries
4. **Real-World**: Capture production patterns

### Continuous Improvement
- Log all tool calls
- Track success/failure rates
- Analyze failure patterns
- Update few-shot examples
- Refine system prompts

---

## REFERENCES

### Google AI
- https://ai.google.dev/gemini-api/docs/prompting-strategies
- https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling
- Google's 69-page Prompt Engineering White Paper (2025)

### OpenAI
- https://platform.openai.com/docs/guides/prompt-engineering/
- https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide
- https://help.openai.com/en/articles/6654000-best-practices

### Anthropic Claude
- https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
- https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
- https://github.com/anthropics/courses/tree/master/tool_use

---

**This document synthesizes the best practices from the three leading AI labs.**
**All techniques are production-tested and backed by official documentation.**
