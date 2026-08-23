import os
import asyncio
from typing import Optional  # 【追加】型定義用
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
# 【追加】サブエージェントごとのキュー参照を保持するクラスとインスタンス
# ------------------------------------------------------------------
class SubAgentState:
    def __init__(self):
        self.queue: Optional[asyncio.Queue] = None

_mcp_state = SubAgentState()
_reporter_state = SubAgentState()

# ------------------------------------------------------------------
# 【追加】サブエージェントからキューへ進捗イベントを投入する関数
# ------------------------------------------------------------------
async def send_event(queue: Optional[asyncio.Queue], message: str, stage: str):
    if not queue:
        return
    progress = {"message": message, "stage": stage}
    await queue.put({"event": {"subAgentProgress": progress}})

# ------------------------------------------------------------------
# 【追加】親ストリームと子キューを非同期で統合（合流）して出力する関数
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
    queue = _mcp_state.queue  # 【追加】共有キューの取得
    await send_event(queue, "顔検出エージェント (mcp_agent) 開始", "start")  # 【追加】開始通知をキューへ送信
    
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=local_model,
            tools=mcp_tools,
            system_prompt="与えられた画像から顔の座標数値のみを検出して返してください。説明文は不要です。"
        )
        text_result = ""
        async for event in agent.stream_async(f"Detect face in: {image_path}"):
            if isinstance(event, str): # LLM やフレームワークから流れてくるデータ型が揃っていないのをチェック
                text_result += event
            elif isinstance(event, dict) and "event" in event:
                event_data = event["event"]
                if "contentBlockDelta" in event_data:
                    delta = event_data["contentBlockDelta"].get("delta", {})
                    if "text" in delta:
                        text_result += delta["text"]
                        
        await send_event(queue, "顔検出処理が完了しました", "complete")  # 【追加】完了通知をキューへ送信
        return text_result

@tool
async def reporter_agent(text: str) -> str:
    """Generates a summary report. Always pass the detection result string into the 'text' argument."""
    queue = _reporter_state.queue  # 【追加】共有キューの取得
    await send_event(queue, "レポート生成エージェント (reporter_agent) 開始", "start")  # 【追加】開始通知をキューへ送信
    
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
                    
    await send_event(queue, "レポート生成が完了しました", "complete")  # 【追加】完了通知をキューへ送信
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
    # print("--- Step 2: Running Stream Test ---")  # 【削除】Step 2 の表示
    print("--- Step 3: Stream Merge Test ---")     # 【追加】Step 3 の表示
    
    # 【追加】共有キューのインスタンス化と状態変数へのセット
    queue = asyncio.Queue()
    _mcp_state.queue = queue
    _reporter_state.queue = queue
    
    stream = orchestrator.stream_async("/strands-agents-mcp/mcp/Bill.jpg")
    
    # print("\n--- リアルタイム受信ログ ---")  # 【削除】
    # async for event in stream:             # 【削除】Step 2 の単一ストリーム受信
    #     print(f"[STREAM EVENT]: {event}")  # 【削除】

    print("\n--- 結合ストリーム（親のイベント＋子の Queue 通知）---")  # 【追加】
    # 【追加】merge_streams を通して親と子のイベントを合流して出力
    async for merged_event in merge_streams(stream, queue):
        print(f"[MERGED EVENT]: {merged_event}")

if __name__ == "__main__":
    asyncio.run(main())
