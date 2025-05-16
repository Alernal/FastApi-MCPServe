from fastapi import FastAPI
from gemini.gemini_client import generate_content_from_gemini
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel

app = FastAPI()

class ChatMessage(BaseModel):
    message: str
    user_id: int

@app.post("/assistant")
async def chat_with_gemini(message: ChatMessage):
    response = await generate_content_from_gemini(message.message, message.user_id)
    return {"response": response}

mcp = FastApiMCP(
    app,
    name="MCPFastAPI",
    include_operations=["get_weather_country"],
    description="MCP server for my weather API",
    describe_all_responses=True,
    describe_full_response_schema=True,
)

mcp.mount()