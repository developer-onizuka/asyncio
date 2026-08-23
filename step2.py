import os
import asyncio
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
async def mcp_agent(image_path: str) -> str:
    """Detects face coordinates from an image file path."""
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=local_model,
            tools=mcp_tools,
            system_prompt="与えられた画像から顔の座標数値のみを検出して返してください。説明文は不要です。"
        )
        # result = await agent.invoke_async(f"Detect face in: {image_path}")  # 削った元の行
        # return str(result)                                                 # 削った元の行
        
        # 変更: stream_async で受け取り、テキストを抽出しながら組み立てる
        text_result = ""
        async for event in agent.stream_async(f"Detect face in: {image_path}"):
            if isinstance(event, str):
                text_result += event
            elif isinstance(event, dict) and "event" in event:
                event_data = event["event"]
                if "contentBlockDelta" in event_data:
                    delta = event_data["contentBlockDelta"].get("delta", {})
                    if "text" in delta:
                        text_result += delta["text"]
        return text_result

@tool
async def reporter_agent(text: str) -> str:
    """Generates a summary report. Always pass the detection result string into the 'text' argument."""
    agent = Agent(
        model=local_model,
        system_prompt="You are a technical report writer. Write a simple markdown summary using the provided text input."
    )
    # result = await agent.invoke_async(f"Write a short inspection report for these face coordinates: {text}") # 削った元の行
    # return str(result)                                                                                      # 削った元の行
    
    # 変更: stream_async で受け取り、テキストを抽出しながら組み立てる
    text_result = ""
    async for event in agent.stream_async(f"Write a short inspection report for these face coordinates: {text}"):
        if isinstance(event, str): # LLM やフレームワークから流れてくるデータ型が揃っていないのをチェック
            text_result += event
        elif isinstance(event, dict) and "event" in event:
            event_data = event["event"]
            if "contentBlockDelta" in event_data:
                delta = event_data["contentBlockDelta"].get("delta", {})
                if "text" in delta:
                    text_result += delta["text"]
    return text_result

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

async def main():
    print("--- Step 2: Running Stream Test ---")
    
    # res = await orchestrator.invoke_async("/strands-agents-mcp/mcp/Bill.jpg")  # 削った元の行
    # print(res)                                                                 # 削った元の行
    
    # 変更: オーケストレーターの出力も stream_async でリアルタイム受信する
    stream = orchestrator.stream_async("/strands-agents-mcp/mcp/Bill.jpg")
    
    print("\n--- リアルタイム受信ログ ---")
    async for event in stream:
        # 流れてくるイベント（文字列や辞書オブジェクト）をそのままリアルタイム表示
        print(f"[STREAM EVENT]: {event}")

if __name__ == "__main__":
    asyncio.run(main())
