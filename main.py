import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Configures CORS so your frontend can communicate securely with the server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits access from all browsers/domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defines what data the server expects to receive from the frontend
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
def generate_image(request: PromptRequest):
    # Grabs your secret key from your system environment settings
    api_key = os.environ.get("FAL_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing configuration: FAL_KEY environment variable is not set.")
    
    # We use Flux Schnell for lightning-fast, high-detail pro images
    api_url = "https://fal.run"
    headers = {
        "Authorization": f"Key {api_key}",
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
        
        # Pulls out the image URL from the AI response payload
        images = result.get("images", [])
        if not images:
            raise HTTPException(status_code=500, detail="The AI engine ran successfully but returned no image array.")
            
        image_url = images[0].get("url")
        return {"image_url": image_url}
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network communication failed: {str(e)}")

# This helps the hosting company know how to start the app server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
