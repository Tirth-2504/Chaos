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
    api_key = os.environ.get("FAL_KEY") or os.getenv("FAL_KEY")
    
    if not api_key:
        available_keys = list(os.environ.keys())
        raise HTTPException(
            status_code=500, 
            detail=f"Missing configuration: FAL_KEY variable not found. Keys: {available_keys}"
        )
    
    # Standard official endpoint for Flux Schnell
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
        
        # FIX: Correctly extract the image list array
        images_list = result.get("images", [])
        if not images_list:
            raise HTTPException(status_code=500, detail="The AI engine ran successfully but returned no images.")
            
        # FIX: Extract the dictionary safely out of the list array index
        first_image_object = images_list[0]
        image_url = first_image_object.get("url")
        
        return {"image_url": image_url}
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network communication failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)