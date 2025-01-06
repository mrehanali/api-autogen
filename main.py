import os
import json
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import autogen
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI-Powered Front-end Generator")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class GenerateCodeRequest(BaseModel):
    description: str

# Configure AutoGen agents
config_list = [{
    "model": os.getenv("MODEL_NAME", "gpt-4o"),
    "api_key": os.getenv("OPENAI_API_KEY"),
}]

llm_config = {
    "config_list": config_list,
    "temperature": 0.1,
    "seed": 42
}

def get_single_response(description: str) -> Dict[str, Any]:
    # Create agents
    assistant = autogen.AssistantAgent(
        name="developer",
        system_message="""You are a skilled React developer who generates complete React applications.
Your response must be ONLY a JSON object containing ALL the necessary files with their complete content.
You MUST implement all the features requested by the user in the description using a proper project structure.

Required base structure (extend based on requirements):
{
    "package.json": "dependencies and scripts",
    "tsconfig.json": "TypeScript configuration",
    "vite.config.ts": "Vite configuration",
    "index.html": "HTML template",
    "src/main.tsx": "Application entry point",
    "src/App.tsx": "Root component"
}

Directory organization guidelines:

1. src/pages/: 
   - Page components based on requirements
   - Use proper routing if needed
   - Include error boundaries

2. src/components/:
   - Only create components needed for the requirements
   - Organize by feature or common/shared
   - TypeScript props interfaces
   - Styled components or CSS modules

3. src/styles/:
   - Only create necessary style files
   - Consistent styling system
   - Responsive design utilities

4. src/hooks/:
   - Custom hooks based on requirements
   - Form handling if needed
   - Data fetching if needed

5. src/utils/:
   - Only create utilities needed for the requirements
   - Validation utilities if needed
   - Type guards if needed

6. src/types/:
   - TypeScript interfaces for the requirements
   - Type definitions as needed

7. src/services/:
   - API integration if needed
   - External services if required
   - Error handling

8. src/context/:
   - Context providers only if state management is needed

Technical requirements:
- Use TypeScript with strict type checking
- Follow React best practices and hooks
- Implement proper error handling
- Include proper styling and responsive design
- Production-ready code with error boundaries
- Proper file organization

DO NOT include any explanations or additional text. ONLY the JSON object with the files.""",
        llm_config=llm_config
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        code_execution_config=False,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0
    )
    
    # Create the chat
    chat_response = user_proxy.initiate_chat(
        assistant,
        message=f"""Create a complete React application that implements: {description}

RESPOND WITH ONLY A JSON OBJECT containing all necessary files and directories.

Base files needed:
- package.json (include necessary dependencies)
- tsconfig.json (TypeScript config)
- vite.config.ts (Vite config)
- index.html (template)
- src/main.tsx (entry point)
- src/App.tsx (root component)

Then, based on the requirements, create and organize additional files under:
- src/pages/
- src/components/
- src/styles/
- src/hooks/
- src/utils/
- src/types/
- src/services/
- src/context/

Each component MUST include:
- TypeScript interfaces
- Proper styling
- Error handling
- Loading states where needed
- Comments

Format:
{{
    "package.json": "content",
    "path/to/your/file.tsx": "content",
    ...
}}

NO additional text or explanations.""",
        clear_history=True
    )
    
    # Get the last message from the assistant
    messages = chat_response.chat_history
    if messages and len(messages) >= 2:
        last_message = messages[-1]
        if isinstance(last_message, dict) and "content" in last_message:
            return {"content": last_message["content"]}
    
    return {"content": None}

async def generate_code_workflow(description: str) -> AsyncGenerator[Dict[Any, str], None]:
    try:
        # Initial status messages
        yield f"data: {json.dumps({'code': 'Starting code generation...', 'file': 'status.log'})}\n\n"
        
        # Get response from the agent
        response = get_single_response(description)
        
        if response and "content" in response:
            try:
                # Extract content and clean it
                content = response["content"]
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Parse the JSON content
                files_content = json.loads(content)
                
                # Send ping event
                current_time = datetime.now(timezone.utc).isoformat()
                yield f": ping - {current_time}\n\n"
                
                # Stream all generated files
                for file_path, file_content in files_content.items():
                    yield f"data: {json.dumps({'code': file_content, 'file': file_path})}\n\n"
                    await asyncio.sleep(0.1)
                
                # Completion message
                yield f"data: {json.dumps({'code': 'Code generation complete!', 'file': 'status.log'})}\n\n"
                
            except json.JSONDecodeError:
                yield f"data: {json.dumps({'code': 'Error: Failed to parse generated code', 'file': 'status.log'})}\n\n"
        else:
            yield f"data: {json.dumps({'code': 'Error: No response received from the agent', 'file': 'status.log'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'code': f'Error: {str(e)}', 'file': 'status.log'})}\n\n"

@app.post("/generate-code")
async def generate_code(request: GenerateCodeRequest):
    if not request.description:
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    return StreamingResponse(
        generate_code_workflow(request.description),
        media_type="text/event-stream"
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 