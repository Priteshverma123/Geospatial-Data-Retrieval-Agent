from fastapi.responses import FileResponse, Response
import logging ,os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import List
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# from nemoguardrails import LLMRails
from pydantic import BaseModel
from  utils.config import config, load_env_variables
from  providers.llm import get_llm_model
from  tools.llm_function import agent_hybrid_retriever
from  tools.marketing import marketing_main
env_name = load_env_variables()


# Set logging level to ERROR to suppress warnings
logging.getLogger("langchain_core").setLevel(logging.ERROR)
logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)


# adding guardrails configs
# guardrails_llm = LLMRails(config=guardrails_config)

# Initialize FastAPI app
app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to allow specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LLM_PROVIDER= config[env_name].LLM_PROVIDER
LLM_MODEL_NAME= config[env_name].LLM_MODEL_NAME
TEMPERATURE= config[env_name].TEMPERATURE
class RetrievalRequest(BaseModel):
    query: str


# Initialize global variables
question_global = None


@app.get("/")
async def hello_world():
    return "Hello, Graph RAG llm-service with fastapi!"


@app.post("/api/agent", response_class=JSONResponse)
async def ask_agentic_question(
        request: RetrievalRequest):
    data = {
        "query": request.query,
    }
    global question_global  # Declare global variables
    question_global = data["query"]
    selected_llm_model = get_llm_model("openai", "gpt-4o", 0)
    ai_response = await agent_hybrid_retriever(data["query"], selected_llm_model)
    return ai_response


SATELLITE_IMAGE_PATH = "./satellite_image.jpg"

@app.get("/api/satellite-image")
async def get_satellite_image():
    if not os.path.exists(SATELLITE_IMAGE_PATH):
        raise HTTPException(status_code=404, detail="Satellite image not found")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return FileResponse(
        SATELLITE_IMAGE_PATH,
        media_type="image/jpeg",
        filename="satellite_image.jpg",
        headers=headers
    )


UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/generate-email")
async def generate_email(
    files: List[UploadFile] = File(...),
    topic: str = Form(...),
    recipient_type: str = Form(...)
):
    file_paths = []
    
    for file in files:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())  # Read and save file
        file_paths.append(file_location)
    
    return marketing_main(file_paths, topic, recipient_type)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
