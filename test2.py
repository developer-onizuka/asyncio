import asyncio

# 1. 子タスク：パスタを茹でる
async def boil_pasta(queue: asyncio.Queue):
    print('      【ステップ13】 await queue.put("  [0分] 🍝 パスタを鍋に投入！")')
    await queue.put("  [0分] 🍝 パスタを鍋に投入！")
    
    print('      【ステップ14】 await asyncio.sleep(8.0)')
    await asyncio.sleep(8.0) # 8分間茹でる
    
    print('      【ステップ25】 await queue.put("  [8分] ⏰ パスタが茹であがりました！")')
    await queue.put("  [8分] ⏰ パスタが茹であがりました！")


# 2. 親タスク：ソースを作る
async def cook_sauce(queue: asyncio.Queue):
    print('    【ステップ6】 yield "[0分] 1. お湯を沸かしてパスタを投下"')
    yield "[0分] 1. お湯を沸かしてパスタを投下"
    
    print('    【ステップ11】 asyncio.create_task(boil_pasta(queue))')
    pasta_task = asyncio.create_task(boil_pasta(queue))
    
    print('    【ステップ12】 await asyncio.sleep(3.0)')
    await asyncio.sleep(3.0) # 3分間切る
    
    print('    【ステップ19】 yield "[3分] 2. ニンニクを弱火で炒める"')
    yield "[3分] 2. ニンニクを弱火で炒める"
    
    print('    【ステップ24】 await asyncio.sleep(7.0)')
    await asyncio.sleep(7.0) # 7分間煮込む
    await pasta_task # ソース完成直前にバックグラウンドタスクの完了を待機
    
    print('    【ステップ30】 yield "[10分] 3. ソースとパスタを和えて完成！"')
    yield "[10分] 3. ソースとパスタを和えて完成！"
    
    print('    【ステップ35】 (cook_sauce generator completed / StopAsyncIteration)')


# 3. どちらのメッセージも届いた瞬間に即時出力する
async def merge(stream, queue: asyncio.Queue):
    print('  [merge] 【ステップ3】 main_task = asyncio.create_task(anext(stream, None))')
    main_task = asyncio.create_task(anext(stream, None))
    
    print('  [merge] 【ステップ4】 queue_task = asyncio.create_task(queue.get())')
    queue_task = asyncio.create_task(queue.get())
    
    waiting = {main_task, queue_task}
    wait_count = 1

    while waiting:
        if wait_count == 1:
            print('  [merge] 【ステップ5】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)')
        elif wait_count == 2:
            print('  [merge] 【ステップ10】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)')
        elif wait_count == 3:
            print('  [merge] 【ステップ18】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)')
        elif wait_count == 4:
            print('  [merge] 【ステップ23】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)')
        elif wait_count == 5:
            print('  [merge] 【ステップ29】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)')
        elif wait_count == 6:
            print('  [merge] 【ステップ34】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)')
        
        wait_count += 1
        done, waiting = await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
        
        for completed in done:
            # --- main_task 側の処理 ---
            if completed == main_task:
                event = completed.result()
                if event is None:
                    print('  [merge] 【ステップ36】 if event is None:')
                    while not queue.empty():
                        yield await queue.get()
                    print('  [merge] 【ステップ37】 queue_task.cancel()')
                    queue_task.cancel()
                    print('  [merge] 【ステップ38】 return (merge完了)')
                    return
                else:
                    if event.startswith("[0分]"):
                        print('  [merge] 【ステップ7】 if completed == main_task:')
                        print(f'  [merge] 【ステップ8】 yield "{event}"')
                        yield event
                        print('  [merge] 【ステップ9】 main_task = asyncio.create_task(anext(stream, None))')
                    elif event.startswith("[3分]"):
                        print('  [merge] 【ステップ20】 if completed == main_task:')
                        print(f'  [merge] 【ステップ21】 yield "{event}"')
                        yield event
                        print('  [merge] 【ステップ22】 main_task = asyncio.create_task(anext(stream, None))')
                    elif event.startswith("[10分]"):
                        print('  [merge] 【ステップ31】 if completed == main_task:')
                        print(f'  [merge] 【ステップ32】 yield "{event}"')
                        yield event
                        print('  [merge] 【ステップ33】 main_task = asyncio.create_task(anext(stream, None))')
                    
                    main_task = asyncio.create_task(anext(stream, None))
                    waiting.add(main_task)

            # --- queue_task 側の処理 ---
            elif completed == queue_task:
                res = completed.result()
                if "パスタを鍋に投入" in res:
                    print('  [merge] 【ステップ15】 elif completed == queue_task:')
                    print(f'  [merge] 【ステップ16】 yield completed.result()  # "{res.strip()}"')
                    yield res
                    print('  [merge] 【ステップ17】 queue_task = asyncio.create_task(queue.get())')
                elif "パスタが茹であがり" in res:
                    print('  [merge] 【ステップ26】 elif completed == queue_task:')
                    print(f'  [merge] 【ステップ27】 yield completed.result()  # "{res.strip()}"')
                    yield res
                    print('  [merge] 【ステップ28】 queue_task = asyncio.create_task(queue.get())')

                queue_task = asyncio.create_task(queue.get())
                waiting.add(queue_task)


# 実行
async def main():
    print('【ステップ1】 q = asyncio.Queue()')
    q = asyncio.Queue()
    gen = cook_sauce(q) # ストリームを明示的にインスタンス化
    print('【ステップ2】 async for msg in merge(gen, q):')
    async for msg in merge(cook_sauce(q), q):
        pass

asyncio.run(main())
