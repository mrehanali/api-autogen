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
    developer = autogen.AssistantAgent(
        name="developer",
        system_message="""You are a skilled React developer who generates complete React applications.
Your response must be ONLY a JSON object containing ALL the necessary files with their complete content.
You MUST implement all the features requested by the user in the description using a proper project structure.
Focus on functionality and structure, the designer agent will enhance the styling later.

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
1. src/pages/: Page components based on requirements
2. src/components/: Only create components needed for the requirements
3. src/styles/: Basic styling structure
4. src/hooks/: Custom hooks based on requirements
5. src/utils/: Only create utilities needed for the requirements
6. src/types/: TypeScript interfaces for the requirements
7. src/services/: API integration if needed
8. src/context/: Context providers only if state management is needed

Technical requirements:
- Use TypeScript with strict type checking
- Follow React best practices and hooks
- Implement proper error handling
- Production-ready code with error boundaries
- Proper file organization

DO NOT focus too much on styling as the designer agent will enhance it later.""",
        llm_config=llm_config
    )

    designer = autogen.AssistantAgent(
        name="designer",
        system_message="""You are a skilled UI/UX designer who enhances React components with beautiful, modern styling.
You will receive a JSON object containing React files and enhance their styling while maintaining functionality.

Focus on:
1. Modern, clean design
2. Responsive layouts
3. Proper spacing and typography
4. Color schemes and visual hierarchy
5. Micro-interactions and hover states
6. Loading states and transitions
7. Error state styling
8. Accessibility considerations

Guidelines:
- Use CSS-in-JS or CSS modules for styling
- Implement responsive design patterns
- Add subtle animations and transitions
- Ensure consistent spacing and alignment
- Use modern color schemes
- Add hover and active states
- Style form elements professionally
- Include loading and error states
- Make components visually appealing

Your response must be ONLY a JSON object with the enhanced files.""",
        llm_config=llm_config
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        code_execution_config=False,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0
    )
    
    # First, get the developer to create the base application
    chat_response = user_proxy.initiate_chat(
        developer,
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
- Basic styling structure
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
    
    # Get the developer's response
    dev_messages = chat_response.chat_history
    if not (dev_messages and len(dev_messages) >= 2 and isinstance(dev_messages[-1], dict) and "content" in dev_messages[-1]):
        return {"content": None}
    
    dev_content = dev_messages[-1]["content"]
    
    # Now, have the designer enhance the styling
    chat_response = user_proxy.initiate_chat(
        designer,
        message=f"""Enhance the styling of these React components while maintaining their functionality: 

{dev_content}

Focus on:
1. Modern, clean design
2. Responsive layouts
3. Proper spacing and typography
4. Color schemes
5. Hover states and transitions
6. Loading and error states
7. Visual hierarchy
8. Accessibility

RESPOND WITH ONLY THE ENHANCED JSON OBJECT.
NO additional text or explanations.""",
        clear_history=True
    )
    
    # Get the designer's response
    design_messages = chat_response.chat_history
    if design_messages and len(design_messages) >= 2:
        last_message = design_messages[-1]
        if isinstance(last_message, dict) and "content" in last_message:
            return {"content": last_message["content"]}
    
    return {"content": dev_content}  # Fallback to developer's content if designer fails

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