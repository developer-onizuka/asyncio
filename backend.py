import os
import asyncio
from typing import Optional
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

# ------------------------------------------------------------------
# サブエージェントごとのキュー参照を保持するクラスとインスタンス
# ------------------------------------------------------------------
class SubAgentState:
    def __init__(self):
        self.queue: Optional[asyncio.Queue] = None

_mcp_state = SubAgentState()
_reporter_state = SubAgentState()

# ------------------------------------------------------------------
# サブエージェントからキューへ進捗イベントを投入する関数
# ------------------------------------------------------------------
async def send_event(queue: Optional[asyncio.Queue], message: str, stage: str, data: str = ""):
    if not queue:
        return
    progress = {"message": message, "stage": stage, "data": data}
    await queue.put({"event": {"subAgentProgress": progress}})

# ------------------------------------------------------------------
# 親ストリームと子キューを非同期で統合（合流）して出力する関数
# ------------------------------------------------------------------
async def merge_streams(stream, queue: asyncio.Queue):
    create_task = asyncio.create_task
    orchestrator_task = create_task(anext(stream, None))
    tools_task = create_task(queue.get())
    waiting = {orchestrator_task, tools_task}
    
    while waiting:
        done, waiting = await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
        for completed in done:
            if completed == orchestrator_task:
                event = completed.result()
                if event is not None:
                    yield event
                    orchestrator_task = create_task(anext(stream, None))
                    waiting.add(orchestrator_task)
                else:
                    orchestrator_task = None
            
            elif completed == tools_task:
                try:
                    tools_event = completed.result()
                    yield tools_event
                    tools_task = create_task(queue.get())
                    waiting.add(tools_task)
                except Exception:
                    tools_task = None
        
        if orchestrator_task is None and queue.empty():
            break

@tool
async def mcp_agent(image_path: str) -> str:
    """Detects face coordinates from an image file path."""
    queue = _mcp_state.queue
    await send_event(queue, "顔検出エージェント (mcp_agent) 開始", "start")
    
    try:
        with mcp_client:
            mcp_tools = mcp_client.list_tools_sync()
            agent = Agent(
                model=local_model,
                tools=mcp_tools,
                system_prompt="与えられた画像から顔の座標数値のみを検出して返してください。説明文は不要です。"
            )
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
                        
            await send_event(queue, "顔検出処理が完了しました", "complete", data=text_result)
            return text_result
    except Exception as e:
        await send_event(queue, f"顔検出エラー: {str(e)}", "error")
        raise e

@tool
async def reporter_agent(text: str) -> str:
    """Generates a summary report. Always pass the detection result string into the 'text' argument."""
    queue = _reporter_state.queue
    await send_event(queue, "レポート生成エージェント (reporter_agent) 開始", "start")
    
    agent = Agent(
        model=local_model,
        system_prompt="You are a technical report writer. Write a simple markdown summary using the provided text input."
    )
    text_result = ""
    async for event in agent.stream_async(f"Write a short inspection report for these face coordinates: {text}"):
        if isinstance(event, str):
            text_result += event
        elif isinstance(event, dict) and "event" in event:
            event_data = event["event"]
            if "contentBlockDelta" in event_data:
                delta = event_data["contentBlockDelta"].get("delta", {})
                if "text" in delta:
                    text_result += delta["text"]
                    
    await send_event(queue, "レポート生成が完了しました", "complete", data=text_result)
    return text_result

ORCHESTRATOR_SYSTEM_PROMPT = """You are a precise task orchestrator.
STRICT INSTRUCTIONS:
Step 1: Call `mcp_agent` with the image file path.
Step 2: Take the output string from `mcp_agent` and pass it directly to `reporter_agent` using parameter 'text'.
Step 3: Output the final markdown report from `reporter_agent`.
"""

orchestrator = Agent(
    model=local_model,
    tools=[mcp_agent, reporter_agent],
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT
)

async def agent_stream(image_path: str):
    """共有キューを初期化し、統合ストリームを yield する"""
    queue = asyncio.Queue()
    _mcp_state.queue = queue
    _reporter_state.queue = queue
    
    stream = orchestrator.stream_async(image_path)
    
    async for event in merge_streams(stream, queue):
        yield event
