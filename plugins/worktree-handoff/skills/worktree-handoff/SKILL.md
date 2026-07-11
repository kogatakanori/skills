---
name: worktree-handoff
description: Hands off a finished requirements/planning conversation to an isolated git worktree session for implementation, by proposing a ready-to-run "claude --worktree <name> --resume <session-id>" command for the user to copy into a separate terminal. Use when requirements or a design/plan have just been finalized and implementation is about to start, or when the user asks to "move this to a worktree", "hand this off for implementation", or "worktreeで実装して".
---

# Worktree Handoff

要件・設計が固まり、これから実装に入るタイミングで、現在の会話を**別ターミナルの独立したgit worktreeセッション**に引き継ぐためのコマンドを提示する。

このスキルは、このセッション自身でファイル編集を始めるためのものではない。このセッションは要件定義・相談用のまま残し、実装は新しいworktreeセッションに委ねる。ブランチ名やセッション名をユーザーが考える必要がないようにするのが目的。

## いつ使うか

- ユーザーと要件・仕様のすり合わせが完了し、次はコードを書く段階に入るとき
- ユーザーが「worktreeで実装して」「別セッションに切り出して」と明示的に依頼したとき
- Plan Modeでplanが承認され、実装フェーズに入るとき

## 手順

### Step 1: worktree名（=ブランチ名）を決める

会話内容から機能・修正内容を要約したkebab-case名を決める（例: `add-oauth-login`, `fix-cache-invalidation`）。ユーザーに確認する必要はない。

### Step 2: 現在のセッションIDを取得する

現在の作業ディレクトリからプロジェクトディレクトリ名を導出し、直近のtranscriptファイル名（拡張子除く）をセッションIDとして取得する:

```bash
PROJECT_ENC=$(pwd | sed 's/[^a-zA-Z0-9]/-/g')
ls -t ~/.claude/projects/"$PROJECT_ENC"/*.jsonl 2>/dev/null | head -1 | xargs -n1 basename | sed 's/\.jsonl$//'
```

同じプロジェクトディレクトリで他のセッションも動いている場合、直近更新されたファイルが必ずしも現在の会話とは限らない。判断に迷う場合はIDをそのまま提示せず、「このセッションで合っているか」一言確認してから進める。

### Step 3: コマンドを提示する

他の説明で挟まず、コードブロック単体でコピペしやすい形で提示する:

```bash
claude --worktree <Step1で決めた名前> --resume <Step2で取得したセッションID>
```

提示に添える一言の例:
「要件はこのセッションにまとめてあります。実装は上のコマンドを別ターミナルで実行して、独立したworktreeで進めてください。」

## 注意点

- `--worktree`の名前と`--resume`のセッションIDは無関係な別々の役割（前者はworktree/ブランチ名、後者は引き継ぐ会話の指定）。一致させる必要はない。
- このセッション自身は要件定義・相談用としてそのまま残る。新しいworktreeセッションでの実装はこのセッションのファイル状態に影響しない。
- 提示したコマンドは新しい別プロセスを起動するものなので、Bashツールで自ら実行してはならない。必ず人が別ターミナルで実行する。
