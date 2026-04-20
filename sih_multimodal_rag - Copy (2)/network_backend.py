import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. Initialize the FastAPI app
app = FastAPI()

# 2. Configure CORS to allow your phone/second laptop to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (perfect for LAN testing)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],
)

# 3. Configure the Gemini API
# It is best practice to set this in your environment, but you can paste the key directly for quick testing.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB57iLgS5pJ-KcAFC6jeKlBXuxrKDh0z6o")
genai.configure(api_key=GEMINI_API_KEY)

# Use gemini-1.5-flash for the fastest, most cost-effective text responses
model = genai.GenerativeModel('gemini-1.5-flash')

# 4. Define the data structure we expect from your React frontend
class ChatRequest(BaseModel):
    message: str
    # If your frontend sends chat history, you can add it here:
    # history: list = [] 

# 5. Create the API Endpoint
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Generate the response using Gemini
        response = model.generate_content(request.message)
        
        # Return it in a simple JSON structure
        return {"reply": response.text}
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response from Gemini")

# Health check endpoint just to verify the server is running
@app.get("/")
async def root():
    return {"status": "Gemini Backend is running!"}