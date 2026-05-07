from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from agent import CodeAgent

app = FastAPI()

agent = CodeAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {
        "message": "Code Agent Running"
    }


@app.post("/chat")
def chat(req: ChatRequest):

    result = agent.run(req.message)

    return result
