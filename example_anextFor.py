import asyncio
import time

# クラス定義：初期化時に出力データを設定する
class Streamer:
    def __init__(self, first_msg, second_msg):
        self.first_msg = first_msg
        self.second_msg = second_msg

    # 非同期ジェネレータメソッド
    async def generate(self):
        await asyncio.sleep(2.0)
        yield self.first_msg
        await asyncio.sleep(2.0)
        yield self.second_msg

# 直列実行（async for を順番に回す ➔ 計8.0秒）
async def main_serial():
    print("--- 直列実行（async for）---")
    
    streamer1 = Streamer("Hello1", "World1")
    streamer2 = Streamer("Hello2", "World2")

    start = time.time()

    # streamer1 の async for が完全に終わる（4秒）まで streamer2 に進まない
    async for msg in streamer1.generate():
        print(msg)  # Hello1 ➔ World1
        
    async for msg in streamer2.generate():
        print(msg)  # Hello2 ➔ World2

    print(f"直列の所要時間: {time.time() - start:.1f}秒\n")


# 並行処理用：1つのストリームを最後まで async for で処理する作業関数
async def process_stream(streamer):
    async for msg in streamer.generate():
        print(msg)

# 並行実行（async for 全体をタスク化して同時に動かす ➔ 計4.0秒）
async def main_parallel():
    print("--- 並行実行（async for + Task）---")
    
    streamer1 = Streamer("Hello1", "World1")
    streamer2 = Streamer("Hello2", "World2")

    start = time.time()

    # async for のループ処理全体を create_task で同時にスタート！
    task1 = asyncio.create_task(process_stream(streamer1))
    task2 = asyncio.create_task(process_stream(streamer2))

    # 2つのループが並行して進むのを待つ
    await task1
    await task2

    print(f"並行の所要時間: {time.time() - start:.1f}秒\n")

async def main():
    await main_serial()
    await main_parallel()

asyncio.run(main())

#async def stream():
#    yield "Hello"
#    yield "World"
#
#async def main():
#    # 2. インスタンス化して変数 s に保持
#    s = stream()
#
#    # 3. anext() や create_task() を使わず、async for ループで順に取り出す
#    async for item in s:
#        print(item)
#
#asyncio.run(main())
