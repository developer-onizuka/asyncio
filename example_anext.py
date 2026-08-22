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

# 直列実行（1つずつ終わるのを待つ ➔ 計8.0秒）
async def main_serial():
    print("--- 直列実行 (async) ---")
    
    # ステップ1：クラスをインスタンス化
    streamer1 = Streamer("Hello1", "World1")
    streamer2 = Streamer("Hello2", "World2")

    # ステップ2：インスタンスからジェネレータ（ストリーム）を生成
    s1 = streamer1.generate()
    s2 = streamer2.generate()

    start = time.time()

    # s1 の処理（4秒）が終わった後に s2 の処理（4秒）が始まる
    print(await anext(s1))  # Hello1 (2秒)
    print(await anext(s1))  # World1 (2秒)
    print(await anext(s2))  # Hello2 (2秒)
    print(await anext(s2))  # World2 (2秒)

    print(f"直列の所要時間: {time.time() - start:.1f}秒\n")

# 並行実行（s1 と s2 を同時に動かす ➔ 計4.0秒）
async def main_parallel():
    print("--- 並行実行 (async + Task) ---")
    
    # ステップ1：クラスをインスタンス化
    streamer1 = Streamer("Hello1", "World1")
    streamer2 = Streamer("Hello2", "World2")

    # ステップ2：インスタンスからジェネレータ（ストリーム）を生成
    s1 = streamer1.generate()
    s2 = streamer2.generate()

    start = time.time()

    # 1つ目の値の取り出しを同時にスタート（2秒）
    t1 = asyncio.create_task(anext(s1))
    t2 = asyncio.create_task(anext(s2))
    print(await t1)  # Hello1
    print(await t2)  # Hello2

    # 2つ目の値の取り出しを同時にスタート（2秒）
    t3 = asyncio.create_task(anext(s1))
    t4 = asyncio.create_task(anext(s2))
    print(await t3)  # World1
    print(await t4)  # World2

    print(f"並行の所要時間: {time.time() - start:.1f}秒\n")

async def main():
    await main_serial()
    await main_parallel()

asyncio.run(main())
