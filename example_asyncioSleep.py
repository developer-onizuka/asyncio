import asyncio

async def main():
    # サブタスク1の定義
    async def sub_task1():
        print('サブタスク1 ...')
        # 【タイマーを数える人】：イベントループ（OSの非同期タイマーを利用）
        # 【CPUの状態】：Pythonは解放され、待機中に「イベントループが」他のタスクのコードを実行できる
        # ➔ その結果、サブタスク1の待ち時間中にサブタスク2が動き、2つのタスクがほぼ同時に1秒で完了する。
        await asyncio.sleep(1)
        print('... サブタスク1 Done!')

    # サブタスク2の定義
    async def sub_task2():
        print('サブタスク2 ...')
        await asyncio.sleep(1)
        print('... サブタスク2 Done!')

    # 2つのタスクを作成して同時にスタートさせる
    task1 = asyncio.create_task(sub_task1())
    task2 = asyncio.create_task(sub_task2())

    # 両方のタスクが終わるのを待つ
    await task1
    await task2

# mainだけを実行
asyncio.run(main())
