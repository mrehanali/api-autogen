# Product Requirements Document: AI-Powered Front-end Generator
## 1. Product Overview
Create an AI-powered backend service that transforms natural language descriptions into React-based front-end code using AutoGen with streaming response, implementing a two-agent workflow for development and review.

## 2. Key Features
### 2.1 API Endpoint
- Single REST API endpoint accepting natural language UI descriptions
- Streaming response for real-time code generation feedback
- Support for technical and non-technical language input

### 2.2 AutoGen Integration
Two-agent workflow:
1. Developer Agent:
   - Processes natural language input
   - Generates React code based on requirements
   - Implements basic responsive design
   - Follows minimal design guidelines

2. Reviewer Agent:
   - Reviews generated code for best practices
   - Validates React component structure
   - Ensures Tailwind CSS usage compliance
   - Provides feedback for improvements

### 2.3 Code Generation
- React components with Tailwind CSS
- Basic responsive design
- Single page components only

## 3. Technical Requirements
### 3.1 Backend Architecture
- FastAPI framework with streaming support
- Single endpoint: `/generate-code`
- Request/Response format:
  ```json
  // Request
  {
    "description": "string"
  }
  
  // Response (streamed)
  {
    "code": "string",
    "status": "string",
    "review_feedback": "string"  // New field for reviewer insights
  }
  ```

### 3.2 AutoGen Implementation
Example workflow implementation:
```python
from autogen import AssistantAgent, UserProxyAgent
import asyncio
from typing import Dict, Any, AsyncGenerator

# Define the agents
developer_agent = AssistantAgent(
    name="developer",
    system_message="You are a skilled React developer who generates code based on requirements.",
    llm_config={
        "temperature": 0.7,
        "request_timeout": 600,
    }
)

reviewer_agent = AssistantAgent(
    name="reviewer",
    system_message="You are a code reviewer who ensures best practices and provides feedback.",
    llm_config={
        "temperature": 0.4,
        "request_timeout": 300,
    }
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    code_execution_config=False,
)

async def generate_code_workflow(description: str) -> AsyncGenerator[Dict[Any, str], None]:
    # Initialize state
    state = {
        "description": description,
        "code": "",
        "review_feedback": "",
        "status": "started"
    }
    
    # Development Phase
    dev_response = await developer_agent.generate_response(
        f"Generate React code for: {description}"
    )
    state["code"] = dev_response.content
    state["status"] = "code_generated"
    yield state
    
    # Review Phase
    review_response = await reviewer_agent.generate_response(
        f"Review this React code:\n{state['code']}"
    )
    state["review_feedback"] = review_response.content
    state["status"] = "reviewed"
    yield state

# FastAPI implementation
@app.post("/generate-code")
async def generate_code(request: GenerateCodeRequest):
    async def stream_response():
        async for state in generate_code_workflow(request.description):
            yield f"data: {json.dumps(state)}\n\n"
    
    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream"
    )

# Example usage
async def main():
    config = {
        "description": "Create a simple contact form"
    }
    async for state in generate_code_workflow(config["description"]):
        print(state)

if __name__ == "__main__":
    asyncio.run(main())
```

## 4. Design Guidelines
[Previous sections remain the same]

## 5. Technical Constraints
[Previous sections remain the same]

## 6. Success Criteria
- 85% code generation success rate
- 30-second maximum generation time
- Valid React code output with basic responsive design
- 90% of reviewer feedback implementation rate

Key changes made in the AutoGen implementation:
1. Replaced LangGraph's StateGraph with AutoGen's agent-based architecture
2. Implemented Developer and Reviewer as AssistantAgents
3. Added UserProxyAgent for orchestration
4. Created async generator for streaming responses
5. Maintained the same two-phase workflow structure
6. Preserved all state management capabilities

The AutoGen implementation provides the same structured workflow while leveraging AutoGen's more sophisticated agent-to-agent communication capabilities and built-in LLM integration.
