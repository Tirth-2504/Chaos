import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
def home():
    return {"status": "Server is up and running!"}

@app.post("/generate")
def generate_image(request: PromptRequest):
    # Try multiple ways Render stores variables to prevent environment reading errors
    api_key = os.environ.get("FAL_KEY") or os.getenv("FAL_KEY")
    
    # Strictly for testing: If it still fails, we output the available keys to see what Render is doing
    if not api_key:
        available_keys = list(os.environ.keys())
        raise HTTPException(
            status_code=500, 
            detail=f"Missing configuration: FAL_KEY environment variable is not found. Available keys detected by server: {available_keys}"
        )
    
    # FIX: Point exactly to the Flux Schnell endpoint queue
    api_url = "https://fal.run"
    headers = {
        "Authorization": f"Key {api_key.strip()}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": request.prompt,
        "image_size": "square_hd",
        "sync_mode": True,
        "num_inference_steps": 4
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"AI Engine Error: {response.text}")
            
        result = response.json()
        images = result.get("images", [])
        if not images:
            raise HTTPException(status_code=500, detail="The AI engine ran successfully but returned no image array.")
            
        # FIX: Correctly grab the URL from the first item in the image array list
        image_url = images[0].get("url")
        return {"image_url": image_url}
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network communication failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
