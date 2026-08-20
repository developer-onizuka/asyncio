```mermaid
sequenceDiagram
    autonumber
    participant Main as main()
    participant Merge as merge()
    participant EvLoop as イベントループ
    participant Sauce as cook_sauce()
    participant Pasta as boil_pasta()
    participant Queue as asyncio.Queue

    rect rgb(240, 240, 255)
    note over Main, Queue: ⏱️ [0分時点・前半] 初期化とソース1行目の処理
    Main->>Queue: 【ステップ1】 q = asyncio.Queue()
    Main->>Merge: 【ステップ2】 async for msg in merge(...)
    Merge->>EvLoop: 【ステップ3】 main_task [第一世代] 作成
    Merge->>EvLoop: 【ステップ4】 queue_task [第一世代] 作成
    Merge->>EvLoop: 【ステップ5】 1回目 await wait() ➔ 制御を渡す
    
    EvLoop->>Sauce: anext [第一世代] を実行
    Sauce-->>Merge: 【ステップ6】 yield "[0分] 1. お湯を沸かして..." (第一世代完了)
    
    EvLoop->>Merge: 第一世代 main_task 完了につき制御復帰
    Merge-->>Main: 【ステップ7-8】 if completed == main_task ➔ yield イベント
    Merge->>EvLoop: 【ステップ9】 main_task [第二世代] 作成（玉込め）
    Merge->>EvLoop: 【ステップ10】 2回目 await wait() ➔ 制御を渡す
    end

    rect rgb(230, 230, 250)
    note over Main, Queue: ⏱️ [0分時点・後半] boil_pasta 起動と各タイマーの計測開始
    EvLoop->>Sauce: anext [第二世代] を実行
    note over Sauce, Pasta: 🍳 3分間でニンニクを切る自分の作業前に、パスタを茹でる依頼
    Sauce->>EvLoop: 【ステップ11】 create_task(boil_pasta)    
    Sauce->>EvLoop: 【ステップ12】 await sleep(3.0) ➔ ⏱️ 3分タイマーセット＆制御を渡す
    note over EvLoop, Sauce: ⏳【イベントループが計測中】Sauceから頼まれた3分タイマーをカウント開始！
    
    EvLoop->>Pasta: boil_pasta を実行（依頼されたパスタの作業を開始）
    Pasta->>Queue: 【ステップ13】 await queue.put("パスタ投入") (queue_task 第一世代完了)
    Pasta->>EvLoop: 【ステップ14】 await sleep(8.0) ➔ ⏱️ 8分タイマーセット＆制御を渡す
    note over EvLoop, Pasta: ⏳【イベントループが計測中】Pastaから頼まれた8分タイマーをカウント開始！
    
    note over EvLoop, Pasta: ⚡【並行調理】事前に依頼を出したため、イベントループ上で「Sauceの3分」と「Pastaの8分」が同時に数えられる！
    
    EvLoop->>Merge: 第一世代 queue_task 完了につき制御復帰
    Merge-->>Main: 【ステップ15-16】 elif completed == queue_task ➔ yield パスタ投入
    Merge->>EvLoop: 【ステップ17】 queue_task [第二世代] 作成（玉込め）
    Merge->>EvLoop: 【ステップ18】 3回目 await wait() ➔ 制御を渡す
    end

    rect rgb(255, 235, 235)
    note over EvLoop, Sauce: ⏳【イベントループが計測完了】ステップ12のSauceの3分タイマーが満了！
    end

    rect rgb(255, 240, 240)
    note over Main, Queue: ⏳【3分経過時点】 ソースのニンニク炒め
    EvLoop->>Sauce: 3秒経過！anext [第二世代] を再開
    Sauce-->>Merge: 【ステップ19】 yield "[3分] 2. ニンニクを..." (第二世代完了)
    
    EvLoop->>Merge: 第二世代 main_task 完了につき制御復帰
    Merge-->>Main: 【ステップ20-21】 if completed == main_task ➔ yield イベント
    Merge->>EvLoop: 【ステップ22】 main_task [第三世代] 作成（玉込め）
    Merge->>EvLoop: 【ステップ23】 4回目 await wait() ➔ 制御を渡す
    
    EvLoop->>Sauce: anext [第三世代] を実行
    Sauce->>EvLoop: 【ステップ24】 await sleep(7.0) ➔ ⏱️ 7分タイマーセット＆制御を渡す
    note over EvLoop, Sauce: ⏳【イベントループが計測中】Sauceから頼まれた次の7分タイマーをカウント開始！
    end

    rect rgb(235, 255, 235)
    note over EvLoop, Pasta: ⏳【イベントループが計測完了】ステップ14のPastaの8分タイマーが満了！
    end

    rect rgb(240, 255, 240)
    note over Main, Queue: ⏳【8分経過時点】 パスタ茹であがり
    EvLoop->>Pasta: 8秒経過！boil_pasta を再開
    Pasta->>Queue: 【ステップ25】 await queue.put("茹であがり") (queue_task 第二世代完了)
    
    EvLoop->>Merge: 第二世代 queue_task 完了につき制御復帰
    Merge-->>Main: 【ステップ26-27】 elif completed == queue_task ➔ yield 茹であがり
    Merge->>EvLoop: 【ステップ28】 queue_task [第三世代] 作成（玉込め）
    Merge->>EvLoop: 【ステップ29】 5回目 await wait() ➔ 制御を渡す
    end

    rect rgb(255, 255, 225)
    note over EvLoop, Sauce: ⏳【イベントループが計測完了】ステップ24のSauceの7分タイマー（合計10分）が満了！
    end

    rect rgb(255, 255, 240)
    note over Main, Queue: ⏳【10分経過時点】 完成と終了処理
    EvLoop->>Sauce: 7秒経過！anext [第三世代] を再開
    Sauce-->>Merge: 【ステップ30】 yield "[10分] 3. 完成！" (第三世代完了)
    
    EvLoop->>Merge: 第三世代 main_task 完了につき制御復帰
    Merge-->>Main: 【ステップ31-32】 if completed == main_task ➔ yield イベント
    Merge->>EvLoop: 【ステップ33】 main_task [第四世代] 作成（玉込め）
    Merge->>EvLoop: 【ステップ34】 6回目 await wait() ➔ 制御を渡す
    
    EvLoop->>Sauce: anext [第四世代] を実行
    Sauce-->>Merge: 【ステップ35】 StopAsyncIteration (None) 返却 (第四世代完了)
    
    EvLoop->>Merge: 第四世代 main_task (None) 完了につき制御復帰
    Merge-->>Main: 【ステップ36】 if event is None: 条件成立
    Merge->>EvLoop: 【ステップ37】 queue_task [第三世代].cancel()
    Merge-->>Main: 【ステップ38】 return (merge処理終了)
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
