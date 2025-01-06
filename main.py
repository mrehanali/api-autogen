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
Your response must be ONLY a JSON object containing the following files with their complete content.
You MUST implement all the features requested by the user in the description.

{
    "package.json": "content of package.json",
    "tsconfig.json": "content of tsconfig.json",
    "vite.config.ts": "content of vite.config.ts",
    "index.html": "content of index.html",
    "src/main.tsx": "content of main.tsx",
    "src/App.tsx": "content of App.tsx"
}

Requirements for each file:
1. package.json: 
   - Include React 18, TypeScript, Vite
   - Add ALL necessary dependencies for the requested features (form handling, validation, UI components)
   - Include exact versions

2. tsconfig.json: 
   - Proper TypeScript configuration for React and Vite
   - Enable strict type checking

3. vite.config.ts: 
   - Basic Vite configuration with React plugin
   - Any additional plugins needed for the requested features

4. index.html: 
   - Include proper meta tags and root div
   - Add any required CDN links or meta tags

5. src/main.tsx: 
   - React 18 entry point with proper imports
   - Include any global providers or context needed

6. src/App.tsx: 
   - Implement ALL the features requested in the user's description
   - Include proper TypeScript types and interfaces
   - Add form validation and error handling
   - Implement all required event handlers
   - Add loading states and success messages
   - Include proper styling and layout
   - Add helpful comments explaining the code

Technical requirements:
- Use TypeScript with proper types and interfaces
- Follow React best practices and hooks
- Implement proper form validation and error handling
- Add loading states and success messages
- Include proper styling and responsive design
- Production-ready code with error boundaries

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

RESPOND WITH ONLY A JSON OBJECT containing these files:
- package.json (include ALL necessary dependencies for the requested features)
- tsconfig.json (proper TypeScript config)
- vite.config.ts (Vite config with needed plugins)
- index.html (with required meta tags)
- src/main.tsx (React 18 entry with required providers)
- src/App.tsx (implement ALL requested features with proper validation and error handling)

The App.tsx MUST include:
- Complete implementation of all requested features
- Proper form validation and error handling
- Loading states and success messages
- TypeScript types and interfaces
- Proper styling and layout
- Event handlers for all interactions
- Helpful comments explaining the code

Format:
{{
    "package.json": "content",
    "tsconfig.json": "content",
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
                
                # Stream each file
                required_files = [
                    "package.json",
                    "tsconfig.json",
                    "vite.config.ts",
                    "index.html",
                    "src/main.tsx",
                    "src/App.tsx"
                ]
                
                for file_path in required_files:
                    if file_path in files_content:
                        yield f"data: {json.dumps({'code': files_content[file_path], 'file': file_path})}\n\n"
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