## 目的
- ユーザー入力とWorker結果を統一的なイベントとして扱う
- LLM Agent の逐次処理を保証する
- Worker（deep_research等）を安全に起動・管理する
- CLI / Web / その他UIから独立したruntime層を提供する

## 前提
- main_agent は単一プロセス・常駐
- LLM Agent は逐次処理のみ（並列処理しない）
- Worker は別プロセスとして起動される
- ユーザーは1人
- session切り替えは不要（将来拡張は可能）

## agent_runtime（メインプロセス）
- ユーザー入力を受ける（CLI/GUIはここに繋ぐ）
- LLM(main_agent) を 逐次実行（single queue）
- workerへ「タスク実行依頼」を送る（ZMQ）
- workerから「完了/失敗/進捗」を受け取り、InputEventとしてqueueへ積む

## worker_runtime（別リポジトリ想定、常駐プロセス）
- ZMQで controller から task を受け取る
- task.kind に応じて「別リポジトリの agent」を起動（例：app.invoke()）
- 結果を controller へ返信（ZMQ）
