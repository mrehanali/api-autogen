# AI-Powered Front-end Generator

This is a FastAPI-based backend service that transforms natural language descriptions into React-based front-end code using AutoGen with streaming response. It implements a two-agent workflow for development and review.

## Features

- Single REST API endpoint accepting natural language UI descriptions
- Streaming response for real-time code generation feedback
- Two-agent workflow with Developer and Reviewer agents
- React components with Tailwind CSS generation
- Basic responsive design implementation

## Prerequisites

- Python 3.8+
- OpenAI API key

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd api-autogen
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file and add your OpenAI API key and other configurations:
```
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4-1106-preview
TEMPERATURE_DEVELOPER=0.7
TEMPERATURE_REVIEWER=0.4
REQUEST_TIMEOUT=600
```

## Running the Application

Start the FastAPI server with:
```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

## API Endpoints

### Generate Code
- **URL**: `/generate-code`
- **Method**: `POST`
- **Request Body**:
```json
{
    "description": "string"
}
```
- **Response**: Server-Sent Events (SSE) stream with the following format:
```json
{
    "code": "string",
    "status": "string",
    "review_feedback": "string"
}
```

### Health Check
- **URL**: `/health`
- **Method**: `GET`
- **Response**:
```json
{
    "status": "healthy"
}
```

## Documentation

API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

The API includes proper error handling for:
- Empty descriptions
- Invalid requests
- OpenAI API issues
- Code generation failures

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 