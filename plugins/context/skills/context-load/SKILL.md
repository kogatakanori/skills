---
name: context-load
description: 個人コンテキストをトピックに応じてオンデマンドでロードするスキル。CLAUDE.mdのCONTEXT_REPOで指定されたリポジトリのindex.mdからタグをもとに関連ファイルを読み込む。
user_invocable: true
---

# context-load

個人コンテキストをトピックに応じてオンデマンドでロードするスキル。
CONTEXT_REPO の index.md に定義されたタグをもとに、関連ファイルをローカルから読み込む。

## 使い方

```
/context-load [topic]
```

- topic を指定すると、index.md の Tags カラムと topic キーワードを照合して関連ファイルを読み込む
- topic を省略すると、会話の内容から自動判断する
- `all` を指定すると全ファイルを読み込む（明示指示のみ）

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

ローカルプラグインパス: `~/.claude/plugins/<repo-name>/`

### 1. プラグインディレクトリを特定する

以下の順で存在確認する：

```bash
ls ~/.claude/plugins/<repo-name>/index.md 2>/dev/null || echo "NOT_FOUND"
```

存在しない場合は以下を案内して終了：
> コンテキストリポジトリがローカルに見つかりません。
> `/context-sync` を実行してセットアップしてください。

### 2. index.md を読み込む

```
Read: ~/.claude/plugins/<repo-name>/index.md
```

### 3. topic に対応する行を抽出する

index.md のテーブルから Tags カラムを確認し、topic キーワードを含む行を選ぶ。

- topic 指定あり → Tags カラムに topic を含む行を選択
- `all` → 全行を選択
- topic 省略 → 直前の会話の話題に最も関連するタグを持つ行を選択

### 4. 対応するファイルを Read する

抽出した行の Path カラムの値を使い：

```
Read: ~/.claude/plugins/<repo-name>/<Path>
```

を各ファイルに対して実行する。

### 5. 完了を報告する

読み込んだファイルの一覧を報告する。

## 注意事項

- 1セッションに1回で通常は十分（同じトピックを再ロードしない）
- ファイルの内容はこのセッションの context window に入る（永続化されない）
- コンテンツが古い場合は `/context-sync` で更新してから再実行
