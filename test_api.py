import requests
import json

def test_generate_code():
    url = "http://localhost:8000/generate-code"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "description": "Create a simple login form with email and password fields, with validation and a submit button."
    }
    
    response = requests.post(url, headers=headers, json=data, stream=True)
    
    for line in response.iter_lines():
        if line:
            # Remove "data: " prefix and decode
            line = line.decode('utf-8')
            
            # Handle ping events
            if line.startswith(": ping"):
                print(line)
                continue
                
            if line.startswith("data: "):
                line = line.replace("data: ", "")
                try:
                    data = json.loads(line)
                    if "file" in data and "code" in data:
                        print(f"\nFile: {data['file']}")
                        print("Content:")
                        print(data['code'][:200] + "..." if len(data['code']) > 200 else data['code'])
                        print("-" * 80)
                except json.JSONDecodeError:
                    print("Failed to parse JSON:", line)

if __name__ == "__main__":
    test_generate_code() 