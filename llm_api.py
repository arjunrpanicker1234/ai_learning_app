from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

@app.route('/api/generate', methods=['POST'])
def generate_response():
    data = request.get_json()

    # Extract prompt and model from request
    prompt = data.get('prompt', '')
    model = data.get('model', 'llama3')
    
    # Simulate LLM response (this is just a mock; replace with actual logic if needed)
    response = {
        "response": f"This is a generated response based on the prompt: '{prompt}' using model '{model}'."
    }
    return jsonify(response)

@app.route('/')
def home():
    return "LLM API Server is running!"

if __name__ == '__main__':
    # Run server on port 11434 to match your Config setup
    app.run(host='0.0.0.0', port=11434, debug=True)
