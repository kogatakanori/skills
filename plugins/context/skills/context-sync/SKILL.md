---
name: context-sync
description: ローカルのコンテキストリポジトリをGitHubの最新版に同期するスキル。CLAUDE.mdのCONTEXT_REPOで指定されたリポジトリをクローンまたはpullする。「コンテキストを更新して」「context-syncを実行して」と言われた時に使用。
user_invocable: true
---

# context-sync

ローカルのコンテキストリポジトリを GitHub の最新版に同期するスキル。

## 使い方

```
/context-sync
```

## 実行手順

### 0. CONTEXT_REPO を特定する

現在のプロジェクトの CLAUDE.md に記載された `CONTEXT_REPO:` の値を読み取る。
すでにコンテキストにロード済みの場合はそのまま使用する。見つからない場合は
プロジェクトの CLAUDE.md を Read して確認する。

例: `CONTEXT_REPO: kogatakanori/context`

見つからない場合は以下を案内して終了:
> CONTEXT_REPO が設定されていません。
> プロジェクトの CLAUDE.md に以下を追加してください:
> ```
> CONTEXT_REPO: <your-github-username>/<repo-name>
> ```

`CONTEXT_REPO` からリポジトリ名（`/` 以降の部分）を取得する。
例: `kogatakanori/context` → `context`

ローカルパス: `~/.claude/plugins/<repo-name>/`

### 1. プラグインディレクトリの確認

```bash
ls ~/.claude/plugins/<repo-name>/ 2>/dev/null || echo "NOT_FOUND"
```

**存在する場合** → ステップ2へ（更新）

**存在しない場合** → ステップ3へ（初回セットアップ）

### 2. 既存プラグインを更新（git pull）

```bash
cd ~/.claude/plugins/<repo-name> && git pull
```

成功したら報告：
> コンテキストを最新版に更新しました。
> （更新されたファイル一覧があれば表示）

### 3. 初回セットアップ（clone）

```bash
mkdir -p ~/.claude/plugins
gh repo clone $CONTEXT_REPO ~/.claude/plugins/<repo-name>
```

成功したら報告：
> コンテキストリポジトリをセットアップしました。
> `/context-load` が使えるようになりました。

### 4. エラー時の案内

- `gh` コマンドが見つからない場合 → `GitHub CLI (gh) が必要です。brew install gh でインストールしてください。`
- 認証エラーの場合 → `gh auth login を実行して GitHub にログインしてください。`
- その他のエラー → エラーメッセージをそのまま表示

## 実行タイミングの目安

- 初回セットアップ時（1回だけ）
- コンテキストの内容を更新した後
- `/context-load` で「NOT_FOUND」と言われたとき
