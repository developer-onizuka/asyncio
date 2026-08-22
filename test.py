import asyncio

# 1. 子タスク：パスタを茹でる
async def boil_pasta(queue: asyncio.Queue):
    await queue.put("  [0分] 🍝 パスタを鍋に投入！")
    await asyncio.sleep(8.0)  # 8分間茹でる
    await queue.put("  [8分] ⏰ パスタが茹であがりました！")

# 2. 親タスク：ソースを作る
async def cook_sauce(queue: asyncio.Queue):
    yield "[0分] 1. お湯を沸かしてパスタを投下"
    
    # バックグラウンドでパスタの処理を開始
    pasta_task = asyncio.create_task(boil_pasta(queue))
    
    await asyncio.sleep(3.0)  # 3分間切る
    yield "[3分] 2. ニンニクを弱火で炒める"
    
    await asyncio.sleep(7.0)  # 7分間煮込む
    
    # 【追加】ソース完成直前にバックグラウンドタスクの完了を待機
    # 8分時点で既に茹で上がっているため追加待ち時間は発生せず、例外発生時のキャッチも可能になります
    await pasta_task
    
    yield "[10分] 3. ソースとパスタを和えて完成！"

# 3. どちらのメッセージも届いた瞬間に即時出力する
async def merge(stream, queue: asyncio.Queue):
    main_task = asyncio.create_task(anext(stream, None))
    queue_task = asyncio.create_task(queue.get())
    waiting = {main_task, queue_task}

    while waiting:
        done, waiting = await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
        for completed in done:
            if completed == main_task:
                event = completed.result()
                if event is None:
                    # ストリームが終了したら残りの Queue をすべて取り出して終了
                    while not queue.empty():
                        yield await queue.get()
                    
                    # 待機中の queue_task を安全にキャンセル
                    queue_task.cancel()
                    try:
                        await queue_task
                    except asyncio.CancelledError:
                        pass
                    return
                else:
                    yield event
                    main_task = asyncio.create_task(anext(stream, None))
                    waiting.add(main_task)

            elif completed == queue_task:
                yield completed.result()
                queue_task = asyncio.create_task(queue.get())
                waiting.add(queue_task)

# 実行
async def main():
    q = asyncio.Queue()
    async for msg in merge(cook_sauce(q), q):
        print(msg)

asyncio.run(main())
