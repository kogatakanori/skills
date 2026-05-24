---
name: arc-specifying
description: Generates spec comment and docs from a GitHub Issue. Checks out a feature branch, runs parallel investigation agents (codebase and architecture analysis), posts spec as an Issue comment, and creates docs/ files. Use at the start of a new feature development cycle. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Specifying

GitHub IssueからSpec（なぜ・意思決定）をIssueコメントとして投稿し、Docs（何を・最新仕様）を `docs/` に生成する。

## Workflow

### Step 0: Hooks設定チェックと自動セットアップ

#### 0-a: Readパーミッション設定チェック

arcプラグインはプロジェクト外のパスにあるため、プロジェクト設定（`.claude/settings.json`）では許可できない。グローバル設定（`~/.claude/settings.json`）の `permissions.allow` 配列にarcプラグインのルートパスを含むエントリ（`~/...arc.../**` のようなパターン）が存在しない場合、以下を自動セットアップする：

1. `Read` ツールでこのSKILL.mdを読み込んだ際の絶対パス（例: `/home/user/.../plugins/arc/skills/arc-specifying/SKILL.md`）から2階層上（`../..`）でarcのルートディレクトリを計算する
2. 計算した絶対パスを `~/` 形式に変換する（`$HOME` に一致するプレフィックス部分を `~/` に置換）
3. `~/.claude/settings.json`（存在しない場合は新規作成）の `permissions.allow` に `Read(~/path/to/arc/**)` を追加する（既存設定とマージ）

**`~/` 形式を使う理由**: グローバル設定では `~/` プレフィックス形式が推奨。絶対パス（`/home/user/...` のような形式）は移植性が低い。

**設定反映のタイミング**: グローバル設定の変更はClaude Codeの再起動後に有効になります。設定を書き換えた場合はユーザーに「設定を反映するにはClaude Codeを再起動してください」と案内し、再起動後に改めて `/arc-specifying` を実行するよう促す。

arcルートへのReadパーミッションが既に設定済みの場合はこのステップをスキップする。

#### 0-b: Hooks設定チェック

`.claude/settings.json` に `WorktreeCreate` / `WorktreeRemove` hookが未設定の場合、以下を自動セットアップする：

1. `.claude/hooks/` ディレクトリを作成
2. `../../templates/hooks/worktree-create.sh` を `.claude/hooks/worktree-create.sh` にコピー
3. `../../templates/hooks/worktree-remove.sh` を `.claude/hooks/worktree-remove.sh` にコピー
4. 両ファイルに実行権限を付与：`chmod +x .claude/hooks/worktree-*.sh`
5. `.claude/settings.json` に hooks エントリを追加（既存設定とマージ）：
   ```json
   {
     "hooks": {
       "WorktreeCreate": [{"type": "command", "command": "bash .claude/hooks/worktree-create.sh"}],
       "WorktreeRemove": [{"type": "command", "command": "bash .claude/hooks/worktree-remove.sh"}]
     }
   }
   ```

hookの内容：
- **worktree-create.sh**: worktree作成 → `.worktreeinclude` のファイルコピー → 依存関係インストール（コメントアウト済み）
- **worktree-remove.sh**: worktreeとブランチを削除

既に両hookが設定済みの場合はこのステップをスキップする。

### Step 1: Issue取得とworktree作成

1. Issue情報を取得する：
   ```bash
   gh issue view <N> --json title,body,labels,assignees,url
   ```

2. `EnterWorktree` ツールで `name=issue-<N>` を指定してworktreeを作成する
   - `.worktreeinclude` に記載されたファイルが自動コピーされる
   - `WorktreeCreate` hook が自動実行される
   - 現在のセッションがworktree内に切り替わる

### Step 2: 並列コードベース調査

`../../agents/codebase-analyst.md` と `../../agents/architecture-analyst.md` を Read し、`[issueのタイトルと本文]` を実際のIssue内容で置換して、2体のExploreエージェントを**同時に**起動する：

**Agent A（codebase-analyst）**: 類似機能・競合コード・踏襲すべきパターンを調査

**Agent B（architecture-analyst）**: アーキテクチャ制約・既存docs・テスト基盤を調査

調査結果を統合し、解消不可能な重大な曖昧点のみ `AskUserQuestion` で確認する（最大2問まで）。

### Step 3: Specコメント投稿

`../../templates/spec.md.template` を参照してSpecの内容を作成し、IssueにGitHubコメントとして投稿する：

```bash
gh issue comment <N> --body "$(cat <<'EOF'
<!-- arc:spec -->
...specの内容...
EOF
)"
```

フォーマットは `references/spec-format.md` に従う。重要な点：
- **Context（Why）**: Issueの背景・解決する課題を明確に記述
- **ADR**: なぜこのアーキテクチャを選択したか、代替案と却下理由を必ず含める
- **Goal/Non-Goals**: スコープを明確に定義する

### Step 4: Docsファイル生成

`../../templates/docs.md.template` を参照して `docs/<feature-name>.md` を生成する。

フォーマットは `references/docs-format.md` に従う。機能の概要・使い方・仕様を記述する（「何を・どう使うか」にフォーカス）。

### Step 5: コミットと案内

```bash
git add docs/
git commit -m "spec: add docs for issue #NNN - <title>"
```

**"IssueのSpecコメントを確認し承認したら、`/arc-investigating` を実行してください"** と案内する。IssueのURLも合わせて表示する。

## Notes

- specの内容はIssueコメントに保存される（`specs/` ディレクトリは使用しない）
- `docs/` ディレクトリが存在しない場合は作成する
- 既存の `docs/` ファイルがある場合は上書き更新する
