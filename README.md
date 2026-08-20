```mermaid
sequenceDiagram
    autonumber
    participant EvLoop as イベントループ
    participant Main as main()
    participant Merge as merge()
    participant Sauce as cook_sauce()
    participant Pasta as boil_pasta()
    participant Queue as asyncio.Queue

    Main->>EvLoop: merge() の実行を要求
    
    rect rgb(240, 240, 255)
    note over Merge, Pasta: [0分] 初期起動＆タスク登録
    EvLoop->>Merge: 処理を開始
    Merge->>EvLoop: create_task(anext) & create_task(queue.get) を登録
    Merge->>EvLoop: 1. await wait() ➔ 「完了まで一時停止し、制御を返す」
    
    EvLoop->>Sauce: 2. 制御を渡して初回実行を開始 (anext/cook_sauce)
    Sauce-->>Merge: yield "[0分] 1. お湯を沸かして..."
    Sauce->>EvLoop: create_task(boil_pasta) を登録
    Sauce->>EvLoop: 3. await sleep(3.0) ➔ 「3秒タイマーセット＆制御を返す」
    
    EvLoop->>Pasta: 4. 制御を渡して初回実行を開始 (boil_pasta)
    Pasta->>Queue: await queue.put(...) ➔ イベントループ経由でキューへ格納
    Queue-->>EvLoop: 格納完了
    Pasta->>EvLoop: 5. await sleep(8.0) ➔ 「8秒タイマーセット＆制御を返す」
    
    EvLoop->>Merge: 6. wait が条件を満たしたため制御を渡して再開
    Merge-->>Main: yield "[0分] 1. お湯を沸かして..."
    Merge->>Queue: queue.get() から「パスタ投入」を取得
    Merge-->>Main: yield "  [0分] 🍝 パスタを鍋に投入！"
    Merge->>EvLoop: 7. await wait() ➔ 「次の完了まで一時停止（制御を返す）」
    end

    rect rgb(255, 240, 240)
    note over Sauce, Merge: [3分経過] ソース側のタイマー満了
    EvLoop->>Sauce: 8. 3秒経過！制御を渡して再開
    Sauce-->>Merge: yield "[3分] 2. ニンニクを弱火で炒める"
    Sauce->>EvLoop: 9. await sleep(7.0) ➔ 「7秒タイマーセット＆制御を返す」
    
    EvLoop->>Merge: 10. wait 完了のため制御を渡して再開
    Merge-->>Main: yield "[3分] 2. ニンニクを弱火で炒める"
    Merge->>EvLoop: 11. await wait() ➔ 「次の完了まで一時停止（制御を返す）」
    end

    rect rgb(240, 255, 240)
    note over Pasta, Merge: [8分経過] パスタ側のタイマー満了
    EvLoop->>Pasta: 12. 8秒経過！制御を渡して再開
    Pasta->>Queue: await queue.put(...) ➔ イベントループ経由でキューへ格納
    Pasta->>EvLoop: 13. 処理終了 (制御を返す)
    
    EvLoop->>Merge: 14. wait(get) 完了のため制御を渡して再開
    Merge->>Queue: queue.get() から「茹であがり」を取得
    Merge-->>Main: yield "  [8分] ⏰ パスタが茹であがりました！"
    Merge->>EvLoop: 15. await wait() ➔ 「次の完了まで一時停止（制御を返す）」
    end

    rect rgb(255, 255, 240)
    note over Sauce, Merge: [10分経過] ソース完成＆終了処理
    EvLoop->>Sauce: 16. 7秒経過！(合計10分) 制御を渡して再開
    Sauce-->>Merge: yield "[10分] 3. 完成！"
    Sauce->>EvLoop: 17. 処理終了 (StopAsyncIteration)
    
    EvLoop->>Merge: 18. ストリーム終了に伴い制御を渡して再開
    Merge->>Queue: queue_task.cancel() で後片付け
    Merge-->>Main: 全処理完了
    end
```
```
【ステップ1】 q = asyncio.Queue()
【ステップ2】 async for msg in merge(cook_sauce(q), q):
  [merge] 【ステップ3】 main_task = asyncio.create_task(anext(stream, None))
  [merge] 【ステップ4】 queue_task = asyncio.create_task(queue.get())
  [merge] 【ステップ5】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
    【ステップ6】 yield "[0分] 1. お湯を沸かしてパスタを投下"
  [merge] 【ステップ7】 if completed == main_task:
  [merge] 【ステップ8】 yield "[0分] 1. お湯を沸かしてパスタを投下"
  [merge] 【ステップ9】 main_task = asyncio.create_task(anext(stream, None))
  [merge] 【ステップ10】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
    【ステップ11】 asyncio.create_task(boil_pasta(queue))
    【ステップ12】 await asyncio.sleep(3.0)
      【ステップ13】 await queue.put("  [0分] 🍝 パスタを鍋に投入！")
      【ステップ14】 await asyncio.sleep(8.0)
  [merge] 【ステップ15】 elif completed == queue_task:
  [merge] 【ステップ16】 yield completed.result()  # "[0分] 🍝 パスタを鍋に投入！"
  [merge] 【ステップ17】 queue_task = asyncio.create_task(queue.get())
  [merge] 【ステップ18】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
    【ステップ19】 yield "[3分] 2. ニンニクを弱火で炒める"
  [merge] 【ステップ20】 if completed == main_task:
  [merge] 【ステップ21】 yield "[3分] 2. ニンニクを弱火で炒める"
  [merge] 【ステップ22】 main_task = asyncio.create_task(anext(stream, None))
  [merge] 【ステップ23】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
    【ステップ24】 await asyncio.sleep(7.0)
      【ステップ25】 await queue.put("  [8分] ⏰ パスタが茹であがりました！")
  [merge] 【ステップ26】 elif completed == queue_task:
  [merge] 【ステップ27】 yield completed.result()  # "[8分] ⏰ パスタが茹であがりました！"
  [merge] 【ステップ28】 queue_task = asyncio.create_task(queue.get())
  [merge] 【ステップ29】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
    【ステップ30】 yield "[10分] 3. ソースとパスタを和えて完成！"
  [merge] 【ステップ31】 if completed == main_task:
  [merge] 【ステップ32】 yield "[10分] 3. ソースとパスタを和えて完成！"
  [merge] 【ステップ33】 main_task = asyncio.create_task(anext(stream, None))
  [merge] 【ステップ34】 await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED)
    【ステップ35】 (cook_sauce generator completed / StopAsyncIteration)
  [merge] 【ステップ36】 if event is None:
  [merge] 【ステップ37】 queue_task.cancel()
  [merge] 【ステップ38】 return (merge完了)
```
