import asyncio
import streamlit as st
from backend import agent_stream

st.set_page_config(page_title="Strands Multi-Agent System", layout="wide")
st.title("🤖 Strands Async Multi-Agent System")

image_path = st.text_input(
    "画像パスを入力してください:", 
    value="/strands-agents-mcp/mcp/Bill.jpg"
)

async def run_pipeline(path: str, status_area, report_area):
    with status_area.status("エージェントオーケストレーション実行中...", expanded=True) as status:
        async for event in agent_stream(path):
            
            if isinstance(event, dict) and "event" in event and "subAgentProgress" in event["event"]:
                progress = event["event"]["subAgentProgress"]
                msg = progress.get("message", "")
                stage = progress.get("stage", "")
                data = progress.get("data", "")
                
                if stage == "start":
                    st.write(f"⏳ **{msg}**")
                elif stage == "complete":
                    st.write(f"✅ **{msg}**")
                    if data and "レポート生成" in msg:
                        # Markdownとして綺麗に整形・描画
                        report_area.markdown(data)
                elif stage == "error":
                    st.write(f"❌ **{msg}**")

        status.update(label="すべての処理が完了しました！", state="complete", expanded=False)

if st.button("実行開始", type="primary"):
    status_container = st.empty()
    st.subheader("📋 最終レポート出力")
    # マークダウン装飾用の枠を作成
    report_container = st.container(border=True)

    asyncio.run(run_pipeline(image_path, status_container, report_container))
