import os
import asyncio  # 追加: 非同期制御ライブラリ
from strands import Agent, tool
from strands.models import OllamaModel
from strands.tools.mcp import MCPClient
from mcp.client.sse import sse_client

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://192.168.33.3:5001/sse")

mcp_client = MCPClient(
    lambda: sse_client(MCP_SERVER_URL)
)

local_model = OllamaModel(
    host="http://svc-ollama:11434",
    model_id="llama3.2:3b",
    options={
        "temperature": 0.0
    }
)

@tool
# def mcp_agent(image_path: str) -> str:  # 削った元の行
async def mcp_agent(image_path: str) -> str:  # async を追加
    """Detects face coordinates from an image file path."""
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=local_model,
            tools=mcp_tools,
            system_prompt="与えられた画像から顔の座標数値のみを検出して返してください。説明文は不要です。"
        )
        # result = agent(f"Detect face in: {image_path}")  # 削った元の行
        result = await agent.invoke_async(f"Detect face in: {image_path}")  # await と invoke_async に変更
        return str(result)

@tool
# def reporter_agent(text: str) -> str:  # 削った元の行
async def reporter_agent(text: str) -> str:  # async を追加
    """Generates a summary report. Always pass the detection result string into the 'text' argument."""
    agent = Agent(
        model=local_model,
        system_prompt="You are a technical report writer. Write a simple markdown summary using the provided text input."
    )
    # result = agent(f"Write a short inspection report for these face coordinates: {text}")  # 削った元の行
    result = await agent.invoke_async(f"Write a short inspection report for these face coordinates: {text}")  # await と invoke_async に変更
    return str(result)

ORCHESTRATOR_SYSTEM_PROMPT = """You are a precise task orchestrator.
STRICT INSTRUCTIONS:
Step 1: Call `mcp_agent` with the image file path.
Step 2: Take the output string from `mcp_agent` and pass it directly to `reporter_agent` using parameter 'text'.
Step 3: Return the final text from `reporter_agent`.
"""

orchestrator = Agent(
    model=local_model,
    tools=[mcp_agent, reporter_agent],
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT
)

# 追記: 非同期のメイン関数を作成
async def main():
    print("--- Running Multi-Agent Async Test ---")
    # res = orchestrator("/strands-agents-mcp/mcp/Bill.jpg")  # 削った元の行
    res = await orchestrator.invoke_async("/strands-agents-mcp/mcp/Bill.jpg")  # await と invoke_async に変更
    print("\n================ FINAL OUTPUT ================")
    print(res)

if __name__ == "__main__":
    # print("--- Running Multi-Agent Test ---")  # 削った元の行
    # res = orchestrator("/strands-agents-mcp/mcp/Bill.jpg")  # 削った元の行
    # ...                                                     # 削った元の行
    
    asyncio.run(main())  # イベントループ（非同期環境）を起動して実行
