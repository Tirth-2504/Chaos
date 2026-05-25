import os
import fal_client
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
    return {"status": "The Python server is fully functional!"}

@app.post("/generate")
def generate_image(request: PromptRequest):
    if not os.environ.get("FAL_KEY") and not os.getenv("FAL_KEY"):
        raise HTTPException(status_code=500, detail="Configuration Error: FAL_KEY variable was not found on Render.")

    try:
        result = fal_client.subscribe(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": request.prompt,
                "image_size": "square_hd",
                "num_inference_steps": 4,
                "sync_mode": True
            }
        )
        
        # SAFELY EXTRACT ARRAY: Fal.ai returns {"images": [{"url": "..."}]}
        images_list = result.get("images", [])
        if not images_list or not isinstance(images_list, list):
            raise HTTPException(status_code=500, detail=f"Data structure error. Got raw result: {result}")
            
        # Extract the dictionary out of the first index position of the array list
        first_image_object = images_list[0]
        image_url = first_image_object.get("url")
        
        return {"image_url": image_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"The AI Engine threw an error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
